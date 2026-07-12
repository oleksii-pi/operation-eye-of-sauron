from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.camera import CameraStream
from app.camera_direction import CameraDirection
from app.config import get_settings
from app.latency_probe import LatencyProbe
from app.motion_detector import MotionDetector
from app.power_control import PowerControl
from app.recorder import FrameRecorder


settings = get_settings()
recordings_dir = Path(__file__).resolve().parents[1] / "recordings"
detector = MotionDetector(
    settings.motion_min_size_cm,
    settings.motion_distance_cm,
    settings.motion_horizontal_fov_degrees,
)
camera = CameraStream(
    settings.rtsp_url,
    width=settings.stream_width,
    height=settings.stream_height,
    jpeg_quality=settings.jpeg_quality,
    fps=settings.stream_fps,
    detector=detector,
    recorder=FrameRecorder(recordings_dir, fps=20.0),
)
direction = CameraDirection(settings.rtsp_url, settings.onvif_port)
latency = LatencyProbe(camera, direction)
light_controller = PowerControl(settings.light_on_ms)
app = FastAPI(title="operation-eye-of-sauron")
static_dir = Path(__file__).resolve().parent / "static"
index_file = static_dir / "index.html"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class DirectionRequest(BaseModel):
    horizontal: int
    vertical: int


class MotionSizeRequest(BaseModel):
    min_size_cm: float


class MotionRequest(BaseModel):
    enabled: bool


class RecordingRequest(BaseModel):
    fps: float = 20.0


class LightRequest(BaseModel):
    enabled: bool
    address: str = ""


@app.on_event("startup")
def startup() -> None:
    camera.start()


@app.on_event("shutdown")
def shutdown() -> None:
    camera.stop()


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(
        index_file.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store"},
    )


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
        "recording": camera.recording_info(),
        "direction": direction.info(),
        "latency": latency.info(),
        "light": light_controller.info(),
        "power": light_controller.info(),
    })


@app.post("/api/latency/start")
def start_latency() -> JSONResponse:
    return JSONResponse(latency.start())


@app.post("/api/recording/start")
def start_recording(request: RecordingRequest | None = None) -> JSONResponse:
    fps = min(60.0, max(1.0, request.fps if request else 20.0))
    return JSONResponse(camera.start_recording(fps))


@app.post("/api/recording/stop")
def stop_recording() -> JSONResponse:
    return JSONResponse(camera.stop_recording())


@app.post("/api/direction")
def move_direction(request: DirectionRequest) -> JSONResponse:
    return JSONResponse(direction.move(request.horizontal, request.vertical))


@app.post("/api/motion-size")
def set_motion_size(request: MotionSizeRequest) -> JSONResponse:
    return JSONResponse(detector.set_min_size_cm(request.min_size_cm))


@app.post("/api/motion")
def set_motion(request: MotionRequest) -> JSONResponse:
    return JSONResponse(detector.set_enabled(request.enabled))


@app.post("/api/light")
def set_light(request: LightRequest) -> JSONResponse:
    return JSONResponse(light_controller.set_enabled(request.enabled, request.address))


@app.post("/api/power")
def set_power(request: LightRequest) -> JSONResponse:
    return JSONResponse(light_controller.set_enabled(request.enabled, request.address))


def masked_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.username:
        return url
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    return urlunsplit((parts.scheme, f"***:***@{host}{port}", parts.path, parts.query, parts.fragment))
