#!/bin/bash

LOG_DIR="/workspace/logs/ppo_grasp"
PORT=6006

if [ ! -d "$LOG_DIR" ]; then
    echo "No logs found at $LOG_DIR"
    echo "Start training first with: bash scripts/train_rl.sh"
    exit 1
fi

echo "Starting TensorBoard..."
echo "  Logs : $LOG_DIR"
echo "  URL  : http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop."

tensorboard --logdir "$LOG_DIR" --host 0.0.0.0 --port $PORT
