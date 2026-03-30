import rclpy
from rclpy.node import Node
from rl.grasp_policy_loader import RLGraspPolicy

from std_msgs.msg import String

import json
import numpy as np


class GraspPlanner(Node):

    def __init__(self):

        super().__init__('grasp_planner')

        self.policy = RLGraspPolicy()

        self.subscription = self.create_subscription(
            String,
            '/objects_3d',
            self.callback,
            10
        )

        self.publisher = self.create_publisher(
            String,
            '/grasp_candidates',
            10
        )

        self.get_logger().info("Grasp planner initialized")

    def generate_grasps(self, centroid):

        x, y, z = centroid

        grasps = []

        grasps.append({
            "pose": [x, y, z + 0.1],
            "approach": "top"
        })

        grasps.append({
            "pose": [x + 0.05, y, z],
            "approach": "side"
        })

        grasps.append({
            "pose": [x, y + 0.05, z],
            "approach": "angled"
        })

        return grasps


    def callback(self, msg):

        objects = json.loads(msg.data)

        grasp_list = []

        for obj in objects:

            grasps = self.generate_grasps(obj["centroid"])

            state = obj["centroid"] + [0.1, 0.1, 0.1]

            action = self.policy.select_grasp(state)

            best_grasp = grasps[action]

            grasp_list.append(best_grasp)

        msg_out = String()
        msg_out.data = json.dumps(grasp_list)

        self.publisher.publish(msg_out)

def main():

    rclpy.init()

    node = GraspPlanner()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()

if __name__ == "__main__":
    main()