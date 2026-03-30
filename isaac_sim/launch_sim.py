import isaacsim  
from isaacsim import SimulationApp


simulation_app = SimulationApp({"headless": True})

from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid, FixedCuboid
from omni.isaac.core.utils.extensions import enable_extension

import numpy as np
import signal
import sys
import cv2


enable_extension("omni.isaac.ros2_bridge")
simulation_app.update()


import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class IsaacSimPublisher(Node):
    """Publishes synthetic camera frames from Isaac Sim to ROS2."""

    def __init__(self):
        super().__init__('isaac_sim_camera')
        self.publisher = self.create_publisher(Image, '/camera/image_raw', 10)
        self.bridge = CvBridge()
        self.get_logger().info("Isaac Sim ROS2 camera publisher ready")

    def publish_frame(self, frame_bgr):
        msg = self.bridge.cv2_to_imgmsg(frame_bgr, encoding="bgr8")
        self.publisher.publish(msg)


def shutdown(ros_node, sim_app):
    """Clean shutdown — ROS2 first, then Isaac Sim."""
    try:
        ros_node.destroy_node()
    except Exception:
        pass
    try:
        rclpy.shutdown()
    except Exception:
        pass
    try:
        sim_app.close()
    except Exception:
        pass



rclpy.init()
ros_node = IsaacSimPublisher()

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

table = FixedCuboid(
    prim_path="/World/Table",
    name="table",
    position=np.array([0.5, 0.0, 0.2]),
    scale=np.array([0.8, 0.6, 0.05]),
    color=np.array([0.5, 0.35, 0.2]),
)
world.scene.add(table)

colors = [
    np.array([1.0, 0.2, 0.2]),
    np.array([0.2, 1.0, 0.2]),
    np.array([0.2, 0.2, 1.0]),
]

cubes = []
for i in range(3):
    cube = DynamicCuboid(
        prim_path=f"/World/Object_{i}",
        name=f"object_{i}",
        position=np.array([0.4 + i * 0.12, 0.0, 0.28]),
        scale=np.array([0.05, 0.05, 0.05]),
        color=colors[i],
        mass=0.1,
    )
    world.scene.add(cube)
    cubes.append(cube)

world.reset()

print("Isaac Sim scene initialized. Publishing to ROS2 /camera/image_raw...")

step = 0
publish_every = 60  

try:
    while simulation_app.is_running():
        world.step(render=False)
        step += 1

        if step % publish_every == 0:
            
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (40, 40, 40)

            
            cv2.rectangle(frame, (120, 100), (520, 380), (100, 70, 40), -1)

           
            cube_colors_bgr = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]
            for i, cube in enumerate(cubes):
                pos = cube.get_world_pose()[0]
                px = int(320 + pos[1] * 300)
                py = int(240 - pos[0] * 300)
                px = max(20, min(620, px))
                py = max(20, min(460, py))
                cv2.circle(frame, (px, py), 20, cube_colors_bgr[i], -1)
                cv2.putText(
                    frame, f"obj_{i}",
                    (px - 20, py - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1
                )

            cv2.putText(
                frame, f"Isaac Sim | Step: {step}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )

            ros_node.publish_frame(frame)
            rclpy.spin_once(ros_node, timeout_sec=0)

        if step % 100 == 0:
            print(f"Step {step} complete")

        if step >= 3000:
            print("Simulation complete.")
            break

except KeyboardInterrupt:
    print("Interrupted by user.")

finally:
    
    print("Shutting down...")
    shutdown(ros_node, simulation_app)
    print("Done.")
