from dataclasses import dataclass

import cv2
import numpy as np

from app.hand_detector import HandDetector


ALIASES = {
    "child": "person",
    "human hand": "hand",
    "human hand with 5 fingers": "hand",
    "human": "person",
    "kid": "person",
}

COCO_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
    "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
    "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
    "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush",
}


@dataclass(frozen=True)
class DetectionBox:
    x1: int
    y1: int
    x2: int
    y2: int


class ObjectDetector:
    def __init__(
        self,
        target: str,
        confidence: float,
        every_n_frames: int,
        model_name: str,
        hand_model_path: str,
    ):
        self.requested_target = target
        self.target = ALIASES.get(target, target)
        self.confidence = confidence
        self.every_n_frames = every_n_frames
        self.model_name = model_name
        self.hand_model_path = hand_model_path
        self._frame_count = 0
        self._boxes: list[DetectionBox] = []
        self._model = None
        self._class_id: int | None = None
        self._hand_detector: HandDetector | None = None
        self._status = self._init_model()

    def _init_model(self) -> str:
        if not self.requested_target:
            return "disabled"
        if self.target == "hand":
            self._hand_detector = HandDetector(self.confidence, self.every_n_frames, self.hand_model_path)
            return str(self._hand_detector.info()["status"])
        if self.target not in COCO_CLASSES:
            return f"unsupported_object: {self.requested_target}"
        try:
            from ultralytics import YOLO

            self._model = YOLO(self.model_name)
            names = self._model.names
            self._class_id = next(key for key, name in names.items() if name == self.target)
            return "ready"
        except Exception as exc:
            self._model = None
            return f"unavailable: {exc}"

    def info(self) -> dict[str, object]:
        return {
            "requested_object": self.requested_target,
            "target_object": self.target,
            "status": self._status,
            "confidence": self.confidence,
            "every_n_frames": self.every_n_frames,
            "model": self.model_name,
            "hand_model": self.hand_model_path,
            "boxes": self._box_count(),
        }

    def annotate(self, frame: np.ndarray) -> np.ndarray:
        if self._hand_detector:
            self._status = str(self._hand_detector.info()["status"])
            return self._hand_detector.annotate(frame)
        if self._model and self._class_id is not None:
            self._frame_count += 1
            if self._frame_count % self.every_n_frames == 1:
                self._boxes = self._detect(frame)
        for box in self._boxes:
            cv2.rectangle(frame, (box.x1, box.y1), (box.x2, box.y2), (0, 255, 0), 2)
        return frame

    def _detect(self, frame: np.ndarray) -> list[DetectionBox]:
        results = self._model.predict(
            frame,
            classes=[self._class_id],
            conf=self.confidence,
            imgsz=320,
            verbose=False,
        )
        boxes: list[DetectionBox] = []
        for result in results:
            for xyxy in result.boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = xyxy.astype(int).tolist()
                boxes.append(DetectionBox(x1, y1, x2, y2))
        return boxes

    def _box_count(self) -> int:
        if self._hand_detector:
            return int(self._hand_detector.info()["boxes"])
        return len(self._boxes)
