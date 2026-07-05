# Operation 'Eye of Sauron'

Camera proof of concept for an RTSP stream on a Raspberry Pi.

## What it does

- Reads the RTSP URL from `.env`
- Connects to the camera with OpenCV
- Detects a configured object or hand and draws green rectangles
- Serves a live MJPEG stream from FastAPI
- Shows the stream in a simple HTML page
- Falls back to a placeholder frame when the camera is offline

## Setup

1. Create a virtual environment if you want one.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the sample env file and edit the camera URL:

```bash
cp .env.example .env
```

4. Put your RTSP URL into `.env`:

```env
RTSP_URL=rtsp://user:password@camera-ip:554/stream1
STREAM_WIDTH=1280
STREAM_HEIGHT=720
JPEG_QUALITY=90
STREAM_FPS=15
detect_object=hand
DETECT_CONFIDENCE=0.45
DETECT_EVERY_N_FRAMES=3
YOLO_MODEL=yolo11n.pt
HAND_MODEL_PATH=models/hand_landmarker.task
```

## Run

```bash
bash run.sh
```

Then open:

```text
http://127.0.0.1:8000
```

## Notes

- The page uses a simple `<img>` tag with an MJPEG stream.
- Stream quality can be tuned with `STREAM_WIDTH`, `STREAM_HEIGHT`, `JPEG_QUALITY`, and `STREAM_FPS`.
- Hand detection uses MediaPipe when `detect_object=hand`.
- Object detection uses YOLO labels. `kid`, `child`, and `human` are treated as `person`.
- Unsupported labels, such as `hat` with the default COCO model, are reported in `/api/status` and do not stop the stream.
- If the RTSP source drops, the server keeps running and shows a placeholder image.
- `GET /api/status` returns the current camera status.
