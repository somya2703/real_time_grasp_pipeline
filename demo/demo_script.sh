#!/bin/bash


set -e

source /opt/ros/humble/setup.bash
source /workspace/ros2_ws/install/setup.bash

DEMO_DIR="/workspace/demo"
OUTPUT="/workspace/demo/demo_output.mp4"
DURATION=30  

mkdir -p "$DEMO_DIR"

echo "============================================"
echo "  Grasp Pipeline Demo Recording"
echo "============================================"
echo ""


echo "[1/3] Starting ROS2 pipeline..."
ros2 launch grasp_pipeline pipeline.launch.py &
PIPELINE_PID=$!


sleep 8
echo "      Pipeline running (PID $PIPELINE_PID)"


echo ""
echo "[2/3] Verifying data flow..."
echo "--- /detections (5 messages) ---"
timeout 8 ros2 topic echo /detections --once || true

echo ""
echo "--- /grasp_candidates (1 message) ---"
timeout 8 ros2 topic echo /grasp_candidates --once || true

echo ""
echo "--- Topic rates ---"
ros2 topic hz /camera/image_raw --window 5 &
HZ_PID=$!
sleep 6
kill $HZ_PID 2>/dev/null || true


echo ""
echo "[3/3] Recording ROS bag for $DURATION seconds..."
ros2 bag record \
    /camera/image_raw \
    /detections \
    /objects_3d \
    /grasp_candidates \
    --output "$DEMO_DIR/demo_bag" \
    --duration $DURATION &
BAG_PID=$!

echo "      Recording... (${DURATION}s)"
wait $BAG_PID


kill $PIPELINE_PID 2>/dev/null || true

echo ""
echo "============================================"
echo "  Demo complete!"
echo "  ROS bag saved to: $DEMO_DIR/demo_bag"
echo "============================================"
echo ""
echo "To replay: ros2 bag play $DEMO_DIR/demo_bag"
echo "To inspect: ros2 bag info $DEMO_DIR/demo_bag"