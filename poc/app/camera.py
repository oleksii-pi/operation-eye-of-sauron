import threading
import time
from socket import create_connection
from urllib.parse import urlparse

import cv2
import numpy as np


def encode_jpeg(frame: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        raise RuntimeError("Failed to encode JPEG frame")
    return buffer.tobytes()


def placeholder_frame(message: str, size: tuple[int, int] = (640, 360)) -> bytes:
    width, height = size
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (24, 24, 24)
    cv2.putText(frame, "Camera PoC", (24, 56), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
    cv2.putText(frame, message, (24, 112), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 220, 255), 2)
    cv2.rectangle(frame, (18, 18), (width - 18, height - 18), (90, 90, 90), 2)
    return encode_jpeg(frame)


class CameraStream:
    def __init__(self, rtsp_url: str, width: int = 640, height: int = 360, retry_seconds: float = 3.0):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.retry_seconds = retry_seconds
        self._lock = threading.Lock()
        self._frame = placeholder_frame("Waiting for RTSP URL")
        self._status = "starting"
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def info(self) -> dict[str, str]:
        with self._lock:
            return {"status": self._status, "rtsp_url_set": str(bool(self.rtsp_url))}

    def snapshot(self) -> bytes:
        with self._lock:
            return self._frame

    def stream(self):
        boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            yield boundary + self.snapshot() + b"\r\n"
            time.sleep(0.1)

    def _set_frame(self, frame: bytes, status: str) -> None:
        with self._lock:
            self._frame = frame
            self._status = status

    def _is_reachable(self) -> tuple[bool, str]:
        parsed = urlparse(self.rtsp_url)
        host = parsed.hostname
        port = parsed.port or 554
        if not host:
            return False, "invalid RTSP URL"
        try:
            with create_connection((host, port), timeout=2):
                return True, ""
        except OSError as exc:
            return False, str(exc)

    def _loop(self) -> None:
        while self._running:
            if not self.rtsp_url:
                self._set_frame(placeholder_frame("Set RTSP_URL in .env"), "missing_url")
                time.sleep(self.retry_seconds)
                continue
            reachable, reason = self._is_reachable()
            if not reachable:
                self._set_frame(placeholder_frame("Cannot reach camera host"), f"camera_unreachable: {reason}")
                time.sleep(self.retry_seconds)
                continue
            capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            if not capture.isOpened():
                self._set_frame(placeholder_frame("Cannot open RTSP stream"), "reconnecting")
                capture.release()
                time.sleep(self.retry_seconds)
                continue
            self._set_frame(placeholder_frame("RTSP connected"), "connected")
            while self._running:
                ok, frame = capture.read()
                if not ok:
                    self._set_frame(placeholder_frame("Stream lost, reconnecting"), "reconnecting")
                    break
                frame = cv2.resize(frame, (self.width, self.height))
                self._set_frame(encode_jpeg(frame), "live")
            capture.release()
            time.sleep(self.retry_seconds)
