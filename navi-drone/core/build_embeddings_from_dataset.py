"""
Navi Drone - build embeddings from the dataset folder.

Walks dataset/<name>/*.jpg (created by capture_dataset.py, or your own
photos arranged the same way) and computes an embedding for each image,
writing them all into known_faces.json. Safe to re-run any time you add or
remove images - by default it rebuilds each person from scratch using
whatever's currently in their folder, so deleting a bad photo and re-running
this script is enough to drop it from recognition.

Usage:
    python build_embeddings_from_dataset.py
    python build_embeddings_from_dataset.py --only alice
"""

import argparse
import os

import cv2

from face_engine import FaceEngine

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")


def largest_face(faces):
    if len(faces) == 0:
        return None
    areas = faces[:, 2] * faces[:, 3]
    return faces[areas.argmax()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="only rebuild this one person", default=None)
    args = parser.parse_args()

    if not os.path.isdir(DATASET_DIR):
        print(f"No dataset folder found at {DATASET_DIR}. Run capture_dataset.py first.")
        return

    engine = FaceEngine()
    people = sorted(os.listdir(DATASET_DIR))
    if args.only:
        people = [p for p in people if p == args.only]

    for name in people:
        person_dir = os.path.join(DATASET_DIR, name)
        if not os.path.isdir(person_dir):
            continue

        embeddings = []
        skipped = 0
        for fname in sorted(os.listdir(person_dir)):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            img = cv2.imread(os.path.join(person_dir, fname))
            if img is None:
                skipped += 1
                continue
            faces = engine.detect(img)
            face = largest_face(faces)
            if face is None:
                skipped += 1
                continue
            embedding = engine.get_embedding(img, face)
            embeddings.append(embedding.flatten().tolist())

        if embeddings:
            engine.known[name] = embeddings
            print(f"{name}: {len(embeddings)} samples used, {skipped} skipped (no face / unreadable)")
        else:
            print(f"{name}: no usable images found, left out of the database")

    engine.save_db()
    print(f"\nSaved {engine.db_path}")


if __name__ == "__main__":
    main()
