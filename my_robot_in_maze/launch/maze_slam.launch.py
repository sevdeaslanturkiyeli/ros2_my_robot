from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='chassis_to_lidar_broadcaster',
            arguments=[
                '--x', '0', '--y', '0', '--z', '0',
                '--yaw', '0', '--pitch', '0', '--roll', '0',
                '--frame-id', 'vehicle_blue/chassis',
                '--child-frame-id', 'vehicle_blue/lidar_link/gpu_lidar'
            ],
            output='screen'
        ),


        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                {
                    'odom_frame': 'vehicle_blue/odom',
                    'base_frame': 'vehicle_blue/chassis',
                    'scan_topic': '/scan',
                    'use_sim_time': True
                }
            ]
        )
    ])
