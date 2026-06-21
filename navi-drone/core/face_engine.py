"""
Navi Drone - core face recognition engine.

Wraps OpenCV's YuNet (detection) and SFace (recognition) models behind a
simple class. This module is identical on the laptop and the Pi 4 - the
only thing that changes is which script imports it (enroll.py on the
laptop, the FastAPI server on the Pi).

Models: https://github.com/opencv/opencv_zoo
"""

import json
import os
import time

import cv2
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
DETECTOR_PATH = os.path.join(MODELS_DIR, "face_detection_yunet.onnx")
RECOGNIZER_PATH = os.path.join(MODELS_DIR, "face_recognition_sface.onnx")

# SFace's recommended thresholds (from the OpenCV Zoo docs). Cosine similarity
# above this means "same person". Raise it for stricter matching (fewer false
# accepts), lower it if real matches are getting missed.
COSINE_MATCH_THRESHOLD = 0.363


class FaceEngine:
    def __init__(self, input_size=(320, 320), score_threshold=0.7, db_path=None):
        if not os.path.exists(DETECTOR_PATH) or not os.path.exists(RECOGNIZER_PATH):
            raise FileNotFoundError(
                "Model files missing. Run core/download_models.sh first."
            )

        self.detector = cv2.FaceDetectorYN_create(
            DETECTOR_PATH,
            "",
            input_size,
            score_threshold=score_threshold,
            nms_threshold=0.3,
            top_k=20,
        )
        self.recognizer = cv2.FaceRecognizerSF_create(RECOGNIZER_PATH, "")

        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), "known_faces.json"
        )
        self.known = self._load_db()  # {name: [embedding, embedding, ...]}

    # ---------- detection / recognition ----------

    def set_input_size(self, w, h):
        self.detector.setInputSize((w, h))

    def detect(self, frame):
        """Returns an array of detections, each row:
        [x, y, w, h, 5x(landmark x,y), score]
        """
        h, w = frame.shape[:2]
        self.set_input_size(w, h)
        _, faces = self.detector.detect(frame)
        return faces if faces is not None else np.empty((0, 15))

    def get_embedding(self, frame, face_row):
        """Aligns and crops the face, then returns its 128-d embedding."""
        aligned = self.recognizer.alignCrop(frame, face_row)
        return self.recognizer.feature(aligned)

    def identify(self, embedding):
        """Compares an embedding against the known-faces database.
        Returns (name, similarity) or ("Unknown", best_similarity)."""
        best_name, best_score = "Unknown", -1.0
        for name, embeddings in self.known.items():
            for known_emb in embeddings:
                known_arr = np.array(known_emb, dtype=np.float32).reshape(1, -1)
                score = self.recognizer.match(
                    embedding, known_arr,
                    cv2.FaceRecognizerSF_FR_COSINE,
                )
                if score > best_score:
                    best_name, best_score = name, score
        if best_score < COSINE_MATCH_THRESHOLD:
            return "Unknown", best_score
        return best_name, best_score

    def process_frame(self, frame):
        """Runs detection + recognition on one frame.
        Returns a list of dicts: bbox, name, similarity, score."""
        results = []
        faces = self.detect(frame)
        for f in faces:
            x, y, w, h = f[:4].astype(int)
            det_score = float(f[-1])
            embedding = self.get_embedding(frame, f)
            name, similarity = self.identify(embedding)
            results.append({
                "bbox": [int(x), int(y), int(w), int(h)],
                "name": name,
                "similarity": round(float(similarity), 3),
                "det_score": round(det_score, 3),
                "ts": time.time(),
            })
        return results

    # ---------- enrollment database ----------

    def _load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path) as fh:
                return json.load(fh)
        return {}

    def save_db(self):
        with open(self.db_path, "w") as fh:
            json.dump(self.known, fh)

    def enroll(self, name, frame, face_row):
        """Adds one embedding sample for `name`, computed from `frame`/`face_row`."""
        embedding = self.get_embedding(frame, face_row)
        self.known.setdefault(name, []).append(embedding.flatten().tolist())
        self.save_db()

    def remove_person(self, name):
        self.known.pop(name, None)
        self.save_db()

    def list_people(self):
        return {name: len(embs) for name, embs in self.known.items()}


def draw_results(frame, results):
    """Draws bounding boxes + name labels on a frame (for local preview)."""
    for r in results:
        x, y, w, h = r["bbox"]
        color = (0, 200, 0) if r["name"] != "Unknown" else (0, 0, 220)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = f"{r['name']} ({r['similarity']:.2f})"
        cv2.putText(frame, label, (x, max(y - 8, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return frame
