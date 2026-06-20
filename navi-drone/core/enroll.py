"""
Navi Drone - enrollment tool.

Run this on your laptop with your webcam pointed at the person you want to
register. It detects the largest face in frame and lets you capture several
samples (different angles/expressions help accuracy).

Controls:
  c  - capture current face under the given name
  d  - delete a person and all their samples
  l  - list enrolled people
  q  - quit

After enrolling, copy core/known_faces.json and core/models/ to the Pi.
"""

import sys

import cv2

from face_engine import FaceEngine, draw_results


def largest_face(faces):
    if len(faces) == 0:
        return None
    areas = faces[:, 2] * faces[:, 3]
    return faces[areas.argmax()]


def main():
    engine = FaceEngine()
    cap = cv2.VideoCapture(0)  # change index if you have multiple cameras
    if not cap.isOpened():
        print("Could not open webcam.")
        sys.exit(1)

    current_name = None
    print("Enrollment tool running. Press 'c' to capture, 'q' to quit.")
    print("Currently enrolled:", engine.list_people())

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

        status = f"Target: {current_name or '(none set)'}  |  c=capture  l=list  d=delete  q=quit"
        cv2.putText(preview, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        cv2.imshow("Navi Drone - Enrollment", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("c"):
            if face is None:
                print("No face detected, try again.")
                continue
            if current_name is None:
                current_name = input("Enter name for this person: ").strip()
            engine.enroll(current_name, frame, face)
            print(f"Captured sample for '{current_name}' "
                  f"(total samples: {engine.list_people()[current_name]})")
        elif key == ord("l"):
            print("Enrolled people:", engine.list_people())
        elif key == ord("d"):
            name = input("Name to delete: ").strip()
            engine.remove_person(name)
            print("Removed.", "Now enrolled:", engine.list_people())
            if name == current_name:
                current_name = None
        elif key == ord("n"):
            current_name = input("Enter name for this person: ").strip()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
