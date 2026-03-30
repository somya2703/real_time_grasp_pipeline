#!/bin/bash

echo "Training RL grasp policy..."
echo ""
echo "To monitor training, run in a separate terminal:"
echo "  bash scripts/tensorboard.sh"
echo "Then open http://localhost:6006 in your browser."
echo ""

export PYTHONPATH=/workspace:$PYTHONPATH


/isaac-sim/python.sh rl/train_rl.py
