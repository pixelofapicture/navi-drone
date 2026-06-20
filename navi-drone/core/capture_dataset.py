"""
Navi Drone - dataset capture tool.

Unlike enroll.py (which captures embeddings straight into known_faces.json),
this saves actual face image *crops* to disk under dataset/<name>/, so you
end up with a reviewable, reusable image dataset:

    dataset/
      alice/
        0001.jpg
        0002.jpg
        ...
      bob/
        0001.jpg
        ...

Useful for: deleting bad/blurry shots before building embeddings, building
the dataset from multiple sessions or angles, or later regenerating
known_faces.json without re-recording anyone.

Controls:
  n        - set/change the name being captured
  c        - burst-capture (20 shots over a few seconds - move your head
             slightly between shots for angle variety)
  SPACE    - single capture
  q        - quit

After capturing, run build_embeddings_from_dataset.py to turn these images
into known_faces.json.
"""

import os
import sys
import time

import cv2

from face_engine import FaceEngine

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
CROP_MARGIN = 0.4        # extra context around the detected face box
CROP_SIZE = 400          # saved images are CROP_SIZE x CROP_SIZE
BURST_COUNT = 20
BURST_INTERVAL_S = 0.2
BLUR_THRESHOLD = 60.0    # lower = blurrier; skip frames under this


def largest_face(faces):
    if len(faces) == 0:
        return None
    areas = faces[:, 2] * faces[:, 3]
    return faces[areas.argmax()]


def is_sharp_enough(crop):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var() >= BLUR_THRESHOLD


def crop_with_margin(frame, face_row):
    h_frame, w_frame = frame.shape[:2]
    x, y, w, h = face_row[:4].astype(int)
    mx, my = int(w * CROP_MARGIN), int(h * CROP_MARGIN)
    x0, y0 = max(0, x - mx), max(0, y - my)
    x1, y1 = min(w_frame, x + w + mx), min(h_frame, y + h + my)
    crop = frame[y0:y1, x0:x1]
    if crop.size == 0:
        return None
    return cv2.resize(crop, (CROP_SIZE, CROP_SIZE))


def next_index(person_dir):
    existing = [f for f in os.listdir(person_dir) if f.lower().endswith(".jpg")]
    nums = [int(os.path.splitext(f)[0]) for f in existing if os.path.splitext(f)[0].isdigit()]
    return (max(nums) + 1) if nums else 1


def save_crop(person_dir, crop):
    idx = next_index(person_dir)
    path = os.path.join(person_dir, f"{idx:04d}.jpg")
    cv2.imwrite(path, crop)
    return path


def main():
    os.makedirs(DATASET_DIR, exist_ok=True)
    engine = FaceEngine()  # only used for detection here
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        sys.exit(1)

    current_name = None
    status_msg = ""
    burst_until = 0
    next_burst_shot = 0
    burst_taken = 0

    print("Dataset capture tool. Press 'n' to set a name, 'c' for a burst capture, 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        faces = engine.detect(frame)
        face = largest_face(faces)
        preview = frame.copy()
        if face is not None:
            x, y, w, h = face[:4].astype(int)
            cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 200, 0), 2)

        now = time.time()
        if now < burst_until and face is not None and now >= next_burst_shot:
            crop = crop_with_margin(frame, face)
            if crop is not None and is_sharp_enough(crop):
                person_dir = os.path.join(DATASET_DIR, current_name)
                save_crop(person_dir, crop)
                burst_taken += 1
                next_burst_shot = now + BURST_INTERVAL_S
                status_msg = f"Burst: {burst_taken}/{BURST_COUNT} captured"
        elif now >= burst_until and burst_taken:
            status_msg = f"Burst done ({burst_taken} saved). Move slightly and press 'c' again for more angles."
            burst_taken = 0

        header = f"Name: {current_name or '(press n)'}  |  c=burst  SPACE=single  q=quit"
        cv2.putText(preview, header, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        if status_msg:
            cv2.putText(preview, status_msg, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 220), 2)
        cv2.imshow("Navi Drone - Dataset Capture", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("n"):
            current_name = input("Enter name for this person: ").strip()
            os.makedirs(os.path.join(DATASET_DIR, current_name), exist_ok=True)
        elif key == ord("c"):
            if not current_name:
                print("Set a name first ('n').")
                continue
            if face is None:
                print("No face detected, try again.")
                continue
            burst_until = now + BURST_COUNT * BURST_INTERVAL_S
            next_burst_shot = now
            burst_taken = 0
        elif key == ord(" "):
            if not current_name:
                print("Set a name first ('n').")
                continue
            if face is None:
                print("No face detected, try again.")
                continue
            crop = crop_with_margin(frame, face)
            if crop is not None and is_sharp_enough(crop):
                person_dir = os.path.join(DATASET_DIR, current_name)
                path = save_crop(person_dir, crop)
                status_msg = f"Saved {os.path.basename(path)}"
            else:
                status_msg = "Too blurry, try again"

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
