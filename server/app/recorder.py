import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


class FrameRecorder:
    def __init__(self, directory: Path, fps: float = 1.0):
        self.directory = directory
        self.fps = fps
        self._lock = threading.RLock()
        self._path: Path | None = None
        self._writer: cv2.VideoWriter | None = None
        self._last_frame_at = 0.0

    def start(self) -> dict[str, str | bool]:
        with self._lock:
            if self._path:
                return self.info()
            self.directory.mkdir(parents=True, exist_ok=True)
            self._path = self._next_path()
            self._path.touch(exist_ok=False)
            self._last_frame_at = 0.0
            return self.info()

    def stop(self) -> dict[str, str | bool]:
        with self._lock:
            self._release()
            self._path = None
            self._last_frame_at = 0.0
            return self.info()

    def write(self, frame: np.ndarray) -> None:
        with self._lock:
            if not self._path:
                return
            now = time.monotonic()
            if self._last_frame_at and now - self._last_frame_at < 1.0 / self.fps:
                return
            if not self._writer:
                height, width = frame.shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                self._writer = cv2.VideoWriter(str(self._path), fourcc, self.fps, (width, height))
            self._writer.write(frame)
            self._last_frame_at = now

    def info(self) -> dict[str, str | bool]:
        return {
            "recording": bool(self._path),
            "file": str(self._path) if self._path else "",
        }

    def _release(self) -> None:
        if self._writer:
            self._writer.release()
            self._writer = None

    def _next_path(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.directory / f"recording_{stamp}.avi"
        counter = 2
        while path.exists():
            path = self.directory / f"recording_{stamp}_{counter}.avi"
            counter += 1
        return path
