# Navi Drone — where navigation meets intelligence

Lightweight real-time face detection + recognition: train/enroll on your
laptop, deploy on a Raspberry Pi 4 with a USB webcam, monitor live from a
phone dashboard over your local WiFi.

## How it works

YuNet (face detection) and SFace (face recognition) are small pretrained
ONNX models run through OpenCV's built-in DNN backend — no PyTorch/TensorFlow,
no GPU, and they run comfortably on a Pi 4's CPU. "Training" here means
**enrollment**: you capture a handful of photos per known person on your
laptop, the engine stores their face embeddings, and at runtime each new
face is matched against that small database by similarity. This is the
practical approach for recognizing a known set of people — training a
network from scratch would need thousands of images per person.

```
core/            shared engine — identical code on laptop and Pi
  face_engine.py   detection + recognition + enrollment database
  enroll.py        quick webcam tool: capture straight into known_faces.json
  capture_dataset.py  saves raw face image crops to dataset/<name>/ for review
  build_embeddings_from_dataset.py  turns dataset/ images into known_faces.json
  recognize_test.py local live-preview test (run on laptop before deploying)
  download_models.sh  fetches the YuNet + SFace weights

pi_server/       runs on the Pi 4
  main.py          FastAPI server: MJPEG stream, REST API, WebSocket events
  database.py      SQLite detection log
  navi-drone.service  optional systemd unit for auto-start on boot

mobile_app/      Expo (React Native) dashboard — Live / Logs / Stats / Settings
```

## 1. Laptop: set up and enroll people

```bash
cd core
pip install -r requirements.txt
./download_models.sh
```

Two ways to register people, pick whichever fits:

**Quick enrollment** — captures embeddings directly, nothing saved to disk
but the final vectors:

```bash
python enroll.py
```

Press `n` to name the person, `c` to capture a few samples, `q` when done.

**Dataset capture** — saves the actual face image crops to `dataset/<name>/`
first, so you can review and delete bad shots before they ever become
embeddings, re-run the build step without a new capture session, or mix in
your own photos:

```bash
python capture_dataset.py
```

Press `n` to set a name, then `c` for a burst of 20 shots over a few seconds
(move your head slightly between shots for angle variety), or SPACE for a
single capture. Blurry frames are automatically skipped. Once you're happy
with the images in `dataset/<name>/`, build the embeddings:

```bash
python build_embeddings_from_dataset.py
```

Re-running this after adding/deleting images in `dataset/` rebuilds that
person's entries from whatever's currently in their folder — both tools
write to the same `known_faces.json`, so you can mix and match.

Sanity check before deploying — `python recognize_test.py` opens a live
window with boxes and names drawn on your webcam feed.

## 2. Deploy to the Pi 4

Copy the whole project to the Pi (the `core/models/` weights and
`core/known_faces.json` you just created travel with it):

```bash
scp -r navi-drone pi@<pi-ip>:~/
```

On the Pi:

```bash
cd ~/navi-drone/pi_server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Plug in the USB webcam first — `cv2.VideoCapture(0)` expects it at index 0;
check `ls /dev/video*` if you have other capture devices and adjust
`CAMERA_INDEX` in `pi_server/main.py`.

To auto-start on boot, edit the paths in `navi-drone.service` to match your
setup, then:

```bash
sudo cp navi-drone.service /etc/systemd/system/
sudo systemctl enable --now navi-drone
```

**Performance tip:** the Pi 4 is the bottleneck, not the model. If frames lag,
raise `PROCESS_EVERY_N_FRAMES` in `main.py` (process fewer frames per second)
or lower `input_size` in `FaceEngine.__init__` (e.g. `(256, 256)`).

## 3. Mobile app

```bash
cd mobile_app
npm install
npx expo start
```

Scan the QR code with the **Expo Go** app on your phone (same WiFi as the
Pi). On first launch, go to the Settings tab and enter the Pi's address —
try `navi-drone.local:8000` first, or use the Pi's IP directly (`hostname -I`
on the Pi) if your network doesn't support `.local` discovery. The Live tab
streams video and a real-time event ticker; Logs and Stats pull from the
Pi's REST API.

No native build tools needed — Expo Go runs it directly. To eventually ship
to the App/Play Store you'd run `eas build`, but that's a later step.

## Tuning recognition accuracy

`COSINE_MATCH_THRESHOLD` in `core/face_engine.py` (default `0.363`, SFace's
recommended value) controls how strict matching is. Raise it if strangers
are getting matched to known people; lower it if known people are showing
up as "Unknown".
