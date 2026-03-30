#!/bin/bash

mkdir -p models

echo "Downloading YOLOv8..."
wget -O models/yolov8n.pt \
https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

echo "Downloading MiDaS..."
wget -O models/midas_small.pt \
https://github.com/isl-org/MiDaS/releases/download/v3_1/dpt_swin2_tiny_256.pt

echo "Models downloaded successfully."
