import sys
import os

# MiDaS lives under /workspace/MiDaS — add to path so imports resolve
sys.path.insert(0, "/workspace/MiDaS")

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

import json
import numpy as np
import torch
import cv2

from midas.model_loader import load_model


class DepthEstimator(Node):

    def __init__(self):
        super().__init__('depth_estimator')

        self.bridge = CvBridge()

        # Subscribe to both raw image and detections
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.detection_sub = self.create_subscription(
            String,
            '/detections',
            self.detection_callback,
            10
        )

        self.publisher = self.create_publisher(
            String,
            '/objects_3d',
            10
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model, self.transform, self.net_w, self.net_h = load_model(
            device=self.device,
            model_path="/workspace/MiDaS/weights/dpt_large-midas-2f21e586.pt",
            model_type="dpt_large_384"
        )
        self.model.eval()

        # Store latest frame for depth inference
        self.latest_frame = None

        self.get_logger().info(f"Depth estimator ready (device: {self.device})")

    def image_callback(self, msg):
        """Cache the latest camera frame for use during detection callbacks."""
        self.latest_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")

    def run_midas(self, frame):
        """Run MiDaS on full frame, return normalized depth map."""
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) / 255.0
        sample = self.transform({"image": img})["image"]
        input_tensor = torch.from_numpy(sample).unsqueeze(0).to(self.device)

        with torch.no_grad():
            depth = self.model.forward(input_tensor)
            depth = torch.nn.functional.interpolate(
                depth.unsqueeze(1),
                size=frame.shape[:2],
                mode="bicubic",
                align_corners=False
            ).squeeze()

        depth_np = depth.cpu().numpy()

        # Normalize to 0-1 range (inverse depth — higher = closer)
        d_min, d_max = depth_np.min(), depth_np.max()
        if d_max > d_min:
            depth_np = (depth_np - d_min) / (d_max - d_min)

        return depth_np

    def detection_callback(self, msg):
        if self.latest_frame is None:
            return

        data = json.loads(msg.data)
        detections = data.get("detections", [])

        if not detections:
            msg_out = String()
            msg_out.data = json.dumps([])
            self.publisher.publish(msg_out)
            return

        # Run MiDaS on the full frame once
        depth_map = self.run_midas(self.latest_frame)

        h, w = self.latest_frame.shape[:2]
        objects_3d = []

        for det in detections:
            bbox = det["bbox"]
            x1, y1, x2, y2 = [int(v) for v in bbox]

            # Clamp to frame bounds
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            # Sample median depth in the bounding box region
            roi = depth_map[y1:y2, x1:x2]
            if roi.size > 0:
                # Inverse depth: convert to metric approximation (0.3–2.0m range)
                inv_depth = float(np.median(roi))
                depth_m = 0.3 + (1.0 - inv_depth) * 1.7
            else:
                depth_m = 1.0  # fallback

            objects_3d.append({
                "centroid": [round(cx, 2), round(cy, 2), round(depth_m, 3)],
                "confidence": det.get("confidence", 1.0),
                "class": det.get("class", 0)
            })

        msg_out = String()
        msg_out.data = json.dumps(objects_3d)
        self.publisher.publish(msg_out)

        self.get_logger().info(
            f"Published {len(objects_3d)} 3D objects",
            throttle_duration_sec=2.0
        )


def main():
    rclpy.init()
    node = DepthEstimator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()