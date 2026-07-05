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


def get_settings() -> Settings:
    load_dotenv_file()
    return Settings(
        rtsp_url=os.getenv("RTSP_URL", "").strip(),
    )
