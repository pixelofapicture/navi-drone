"""
Navi Drone - local real-time test.

Run this on your laptop (after enrolling people with enroll.py) to verify
recognition works before deploying to the Pi. Same FaceEngine class will run
unchanged on the Pi inside the FastAPI server.
"""

import time

import cv2

from face_engine import FaceEngine, draw_results


def main():
    engine = FaceEngine()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    prev_t = time.time()
    fps = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        results = engine.process_frame(frame)
        draw_results(frame, results)

        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(now - prev_t, 1e-6))
        prev_t = now
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, frame.shape[0] - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("Navi Drone - Live Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
