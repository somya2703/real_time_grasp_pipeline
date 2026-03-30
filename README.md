# Real-Time Robotic Grasp Pipeline

A real-time perception and grasp planning pipeline for robotic manipulation, built with ROS2, Isaac Sim, and deep learning. The system detects objects from a camera feed, estimates their 3D positions using monocular depth estimation, selects grasp poses using a learned RL policy, and executes grasp actions — all as a live ROS2 node graph.

---

## Demo

> Two-part demo: Isaac Sim physics simulation followed by the full perception pipeline running end-to-end.

<!-- Replace with your actual video link -->
[![Demo Video](https://img.shields.io/badge/Demo-Video-blue)](https://github.com/YOUR_USERNAME/real_time_grasp_pipeline)

---

## Architecture

```
camera_node
    │
    │  /camera/image_raw  (sensor_msgs/Image)
    ▼
yolo_detector  ──────────────────────────────────────────────────────┐
    │                                                                │
    │  /detections  (JSON: bboxes, confidence, latency)              │
    ▼                                                                │
depth_estimator  (MiDaS DPT-Large)                                   │
    │                                                                │
    │  /objects_3d  (JSON: 3D centroids, depth in metres)            │
    ▼                                                                │
grasp_planner  (RL Policy: PPO)                                      │
    │                                                                │
    │  /grasp_candidates  (JSON: pose, approach direction)           │
    ▼                                                                │
grasp_action_server ◄────────────────────────────────────────────────┘
```

Isaac Sim runs in a separate process and can publish synthetic camera frames directly to `/camera/image_raw`, replacing the static test image with physics-simulated scene data.

---

## Tech Stack

| Component | Technology |
|---|---|
| Simulation | NVIDIA Isaac Sim 4.2 |
| Robot middleware | ROS2 Humble |
| Object detection | YOLOv8n (Ultralytics) — TensorRT + .pt fallback |
| Depth estimation | MiDaS DPT-Large 384 |
| RL policy | PPO via Stable-Baselines3 |
| Training monitoring | TensorBoard |
| Container runtime | Docker + NVIDIA Container Toolkit |
| Base image | `nvcr.io/nvidia/isaac-sim:4.2.0` |
| Python | 3.10 (system) + Isaac Sim bundled Python |
| GPU compute | CUDA 13, cuDNN, TensorRT 8.6+ |

---

## Project Structure

```
real_time_grasp_pipeline/
├── docker/
│   ├── Dockerfile              
│   ├── docker-compose.yml
│   └── entrypoint.sh
├── isaac_sim/
│   └── launch_sim.py           # Isaac Sim scene + ROS2 image publisher
├── ros2_ws/
│   └── src/grasp_pipeline/
│       ├── grasp_pipeline/
│       │   ├── camera_node.py
│       │   ├── yolo_detector.py
│       │   ├── depth_estimator.py
│       │   ├── grasp_planner.py
│       │   └── grasp_action_server.py
│       └── launch/
│           └── pipeline.launch.py
├── rl/
│   ├── envs/grasp_env.py       # Gymnasium environment
│   ├── train_rl.py             # PPO training with TensorBoard logging
│   └── grasp_policy_loader.py
├── MiDaS/                     
├── models/                     # Weights (not tracked by git — see below)
│   └── checkpoints/           
├── logs/
│   └── ppo_grasp/              
├── configs/
│   ├── pipeline.yaml
│   ├── grasp.yaml
│   └── yolo.yaml
├── visualization/
│   └── pipeline_monitor.py     
├── scripts/
│   ├── run_pipeline.sh
│   ├── run_sim.sh
│   ├── train_rl.sh
│   ├── tensorboard.sh
│   └── record_demo.sh
├── demo/
│   └── demo_script.sh
├── requirements.txt           
└── requirements-ros.txt        
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/real_time_grasp_pipeline.git
cd real_time_grasp_pipeline
git submodule update --init --recursive   # pulls MiDaS
```

### 2. Download model weights

```bash
# MiDaS DPT-Large (~1.3GB)
mkdir -p MiDaS/weights
wget https://github.com/intel-isl/DPT/releases/download/1_0/dpt_large-midas-2f21e586.pt \
    -O MiDaS/weights/dpt_large-midas-2f21e586.pt

# Symlink into models/
ln -sf /workspace/MiDaS/weights/dpt_large-midas-2f21e586.pt \
    models/dpt_large-midas-2f21e586.pt

# YOLOv8n weights are downloaded automatically by ultralytics on first run.
# The TensorRT engine is re-exported automatically if the version is incompatible.
```

### 3. Pull the Isaac Sim base image

```bash
docker pull nvcr.io/nvidia/isaac-sim:4.2.0
```

This is ~15GB. Do this before building.

### 4. Build the container

```bash
cd docker
docker compose build --no-cache 2>&1 | tee ../build.log
```

### 5. Start the container

```bash
docker compose up -d
docker exec -it grasp_pipeline bash
```

---

## Running

> **Important:** Isaac Sim and the full pipeline cannot run simultaneously on GPUs with less than 8GB VRAM. Run them separately.

### Run the perception pipeline

```bash
bash scripts/run_pipeline.sh
```

### Monitor all nodes live

In a second terminal inside the container:

```bash
source /opt/ros/humble/setup.bash
source /workspace/ros2_ws/install/setup.bash
python3 visualization/pipeline_monitor.py
```

Shows per-node message rates, detection bboxes, 3D object positions, grasp candidates, and action server status.

### Run the Isaac Sim scene

```bash
bash scripts/run_sim.sh
```

Isaac Sim publishes synthetic camera frames to `/camera/image_raw`. On a GPU with sufficient VRAM both can run together and the pipeline processes live sim data.

---

## RL Training

### Train the policy

```bash
bash scripts/train_rl.sh
```

Trains a PPO policy on the `GraspEnv` gymnasium environment for 200k timesteps. Saves:
- `models/grasp_policy.zip` — final model
- `models/best_model.zip` — best checkpoint by eval reward
- `models/checkpoints/` — intermediate checkpoints every 25k steps
- `logs/ppo_grasp/` — TensorBoard logs

### Monitor training with TensorBoard

In a second terminal inside the container:

```bash
bash scripts/tensorboard.sh
```

Then open **http://localhost:6006** in your browser.

TensorBoard tracks the following metrics:

| Tab | Metric | Description |
|---|---|---|
| `grasp/` | `mean_episode_reward` | Mean reward per rollout — rises toward +1 as policy improves |
| `grasp/` | `success_rate` | Fraction of grasps that succeed per rollout |
| `grasp/` | `mean_episode_length` | Steps per episode (always 1 for single-step env) |
| `grasp/` | `episodes_collected` | Running total of training episodes |
| `train/` | `policy_loss` | PPO policy gradient loss |
| `train/` | `value_loss` | Value function regression loss |
| `train/` | `entropy_loss` | Entropy bonus — encourages exploration |
| `train/` | `explained_variance` | How well value function predicts returns |
| `eval/` | `mean_reward` | Reward on held-out eval episodes every 5k steps |

If TensorBoard is not installed, run `pip3 install tensorboard` inside the container first.

---

## Known Bottlenecks

**Hardware**

The pipeline was developed and tested on a laptop RTX 4050 with 6GB VRAM, which is below the 8GB minimum Isaac Sim recommends. This means Isaac Sim and the ROS2 pipeline cannot run simultaneously without risking a system crash. On a workstation GPU (RTX 3090, A100, etc.) both run concurrently without issue.
