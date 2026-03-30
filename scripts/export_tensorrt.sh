#!/bin/bash

echo "Exporting YOLOv8 to TensorRT (safe mode)..."

yolo export \
model=models/yolov8n.pt \
format=engine \
device=0 \
imgsz=640 \
batch=1 \
workspace=2 \
half=False

echo "TensorRT engine generated."