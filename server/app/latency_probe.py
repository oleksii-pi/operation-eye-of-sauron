import threading
import time

import cv2
import numpy as np

from app.camera import CameraStream
from app.camera_direction import CameraDirection, clamp

MOVE_STEP = 3
PROBE_SECONDS = 3


class LatencyProbe:
    def __init__(self, camera: CameraStream, direction: CameraDirection):
        self.camera = camera
        self.direction = direction
        self._lock = threading.Lock()
        self._status = "waiting"
        self._seconds = 0.0
        self._error = ""
        self._restore_to: tuple[int, int] | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> dict[str, str | float]:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return self._info()
            self._status = "calculating"
            self._seconds = 0.0
            self._error = ""
            self._restore_to = None
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return self._info()

    def info(self) -> dict[str, str | float]:
        with self._lock:
            return self._info()

    def _info(self) -> dict[str, str | float]:
        return {
            "status": self._status,
            "seconds": self._seconds,
            "error": self._error,
        }

    def _set(self, status: str, seconds: float = 0.0, error: str = "") -> None:
        with self._lock:
            self._status = status
            self._seconds = seconds
            self._error = error

    def _run(self) -> None:
        self._set("calculating")
        deadline = time.monotonic() + PROBE_SECONDS
        try:
            baseline = self._wait_frame(deadline)
            original = self.direction.info()
            horizontal = int(original["horizontal"])
            vertical = int(original["vertical"])
            self._restore_to = (horizontal, vertical)
            step = MOVE_STEP if horizontal <= 80 else -MOVE_STEP
            started_at = time.monotonic()
            move = self.direction.move(clamp(horizontal + step), vertical)
            if move.get("last_error"):
                self._set("failed", error=str(move["last_error"]))
                return
            while time.monotonic() < deadline:
                frame = self._frame()
                if frame is not None and self._changed(baseline, frame):
                    seconds = round(time.monotonic() - started_at, 1)
                    self._set("done", seconds=max(0.1, seconds))
                    return
                time.sleep(0.05)
            self._set("failed", error="no visible camera movement detected in 3s")
        except Exception as exc:
            self._set("failed", error=str(exc))
        finally:
            self._restore()

    def _restore(self) -> None:
        if not self._restore_to:
            return
        horizontal, vertical = self._restore_to
        try:
            self.direction.move(horizontal, vertical)
        except Exception:
            return

    def _wait_frame(self, deadline: float) -> np.ndarray:
        previous = None
        stable_at = 0.0
        while time.monotonic() < deadline:
            frame = self._frame()
            if frame is not None and self.camera.info()["status"] == "live":
                if previous is not None and self._similar(previous, frame):
                    stable_at = stable_at or time.monotonic()
                    if time.monotonic() - stable_at >= 0.35:
                        return frame
                else:
                    stable_at = 0.0
                previous = frame
            time.sleep(0.05)
        raise RuntimeError("no live RTSP frame")

    def _frame(self) -> np.ndarray | None:
        image = np.frombuffer(self.camera.snapshot(), dtype=np.uint8)
        frame = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)
        if frame is None:
            return None
        return cv2.resize(frame, (96, 54), interpolation=cv2.INTER_AREA)

    def _changed(self, before: np.ndarray, after: np.ndarray) -> bool:
        diff = cv2.absdiff(before, after)
        mean = float(diff.mean())
        changed = float((diff > 24).mean())
        return mean > 10 or changed > 0.12

    def _similar(self, before: np.ndarray, after: np.ndarray) -> bool:
        return float(cv2.absdiff(before, after).mean()) < 4
