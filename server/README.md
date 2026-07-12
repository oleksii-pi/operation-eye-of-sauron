# Operation 'Eye of Sauron'

Mac-hosted camera control app for an RTSP stream with an ESP32-D0WDQ6 LED light controller.

## What it does

- Reads the RTSP URL from `.env`
- Connects to the camera with OpenCV
- Detects moving objects above a configured real-world size and draws green rectangles
- Serves a live MJPEG stream from FastAPI
- Shows the stream in a simple HTML page
- Sends UDP light commands to an ESP32-D0WDQ6 controller
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
LIGHT_ON_MS=200
STREAM_WIDTH=1280
STREAM_HEIGHT=720
JPEG_QUALITY=90
STREAM_FPS=15
MOTION_MIN_SIZE_CM=5
MOTION_DISTANCE_CM=200
MOTION_HORIZONTAL_FOV_DEGREES=62
ONVIF_PORT=2020
```

## Run

```bash
bash run.sh
```

Then open:

```text
http://127.0.0.1:8001
```

## Notes

- The page uses a simple `<img>` tag with an MJPEG stream.
- Stream quality can be tuned with `STREAM_WIDTH`, `STREAM_HEIGHT`, `JPEG_QUALITY`, and `STREAM_FPS`.
- Motion detection uses `MOTION_MIN_SIZE_CM` at `MOTION_DISTANCE_CM`.
- The page has a motion size slider that updates the threshold without restarting.
- The page has an `LED Controller UDP` field for the ESP32 target, for example `192.168.0.231:4210`.
- `MOTION_HORIZONTAL_FOV_DEGREES` should match the camera lens for better size estimates.
- If the RTSP source drops, the server keeps running and shows a placeholder image.
- `GET /api/status` returns the current camera status.
- `POST /api/motion-size` accepts `min_size_cm`.
- `POST /api/direction` accepts `horizontal` and `vertical` values from `-100` to `100`.
- Camera movement uses ONVIF absolute PTZ on `ONVIF_PORT`.
- `POST /api/light` accepts `enabled` and `address`, then sends UDP `on:200` or `off`.
- `POWER_ON_MS` is still accepted as a backward-compatible alias for `LIGHT_ON_MS`.
