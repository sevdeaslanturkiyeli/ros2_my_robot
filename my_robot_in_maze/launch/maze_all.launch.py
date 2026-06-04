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
        
        # 1. Gazebo Simülasyonu ve Robotu Dünyaya Doğuran Sistem Launch'ı
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(system_launch_path)
        ),
        
        # 2. SLAM Toolbox (Harita Motoru) Launch'ı
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch_path)
        ),

        # 3. İşlemciyi Kurtaran Statik TF Yayıncısı (LIDAR'ın 10 kHz'lik Çılgınlığını Susturur)
        # Parametreler: X Y Z Roll Pitch Yaw Parent_Frame Child_Frame
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='static_lidar_tf_publisher',
            arguments=['0.0', '0.0', '0.1', '0', '0', '0', 'vehicle_blue/chassis', 'vehicle_blue/lidar_link/gpu_lidar'],
            parameters=[{'use_sim_time': True}],
            output='screen'
        ),

        # 4. RViz2 Görselleştirme Ekranı
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_path],
            parameters=[{'use_sim_time': True}], 
            output='screen'
        )
    ])
