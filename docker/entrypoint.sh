#!/bin/bash

source /opt/ros/humble/setup.bash

export PYTHONPATH=/workspace:/workspace/MiDaS:$PYTHONPATH

cd /workspace/ros2_ws
colcon build --symlink-install
source install/setup.bash

cd /workspace

exec "$@"