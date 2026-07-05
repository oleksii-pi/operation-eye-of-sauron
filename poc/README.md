# Operation 'Eye of Sauron'

Camera proof of concept for an RTSP stream on a Raspberry Pi.

## What it does

- Reads the RTSP URL from `.env`
- Connects to the camera with OpenCV
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
- If the RTSP source drops, the server keeps running and shows a placeholder image.
- `GET /api/status` returns the current camera status.

