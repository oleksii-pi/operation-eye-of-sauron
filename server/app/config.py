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
    motor_server_ip: str
    stream_width: int
    stream_height: int
    jpeg_quality: int
    stream_fps: float
    motion_min_size_cm: float
    motion_distance_cm: float
    motion_horizontal_fov_degrees: float
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
        motor_server_ip=os.getenv("motor_server_ip", "").strip(),
        stream_width=max(320, int_env("STREAM_WIDTH", 1280)),
        stream_height=max(180, int_env("STREAM_HEIGHT", 720)),
        jpeg_quality=min(100, max(50, int_env("JPEG_QUALITY", 90))),
        stream_fps=min(30.0, max(1.0, float_env("STREAM_FPS", 15.0))),
        motion_min_size_cm=min(100.0, max(1.0, float_env("MOTION_MIN_SIZE_CM", 5.0))),
        motion_distance_cm=max(1.0, float_env("MOTION_DISTANCE_CM", 200.0)),
        motion_horizontal_fov_degrees=min(170.0, max(10.0, float_env("MOTION_HORIZONTAL_FOV_DEGREES", 62.0))),
        onvif_port=max(1, int_env("ONVIF_PORT", 2020)),
    )
