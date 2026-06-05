import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'my_robot_in_warehouse'
    

    pkg_share = get_package_share_directory(package_name)
    world_file_path = os.path.join(pkg_share, 'worlds', 'warehouse.world')


    src_rviz_path = os.path.join(
        os.path.expanduser('~'),
        'ros2_myws', 'src', 'my_robot', 'my_robot_in_warehouse', 'rviz', 'warehouse_slam.rviz'
    )
    

    src_models_path = os.path.join(os.path.expanduser('~'), 'ros2_myws', 'src', 'my_robot', 'my_robot_in_warehouse', 'models')
    install_models_path = os.path.join(pkg_share, 'models')
    combined_model_path = f"{os.environ.get('GAZEBO_MODEL_PATH', '')}:{src_models_path}:{install_models_path}"

    return LaunchDescription([

        SetEnvironmentVariable(name='GAZEBO_MODEL_PATH', value=combined_model_path),


        # GAZEBO 
        ExecuteProcess(
            cmd=['gazebo', '--verbose', world_file_path, '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so'],
            output='screen'
        ),


        # LIDAR STATIC TF KÖPRÜSÜ
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_lidar_broadcaster',
            output='screen',
            arguments=['--x', '0.15', '--y', '0', '--z', '0.1', 
                       '--roll', '0', '--pitch', '0', '--yaw', '0', 
                       '--frame-id', 'base_link', '--child-frame-id', 'lidar_link'],
            parameters=[{'use_sim_time': True}]
        ),


        # SLAM TOOLBOX 

        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='async_slam_toolbox_node',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'odom_frame': 'odom',
                'base_frame': 'base_link',
                'scan_topic': '/scan'
            }]
        ),

        # RVIZ2 
        
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', src_rviz_path],
            parameters=[{'use_sim_time': True}]
        )
    ])
