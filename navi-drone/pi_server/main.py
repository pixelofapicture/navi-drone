"""
Navi Drone - Pi 4 server.

Reads the USB webcam in a background thread, runs the shared FaceEngine on
every frame, and exposes:

  GET  /video_feed   - MJPEG stream with boxes/names drawn on it
  GET  /api/people   - enrolled people + sample counts
  GET  /api/logs     - recent detection log
  GET  /api/stats    - per-person counts for the dashboard
  WS   /ws/events     - pushes a message every time someone new is recognized
  GET  /api/health   - simple liveness check

Run with:  uvicorn main:app --host 0.0.0.0 --port 8000
"""

import asyncio
import sys
import threading
import time
from pathlib import Path

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

sys.path.append(str(Path(__file__).resolve().parent.parent / "core"))
from face_engine import FaceEngine, draw_results  # noqa: E402

import database

# ---- config ----
CAMERA_INDEX = 0
PROCESS_EVERY_N_FRAMES = 2   # skip frames to keep the Pi 4 CPU happy
JPEG_QUALITY = 70
SAME_PERSON_COOLDOWN_S = 15  # don't re-log/re-notify the same person constantly

app = FastAPI(title="Navi Drone")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local network only deployment; tighten if exposed further
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()
engine = FaceEngine()

_latest_jpeg = None
_latest_results = []
_lock = threading.Lock()
_last_seen = {}  # name -> last logged timestamp

_event_loop = None
_ws_clients = set()


def camera_loop():
    global _latest_jpeg, _latest_results

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"ERROR: could not open camera index {CAMERA_INDEX}")
        return

    frame_count = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.5)
            continue

        frame_count += 1
        if frame_count % PROCESS_EVERY_N_FRAMES == 0:
            results = engine.process_frame(frame)
            draw_results(frame, results)
            with _lock:
                _latest_results = results
            handle_events(results)

        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        if ok:
            with _lock:
                _latest_jpeg = buf.tobytes()


def handle_events(results):
    """Logs to SQLite and pushes a WebSocket event, with a per-person cooldown
    so a person standing in frame doesn't spam the log/app every frame."""
    now = time.time()
    for r in results:
        name = r["name"]
        last = _last_seen.get(name, 0)
        if now - last < SAME_PERSON_COOLDOWN_S:
            continue
        _last_seen[name] = now
        database.log_detection(name, r["similarity"], r["det_score"])
        broadcast_event(r)


def broadcast_event(result):
    if _event_loop is None:
        return
    asyncio.run_coroutine_threadsafe(_broadcast(result), _event_loop)


async def _broadcast(result):
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(result)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.discard(ws)


@app.on_event("startup")
async def on_startup():
    global _event_loop
    _event_loop = asyncio.get_event_loop()
    threading.Thread(target=camera_loop, daemon=True).start()
    try:
        advertise_mdns()
    except Exception as e:
        print(f"mDNS advertising not started ({e}); use the Pi's IP address in the app instead.")


def advertise_mdns():
    """Optional: makes the Pi discoverable as navi-drone.local on the LAN."""
    import socket

    from zeroconf import ServiceInfo, Zeroconf

    ip = socket.gethostbyname(socket.gethostname())
    info = ServiceInfo(
        "_http._tcp.local.",
        "Navi Drone._http._tcp.local.",
        addresses=[socket.inet_aton(ip)],
        port=8000,
        server="navi-drone.local.",
    )
    Zeroconf().register_service(info)
    print(f"Advertised as navi-drone.local ({ip})")


# ---------- routes ----------

def mjpeg_generator():
    while True:
        with _lock:
            frame = _latest_jpeg
        if frame is not None:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.03)


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/api/people")
def people():
    return engine.list_people()


@app.get("/api/logs")
def logs(limit: int = 100):
    return database.recent_logs(limit)


@app.get("/api/stats")
def stats():
    return database.stats()


@app.get("/api/health")
def health():
    with _lock:
        has_frame = _latest_jpeg is not None
    return JSONResponse({"status": "ok" if has_frame else "starting"})


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive; client doesn't need to send real data
    except WebSocketDisconnect:
        _ws_clients.discard(websocket)
