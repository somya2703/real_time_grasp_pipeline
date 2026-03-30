#!/usr/bin/env python3


import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

import json
import time
import os
import threading
from collections import deque



RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
CLEAR   = "\033[2J\033[H"


class PipelineMonitor(Node):

    def __init__(self):
        super().__init__('pipeline_monitor')

        self.lock = threading.Lock()

        # Per-node state
        self.state = {
            "camera": {
                "last_msg": None, "count": 0, "hz": 0.0,
                "timestamps": deque(maxlen=10)
            },
            "yolo": {
                "last_msg": None, "count": 0, "hz": 0.0,
                "timestamps": deque(maxlen=10),
                "detections": [], "latency_ms": 0.0
            },
            "depth": {
                "last_msg": None, "count": 0, "hz": 0.0,
                "timestamps": deque(maxlen=10),
                "objects": []
            },
            "grasp_planner": {
                "last_msg": None, "count": 0, "hz": 0.0,
                "timestamps": deque(maxlen=10),
                "candidates": []
            },
        }

        self.start_time = time.time()

        
        self.create_subscription(Image, '/camera/image_raw',
                                 self.camera_cb, 10)
        self.create_subscription(String, '/detections',
                                 self.yolo_cb, 10)
        self.create_subscription(String, '/objects_3d',
                                 self.depth_cb, 10)
        self.create_subscription(String, '/grasp_candidates',
                                 self.grasp_cb, 10)

        
        self.create_timer(0.5, self.render)

    def _update(self, key, extra=None):
        now = time.time()
        with self.lock:
            s = self.state[key]
            s["count"] += 1
            s["last_msg"] = now
            s["timestamps"].append(now)
            if len(s["timestamps"]) >= 2:
                dt = s["timestamps"][-1] - s["timestamps"][0]
                if dt > 0:
                    s["hz"] = (len(s["timestamps"]) - 1) / dt
            if extra:
                s.update(extra)

    def camera_cb(self, msg):
        self._update("camera")

    def yolo_cb(self, msg):
        try:
            data = json.loads(msg.data)
            self._update("yolo", {
                "detections": data.get("detections", []),
                "latency_ms": data.get("latency_ms", 0.0)
            })
        except Exception:
            self._update("yolo")

    def depth_cb(self, msg):
        try:
            data = json.loads(msg.data)
            self._update("depth", {"objects": data})
        except Exception:
            self._update("depth")

    def grasp_cb(self, msg):
        try:
            data = json.loads(msg.data)
            self._update("grasp_planner", {"candidates": data})
        except Exception:
            self._update("grasp_planner")

    def fmt_time(self, ts):
        if ts is None:
            return f"{RED}never{RESET}"
        age = time.time() - ts
        if age < 2.0:
            return f"{GREEN}{age:.1f}s ago{RESET}"
        return f"{YELLOW}{age:.1f}s ago{RESET}"

    def fmt_hz(self, hz):
        if hz > 0.5:
            return f"{GREEN}{hz:.2f} Hz{RESET}"
        return f"{RED}{hz:.2f} Hz{RESET}"

    def render(self):
        with self.lock:
            s = dict(self.state)

        uptime = time.time() - self.start_time
        lines = []

        lines.append(f"{CLEAR}")
        lines.append(f"{BOLD}{CYAN}{'='*70}{RESET}")
        lines.append(f"{BOLD}{CYAN}  GRASP PIPELINE MONITOR   uptime: {uptime:.0f}s{RESET}")
        lines.append(f"{BOLD}{CYAN}{'='*70}{RESET}")
        lines.append("")

        # ── Node 1: Camera
        c = s["camera"]
        lines.append(f"{BOLD}{BLUE}[ NODE 1 ] camera_node{RESET}  →  /camera/image_raw")
        lines.append(f"  Rate     : {self.fmt_hz(c['hz'])}")
        lines.append(f"  Messages : {WHITE}{c['count']}{RESET}")
        lines.append(f"  Last msg : {self.fmt_time(c['last_msg'])}")
        lines.append("")

        # ── Node 2: YOLO
        y = s["yolo"]
        lines.append(f"{BOLD}{MAGENTA}[ NODE 2 ] yolo_detector{RESET}  →  /detections")
        lines.append(f"  Rate     : {self.fmt_hz(y['hz'])}")
        lines.append(f"  Messages : {WHITE}{y['count']}{RESET}")
        lines.append(f"  Latency  : {YELLOW}{y['latency_ms']:.1f} ms{RESET}")
        lines.append(f"  Last msg : {self.fmt_time(y['last_msg'])}")
        if y["detections"]:
            lines.append(f"  Detections ({len(y['detections'])}):")
            for i, d in enumerate(y["detections"][:3]):
                bb = d["bbox"]
                lines.append(
                    f"    [{i}] conf={d['confidence']:.2f}  "
                    f"bbox=[{bb[0]:.0f},{bb[1]:.0f},{bb[2]:.0f},{bb[3]:.0f}]"
                    f"  class={d.get('class', '?')}"
                )
        else:
            lines.append(f"  {YELLOW}No detections{RESET}")
        lines.append("")

        # ── Node 3: Depth Estimator
        d = s["depth"]
        lines.append(f"{BOLD}{GREEN}[ NODE 3 ] depth_estimator{RESET}  →  /objects_3d")
        lines.append(f"  Rate     : {self.fmt_hz(d['hz'])}")
        lines.append(f"  Messages : {WHITE}{d['count']}{RESET}")
        lines.append(f"  Last msg : {self.fmt_time(d['last_msg'])}")
        if d["objects"]:
            lines.append(f"  Objects 3D ({len(d['objects'])}):")
            for i, obj in enumerate(d["objects"][:3]):
                cx, cy, cz = obj["centroid"]
                lines.append(
                    f"    [{i}] x={cx:.1f}px  y={cy:.1f}px  "
                    f"depth={cz:.3f}m  conf={obj.get('confidence', 0):.2f}"
                )
        else:
            lines.append(f"  {YELLOW}No objects{RESET}")
        lines.append("")

        # ── Node 4: Grasp Planner
        g = s["grasp_planner"]
        lines.append(f"{BOLD}{YELLOW}[ NODE 4 ] grasp_planner{RESET}  →  /grasp_candidates")
        lines.append(f"  Rate     : {self.fmt_hz(g['hz'])}")
        lines.append(f"  Messages : {WHITE}{g['count']}{RESET}")
        lines.append(f"  Last msg : {self.fmt_time(g['last_msg'])}")
        if g["candidates"]:
            lines.append(f"  Grasp Candidates ({len(g['candidates'])}):")
            for i, gc in enumerate(g["candidates"][:3]):
                pose = gc.get("pose", [])
                approach = gc.get("approach", "?")
                lines.append(
                    f"    [{i}] approach={approach}  "
                    f"pose=[{', '.join(f'{v:.3f}' for v in pose)}]"
                )
        else:
            lines.append(f"  {YELLOW}No candidates{RESET}")
        lines.append("")

        # ── Node 5: Grasp Action Server (inferred from grasp candidates)
        lines.append(f"{BOLD}{RED}[ NODE 5 ] grasp_action_server{RESET}  →  executing grasps")
        if g["candidates"] and g["last_msg"] and (time.time() - g["last_msg"]) < 3.0:
            best = g["candidates"][0]
            lines.append(f"  Status   : {GREEN}ACTIVE{RESET}")
            lines.append(
                f"  Executing: approach={best.get('approach','?')}  "
                f"pose={best.get('pose', [])}"
            )
        else:
            lines.append(f"  Status   : {YELLOW}WAITING{RESET}")
        lines.append("")

        lines.append(f"{BOLD}{CYAN}{'='*70}{RESET}")
        lines.append(f"  Press Ctrl+C to exit monitor")
        lines.append(f"{BOLD}{CYAN}{'='*70}{RESET}")

        print("\n".join(lines), flush=True)


def main():
    rclpy.init()
    node = PipelineMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
