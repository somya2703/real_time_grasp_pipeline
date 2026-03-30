import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2

class CameraNode(Node):


    def __init__(self):

        super().__init__('camera_node')

    # ROS publisher
        self.publisher = self.create_publisher(
            Image,
            '/camera/image_raw',
            10
        )

        self.bridge = CvBridge()

    # Load test image once
        self.frame = cv2.imread("/workspace/test_data/test.jpg")

        if self.frame is None:
            self.get_logger().error("Test image not found!")
        else:
            self.get_logger().info("Loaded test image successfully")

    # Publish image every second
        self.timer = self.create_timer(
            1.0,
            self.publish_image
        )

    def publish_image(self):

        if self.frame is None:
            return

        msg = self.bridge.cv2_to_imgmsg(self.frame, encoding="bgr8")
        self.publisher.publish(msg)


def main():

    rclpy.init()

    node = CameraNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()

if __name__ == "__main__":
    main()
