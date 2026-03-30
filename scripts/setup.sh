#!/bin/bash

echo "Setting up project..."

./scripts/download_models.sh

docker compose build

echo "Initializing ROS dependencies..."

source /opt/ros/humble/setup.bash

cd ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y

colcon build

echo "Setup complete."