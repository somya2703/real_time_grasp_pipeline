#!/bin/bash

set -e

source /opt/ros/humble/setup.bash

cd /workspace/ros2_ws

echo "Building ROS2 workspace..."
colcon build

source install/setup.bash

echo "Launching perception pipeline..."
ros2 launch grasp_pipeline pipeline.launch.py