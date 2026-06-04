import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'my_robot_in_warehouse'
    
    world_file_path = os.path.join(
        get_package_share_directory(package_name),
        'worlds',
        'warehouse.world'
    )

    gazebo_ros_share = get_package_share_directory('gazebo_ros')
    gazebo_launch = os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')

    return LaunchDescription([

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gazebo_launch),
            launch_arguments={'world': world_file_path}.items()
        ),


        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_lidar_broadcaster',
            arguments=['0.15', '0', '0.1', '0', '0', '0', 'base_link', 'lidar_link'],
            parameters=[{
                'use_sim_time': True
            }]
        )
    ])
