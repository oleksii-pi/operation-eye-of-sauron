from dataclasses import dataclass
import math
import threading
import time

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
        self._updated_at = 0.0
        self._frame_size = (0, 0)
        self._enabled = False
        self._pause_frame: np.ndarray | None = None
        self._scene_motion = 0.0
        self._settled_at = 0.0
        self._lock = threading.Lock()

    def info(self) -> dict[str, object]:
        with self._lock:
            return {
                "mode": "motion",
                "status": "ready" if self._enabled else "paused",
                "enabled": self._enabled,
                "min_size_cm": self._min_size_cm,
                "distance_cm": self.distance_cm,
                "horizontal_fov_degrees": self.horizontal_fov_degrees,
                "boxes": len(self._boxes),
                "last_motion_age_seconds": self._motion_age(),
                "scene_motion": self._scene_motion,
                "scene_settled": self.scene_settled(),
            }

    def set_min_size_cm(self, value: float) -> dict[str, object]:
        with self._lock:
            self._min_size_cm = min(100.0, max(1.0, float(value)))
        return self.info()

    def set_enabled(self, enabled: bool) -> dict[str, object]:
        with self._lock:
            self._enabled = enabled
            self._boxes = []
            self._updated_at = 0.0
            self._pause_frame = None
            self._settled_at = 0.0
            self._scene_motion = 0.0 if enabled else 1.0
            if enabled:
                self._background = None
        return self.info()

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        with self._lock:
            enabled = self._enabled
        if not enabled:
            self._track_scene(gray, frame.shape[1], frame.shape[0])
            return frame
        if self._background is None:
            self._background = gray.astype("float")
            return frame

        cv2.accumulateWeighted(gray, self._background, 0.05)
        background = cv2.convertScaleAbs(self._background)
        delta = cv2.absdiff(gray, background)
        threshold = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        threshold = cv2.dilate(threshold, None, iterations=2)
        boxes = self._find_boxes(threshold, frame.shape[1])
        with self._lock:
            draw_boxes = self._enabled
            if draw_boxes:
                self._boxes = boxes
                self._frame_size = (frame.shape[1], frame.shape[0])
                self._updated_at = time.monotonic()
        if not draw_boxes:
            return frame
        for box in boxes:
            cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), (0, 255, 0), 2)
        return frame

    def target(self) -> dict[str, float | int] | None:
        with self._lock:
            enabled = self._enabled
            boxes = list(self._boxes)
            updated_at = self._updated_at
            frame_width, frame_height = self._frame_size
        if not enabled or not boxes:
            return None
        small_boxes = self._small_boxes(boxes, frame_width, frame_height)
        target_boxes = self._target_boxes(small_boxes, frame_width, frame_height)
        if not target_boxes:
            return None
        x1, y1 = min(item.x1 for item in target_boxes), min(item.y1 for item in target_boxes)
        x2, y2 = max(item.x2 for item in target_boxes), max(item.y2 for item in target_boxes)
        return {
            "x": (x1 + x2) / 2,
            "y": (y1 + y2) / 2,
            "width": x2 - x1,
            "height": y2 - y1,
            "motion_boxes": len(small_boxes),
            "age_seconds": max(0.0, time.monotonic() - updated_at),
        }

    def scene_state(self) -> dict[str, float | bool]:
        with self._lock:
            return {"motion": self._scene_motion, "settled": self.scene_settled(), "settled_seconds": self._settled_seconds()}

    def scene_settled(self, stable_seconds: float = 0.35) -> bool:
        return bool(self._settled_at and self._settled_seconds() >= stable_seconds)

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

    def _small_boxes(self, boxes: list[MotionBox], frame_width: int, frame_height: int) -> list[MotionBox]:
        if not frame_width or not frame_height:
            return boxes
        max_area = frame_width * frame_height * 0.15
        max_width = frame_width * 0.5
        max_height = frame_height * 0.5
        return [
            box for box in boxes
            if (box.x2 - box.x1) * (box.y2 - box.y1) <= max_area
            and box.x2 - box.x1 <= max_width
            and box.y2 - box.y1 <= max_height
        ]

    def _target_boxes(self, boxes: list[MotionBox], frame_width: int, frame_height: int) -> list[MotionBox]:
        if len(boxes) == 1:
            return boxes
        if len(boxes) != 2 or not frame_width or not frame_height:
            return []
        first, second = boxes
        dx = abs(first.x1 + first.x2 - second.x1 - second.x2) / 2
        dy = abs(first.y1 + first.y2 - second.y1 - second.y2) / 2
        return boxes if dx <= frame_width * 0.18 and dy <= frame_height * 0.18 else []

    def _track_scene(self, gray: np.ndarray, width: int, height: int) -> None:
        now = time.monotonic()
        with self._lock:
            previous = self._pause_frame
        motion = 1.0
        if previous is not None:
            delta = cv2.absdiff(gray, previous)
            threshold = cv2.threshold(delta, 18, 255, cv2.THRESH_BINARY)[1]
            motion = cv2.countNonZero(threshold) / float(threshold.size)
        with self._lock:
            self._background = gray.astype("float")
            self._pause_frame = gray.copy()
            self._boxes = []
            self._frame_size = (width, height)
            self._updated_at = 0.0
            self._scene_motion = motion
            self._settled_at = self._settled_at or now if motion < 0.012 else 0.0

    def _motion_age(self) -> float | None:
        return max(0.0, time.monotonic() - self._updated_at) if self._updated_at else None

    def _settled_seconds(self) -> float:
        return max(0.0, time.monotonic() - self._settled_at) if self._settled_at else 0.0
