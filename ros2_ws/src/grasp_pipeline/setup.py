from setuptools import setup
from glob import glob
import os

package_name = 'grasp_pipeline'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='Real-time robotic grasp pipeline',
    license='MIT',
    entry_points={
        'console_scripts': [
            'camera_node = grasp_pipeline.camera_node:main',
            'yolo_detector = grasp_pipeline.yolo_detector:main',
            'depth_estimator = grasp_pipeline.depth_estimator:main',
            'grasp_planner = grasp_pipeline.grasp_planner:main',
            'grasp_action_server = grasp_pipeline.grasp_action_server:main',
        ],
    },
)