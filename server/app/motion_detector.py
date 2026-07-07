from dataclasses import dataclass
import math
import threading

import cv2
import numpy as np


@dataclass(frozen=True)
class MotionBox:
    x1: int
    y1: int
    x2: int
    y2: int


class MotionDetector:
    def __init__(
        self,
        min_size_cm: float = 5.0,
        distance_cm: float = 200.0,
        horizontal_fov_degrees: float = 62.0,
    ):
        self.distance_cm = max(1.0, distance_cm)
        self.horizontal_fov_degrees = min(170.0, max(10.0, horizontal_fov_degrees))
        self._min_size_cm = max(1.0, min_size_cm)
        self._background: np.ndarray | None = None
        self._boxes: list[MotionBox] = []
        self._lock = threading.Lock()

    def info(self) -> dict[str, object]:
        with self._lock:
            return {
                "mode": "motion",
                "status": "ready",
                "min_size_cm": self._min_size_cm,
                "distance_cm": self.distance_cm,
                "horizontal_fov_degrees": self.horizontal_fov_degrees,
                "boxes": len(self._boxes),
            }

    def set_min_size_cm(self, value: float) -> dict[str, object]:
        with self._lock:
            self._min_size_cm = min(100.0, max(1.0, float(value)))
        return self.info()

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        if self._background is None:
            self._background = gray.astype("float")
            return frame

        cv2.accumulateWeighted(gray, self._background, 0.05)
        background = cv2.convertScaleAbs(self._background)
        delta = cv2.absdiff(gray, background)
        threshold = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None, iterations=2)
        self._boxes = self._find_boxes(threshold, frame.shape[1])
        for box in self._boxes:
            cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), (0, 255, 0), 2)
        return frame

    def _find_boxes(self, threshold: np.ndarray, frame_width: int) -> list[MotionBox]:
        min_pixels = self._min_pixels(frame_width)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes: list[MotionBox] = []
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            if max(width, height) < min_pixels:
                continue
            if cv2.contourArea(contour) < min_pixels * min_pixels * 0.20:
                continue
            boxes.append(MotionBox(x, y, x + width, y + height))
        return boxes

    def _min_pixels(self, frame_width: int) -> int:
        with self._lock:
            min_size_cm = self._min_size_cm
        fov = math.radians(self.horizontal_fov_degrees)
        visible_width_cm = 2.0 * self.distance_cm * math.tan(fov / 2.0)
        return max(2, round(frame_width * min_size_cm / visible_width_cm))
