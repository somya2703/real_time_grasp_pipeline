from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        Node(
            package='grasp_pipeline',
            executable='camera_node',
            name='camera_node',
            output='screen'
        ),

        Node(
            package='grasp_pipeline',
            executable='yolo_detector',
            name='yolo_detector',
            output='screen'
        ),

        Node(
            package='grasp_pipeline',
            executable='depth_estimator',
            name='depth_estimator',
            output='screen'
        ),

        Node(
            package='grasp_pipeline',
            executable='grasp_planner',
            name='grasp_planner',
            output='screen'
        ),

        Node(
            package='grasp_pipeline',
            executable='grasp_action_server',
            name='grasp_action_server',
            output='screen'
        ),

    ])