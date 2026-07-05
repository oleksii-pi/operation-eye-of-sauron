from dataclasses import dataclass
from pathlib import Path
import time

import cv2
import numpy as np


@dataclass(frozen=True)
class HandBox:
    x1: int
    y1: int
    x2: int
    y2: int


class HandDetector:
    def __init__(self, confidence: float, every_n_frames: int, model_path: str):
        self.confidence = confidence
        self.every_n_frames = every_n_frames
        self.model_path = model_path
        self._frame_count = 0
        self._boxes: list[HandBox] = []
        self._landmarker = None
        self._status = self._init_model()

    def _init_model(self) -> str:
        if not Path(self.model_path).exists():
            return f"missing_model: {self.model_path}"
        try:
            import mediapipe as mp

            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=self.model_path),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=self.confidence,
                min_hand_presence_confidence=self.confidence,
                min_tracking_confidence=0.5,
            )
            self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
            return "ready"
        except Exception as exc:
            self._landmarker = None
            return f"unavailable: {exc}"

    def info(self) -> dict[str, object]:
        return {"status": self._status, "model": self.model_path, "boxes": len(self._boxes)}

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        if self._landmarker:
            self._frame_count += 1
            if self._frame_count % self.every_n_frames == 1:
                self._boxes = self._detect(frame)
        for box in self._boxes:
            cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), (0, 255, 0), 2)
        return frame

    def _detect(self, frame: np.ndarray) -> list[HandBox]:
        height, width = frame.shape[:2]
        import mediapipe as mp

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(time.monotonic() * 1000)
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.hand_landmarks:
            return []
        boxes: list[HandBox] = []
        for landmarks in result.hand_landmarks:
            xs = [point.x for point in landmarks]
            ys = [point.y for point in landmarks]
            x1 = max(0, int(min(xs) * width) - 12)
            y1 = max(0, int(min(ys) * height) - 12)
            x2 = min(width - 1, int(max(xs) * width) + 12)
            y2 = min(height - 1, int(max(ys) * height) + 12)
            boxes.append(HandBox(x1, y1, x2, y2))
        return boxes
