import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    
    system_launch_path = '/home/sevde/ros2_myws/src/my_robot/my_robot_in_maze/launch/maze_system.launch.py'
    slam_launch_path = '/home/sevde/ros2_myws/src/my_robot/my_robot_in_maze/launch/maze_slam.launch.py'
    rviz_config_path = '/home/sevde/ros2_myws/src/my_robot/my_robot_in_maze/rviz/maze_slam.rviz' 

    return LaunchDescription([
        

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(system_launch_path)
        ),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch_path)
        ),


        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_path],
            parameters=[{'use_sim_time': True}], 
            output='screen'
        )
    ])
