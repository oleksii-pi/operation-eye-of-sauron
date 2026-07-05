from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from app.camera import CameraStream
from app.config import get_settings
from app.object_detector import ObjectDetector


settings = get_settings()
detector = ObjectDetector(
    settings.detect_object,
    settings.detect_confidence,
    settings.detect_every_n_frames,
    settings.yolo_model,
    settings.hand_model_path,
)
camera = CameraStream(
    settings.rtsp_url,
    width=settings.stream_width,
    height=settings.stream_height,
    jpeg_quality=settings.jpeg_quality,
    fps=settings.stream_fps,
    detector=detector,
)
app = FastAPI(title="Camera PoC")
index_file = Path(__file__).resolve().parent / "static" / "index.html"


@app.on_event("startup")
def startup() -> None:
    camera.start()


@app.on_event("shutdown")
def shutdown() -> None:
    camera.stop()


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/stream.mjpg")
def stream() -> StreamingResponse:
    headers = {"Cache-Control": "no-store", "Pragma": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(
        camera.stream(),
        headers=headers,
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/status")
def status() -> JSONResponse:
    stream = {
        "width": settings.stream_width,
        "height": settings.stream_height,
        "jpeg_quality": settings.jpeg_quality,
        "fps": settings.stream_fps,
    }
    return JSONResponse({
        "settings": {
            "rtsp_url": masked_url(settings.rtsp_url),
            "stream": stream,
            "detection": detector.info(),
        },
        "camera": camera.info(),
    })


def masked_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.username:
        return url
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    return urlunsplit((parts.scheme, f"***:***@{host}{port}", parts.path, parts.query, parts.fragment))
