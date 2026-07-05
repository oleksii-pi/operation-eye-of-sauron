import os
import threading
import time
from socket import create_connection
from urllib.parse import urlparse

os.environ["OPENCV_FFMPEG_DEBUG"] = "0"
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"

import cv2
import numpy as np

LOW_LATENCY_FFMPEG_OPTIONS = (
    ("rtsp_transport", "tcp"),
    ("fflags", "nobuffer"),
    ("flags", "low_delay"),
    ("max_delay", "0"),
    ("reorder_queue_size", "0"),
    ("analyzeduration", "0"),
    ("probesize", "32"),
    ("loglevel", "quiet"),
)


def encode_jpeg(frame: np.ndarray, quality: int = 90) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Failed to encode JPEG frame")
    return buffer.tobytes()


def placeholder_frame(message: str, size: tuple[int, int] = (1280, 720), quality: int = 90) -> bytes:
    width, height = size
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:] = (24, 24, 24)
    cv2.putText(frame, "Camera PoC", (24, 56), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
    cv2.putText(frame, message, (24, 112), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 220, 255), 2)
    cv2.rectangle(frame, (18, 18), (width - 18, height - 18), (90, 90, 90), 2)
    return encode_jpeg(frame, quality)


def configure_ffmpeg_capture() -> None:
    parts = [part for part in os.getenv("OPENCV_FFMPEG_CAPTURE_OPTIONS", "").split("|") if part]
    keys = {part.split(";", 1)[0] for part in parts if ";" in part}
    parts.extend(f"{key};{value}" for key, value in LOW_LATENCY_FFMPEG_OPTIONS if key not in keys)
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "|".join(parts)


class CameraStream:
    def __init__(
        self,
        rtsp_url: str,
        width: int = 1280,
        height: int = 720,
        jpeg_quality: int = 90,
        fps: float = 15.0,
        retry_seconds: float = 3.0,
    ):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.jpeg_quality = jpeg_quality
        self.frame_delay = 1.0 / fps
        self.retry_seconds = retry_seconds
        self._lock = threading.Lock()
        self._frame = self._placeholder("Waiting for RTSP URL")
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
        try:
            while self._running:
                yield boundary + self.snapshot() + b"\r\n"
                time.sleep(self.frame_delay)
        except GeneratorExit:
            return

    def _placeholder(self, message: str) -> bytes:
        return placeholder_frame(message, (self.width, self.height), self.jpeg_quality)

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
                self._set_frame(self._placeholder("Set RTSP_URL in .env"), "missing_url")
                time.sleep(self.retry_seconds)
                continue
            reachable, reason = self._is_reachable()
            if not reachable:
                self._set_frame(self._placeholder("Cannot reach camera host"), f"camera_unreachable: {reason}")
                time.sleep(self.retry_seconds)
                continue
            configure_ffmpeg_capture()
            capture = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            if not capture.isOpened():
                self._set_frame(self._placeholder("Cannot open RTSP stream"), "reconnecting")
                capture.release()
                time.sleep(self.retry_seconds)
                continue
            self._set_frame(self._placeholder("RTSP connected"), "connected")
            while self._running:
                ok, frame = capture.read()
                if not ok:
                    self._set_frame(self._placeholder("Stream lost, reconnecting"), "reconnecting")
                    break
                frame = self._resize(frame)
                self._set_frame(encode_jpeg(frame, self.jpeg_quality), "live")
            capture.release()
            time.sleep(self.retry_seconds)

    def _resize(self, frame: np.ndarray) -> np.ndarray:
        current_height, current_width = frame.shape[:2]
        target = (self.width, self.height)
        if (current_width, current_height) == target:
            return frame
        interpolation = cv2.INTER_AREA
        if self.width > current_width or self.height > current_height:
            interpolation = cv2.INTER_LINEAR
        return cv2.resize(frame, target, interpolation=interpolation)
