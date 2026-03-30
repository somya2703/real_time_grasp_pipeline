import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import json
import time


class GraspActionServer(Node):

    def __init__(self):
        super().__init__('grasp_action_server')

        self.subscription = self.create_subscription(
            String,
            '/grasp_candidates',
            self.callback,
            10
        )

        self.get_logger().info("Grasp action server ready")

    def callback(self, msg):
        grasps = json.loads(msg.data)

        if len(grasps) == 0:
            self.get_logger().warn("No grasp candidates received")
            return

        best_grasp = grasps[0]

        self.get_logger().info(
            f"Executing grasp at pose={best_grasp['pose']} "
            f"approach={best_grasp['approach']}"
        )

        # TODO: replace with real robot arm commander
        time.sleep(1)

        self.get_logger().info("Grasp execution complete")


def main():
    rclpy.init()
    node = GraspActionServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()