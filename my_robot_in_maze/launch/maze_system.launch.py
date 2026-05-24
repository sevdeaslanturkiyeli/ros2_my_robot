import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node

def generate_launch_description():
    
    world_path = '/home/sevde/ros2_myws/src/my_robot/my_robot_in_maze/worlds/maze.world'
    models_path = '/home/sevde/ros2_myws/src/my_robot/my_robot_in_maze/models'

    return LaunchDescription([
        
        SetEnvironmentVariable(name='GZ_SIM_RESOURCE_PATH', value=models_path),
        SetEnvironmentVariable(name='QT_QPA_PLATFORM', value='xcb'),

        ExecuteProcess(
            cmd=['ign', 'gazebo', '-r', world_path],
            output='screen'
        ),

        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'
            ],
            output='screen'
        )
    ])
