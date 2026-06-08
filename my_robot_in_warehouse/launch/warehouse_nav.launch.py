import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'my_robot_in_warehouse'

    pkg_share = get_package_share_directory(package_name)
    world_file_path = os.path.join(pkg_share, 'worlds', 'warehouse.world')

    src_rviz_path = os.path.join(
        os.path.expanduser('~'),
        'ros2_myws', 'src', 'my_robot', 'my_robot_in_warehouse', 'rviz', 'warehouse_slam_map.rviz'
    )
    
    map_yaml_file = '/home/sevde/ros2_myws/src/my_robot/my_robot_in_warehouse/maps/warehouse_map/warehouse_map.yaml'

    urdf_file = '/home/sevde/ros2_myws/src/my_robot/my_robot_in_warehouse/models/my_robot.urdf'


    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    nav2_launch = os.path.join(nav2_bringup_share, 'launch', 'navigation_launch.py')

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

        # 2. ROBOT STATE PUBLISHER
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': True, 
                'robot_description': open(urdf_file, 'r').read()
            }]
        ),

        # Map -> Odom 
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='map_to_odom_broadcaster',
            output='screen',
            arguments=['--x', '0', '--y', '0', '--z', '0', 
                       '--roll', '0', '--pitch', '0', '--yaw', '0', 
                       '--frame-id', 'map', '--child-frame-id', 'odom'],
            parameters=[{'use_sim_time': True}]
        ),

        # Map server
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'use_sim_time': True, 
                'yaml_filename': map_yaml_file,
                'frame_id': 'map'
            }] 
        ),

       
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_map',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': ['map_server']
            }]
        ),

        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch),
            launch_arguments={
                'use_sim_time': 'true',
                'autostart': 'true',
                'use_sim_robot': 'true'
            }.items()
        ),

        # RVIZ2 
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', src_rviz_path],
            parameters=[{'use_sim_time': True}]
        ),
    ])

