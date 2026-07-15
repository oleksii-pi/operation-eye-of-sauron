import threading
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


class FrameRecorder:
    def __init__(self, directory: Path, fps: float = 4.0, playback_fps: float = 30.0):
        self.directory = directory
        self.fps = fps
        self.playback_fps = playback_fps
        self._lock = threading.RLock()
        self._path: Path | None = None
        self._writer: cv2.VideoWriter | None = None
        self._last_frame_at = 0.0

    def start(self, fps: float | None = None) -> dict[str, str | bool | float]:
        with self._lock:
            if self._path:
                return self.info()
            if fps is not None:
                self.fps = fps
            self.directory.mkdir(parents=True, exist_ok=True)
            self._path = self._next_path()
            self._path.touch(exist_ok=False)
            self._last_frame_at = 0.0
            return self.info()

    def stop(self) -> dict[str, str | bool | float]:
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
                self._writer = self._open_writer(width, height)
                if not self._writer:
                    return
            self._writer.write(frame)
            self._last_frame_at = now

    def info(self) -> dict[str, str | bool | float]:
        return {
            "recording": bool(self._path),
            "file": str(self._path) if self._path else "",
            "fps": self.fps,
            "playback_fps": self.playback_fps,
            "speed": self.playback_fps / self.fps if self.fps else 1.0,
        }

    def _release(self) -> None:
        if self._writer:
            self._writer.release()
            self._writer = None

    def _next_path(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.directory / f"recording_{stamp}.mp4"
        counter = 2
        while path.exists():
            path = self.directory / f"recording_{stamp}_{counter}.mp4"
            counter += 1
        return path

    def _open_writer(self, width: int, height: int) -> cv2.VideoWriter | None:
        if not self._path:
            return None
        for codec in ("avc1", "H264", "mp4v"):
            fourcc = cv2.VideoWriter_fourcc(*codec)
            writer = cv2.VideoWriter(str(self._path), fourcc, self.playback_fps, (width, height))
            if writer.isOpened():
                return writer
            writer.release()
        return None
