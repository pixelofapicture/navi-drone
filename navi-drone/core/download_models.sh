#!/usr/bin/env bash
# Downloads the pretrained YuNet (face detection) and SFace (face recognition)
# ONNX models from the OpenCV Zoo. Run this once on your laptop, then copy the
# resulting core/models/ folder to the Pi (or re-run this script on the Pi).
set -e
cd "$(dirname "$0")/models"

echo "Downloading YuNet face detector..."
curl -L -o face_detection_yunet.onnx \
  "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"

echo "Downloading SFace face recognizer..."
curl -L -o face_recognition_sface.onnx \
  "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

echo "Done. Files:"
ls -lh
