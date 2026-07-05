from dataclasses import dataclass
from pathlib import Path
import os


def load_dotenv_file(path: str = ".env") -> None:
    file_path = Path(path)
    if not file_path.exists():
        return
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key.strip(), value)


@dataclass(frozen=True)
class Settings:
    rtsp_url: str
    stream_width: int
    stream_height: int
    jpeg_quality: int
    stream_fps: float
    detect_object: str
    detect_confidence: float
    detect_every_n_frames: int
    yolo_model: str
    hand_model_path: str
    onvif_port: int


def int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def get_settings() -> Settings:
    load_dotenv_file()
    return Settings(
        rtsp_url=os.getenv("RTSP_URL", "").strip(),
        stream_width=max(320, int_env("STREAM_WIDTH", 1280)),
        stream_height=max(180, int_env("STREAM_HEIGHT", 720)),
        jpeg_quality=min(100, max(50, int_env("JPEG_QUALITY", 90))),
        stream_fps=min(30.0, max(1.0, float_env("STREAM_FPS", 15.0))),
        detect_object=os.getenv("detect_object", "").strip().lower(),
        detect_confidence=min(1.0, max(0.05, float_env("DETECT_CONFIDENCE", 0.45))),
        detect_every_n_frames=max(1, int_env("DETECT_EVERY_N_FRAMES", 3)),
        yolo_model=os.getenv("YOLO_MODEL", "yolo11n.pt").strip() or "yolo11n.pt",
        hand_model_path=os.getenv("HAND_MODEL_PATH", "models/hand_landmarker.task").strip(),
        onvif_port=max(1, int_env("ONVIF_PORT", 2020)),
    )
