import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

from ultralytics import YOLO
import json
import os
import time


class YoloDetector(Node):

    def __init__(self):
        super().__init__('yolo_detector')

        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.publisher = self.create_publisher(
            String,
            '/detections',
            10
        )

        engine_path = "/workspace/models/yolov8n.engine"
        pt_path = "/workspace/models/yolov8n.pt"

        # Always start with .pt — the existing .engine was built with an older
        # TensorRT version and will fail deserialization on the new container.
        self.get_logger().info("Loading YOLO .pt model...")
        pt_model = YOLO(pt_path, task="detect")

        # Try to re-export a fresh engine compatible with installed TensorRT
        try:
            self.get_logger().info("Exporting fresh TensorRT engine (first run only, ~60s)...")
            pt_model.export(format="engine", device=0, half=True, imgsz=640)
            self.model = YOLO(engine_path, task="detect")
            self.get_logger().info("YOLO using fresh TensorRT engine")
        except Exception as e:
            self.get_logger().warn(
                f"TensorRT export failed ({e}), using .pt model instead"
            )
            self.model = pt_model

        self.get_logger().info("YOLO detector initialized")

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")

        start = time.time()

        results = self.model(frame, verbose=False)

        detections = []

        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf)
            cls = int(box.cls)

            detections.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": conf,
                "class": cls
            })

        latency = (time.time() - start) * 1000

        msg_out = String()
        msg_out.data = json.dumps({
            "detections": detections,
            "latency_ms": round(latency, 2)
        })

        self.publisher.publish(msg_out)
        self.get_logger().info(
            f"Detected {len(detections)} objects | latency: {latency:.1f}ms",
            throttle_duration_sec=2.0
        )


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()