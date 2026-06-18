import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    user_home = os.path.expanduser('~')
    package_name = 'my_robot_in_house'
    

    src_models_path = os.path.join(user_home, 'ros2_myws/src/my_robot', package_name, 'models')
    pkg_share = get_package_share_directory(package_name)
    install_models_path = os.path.join(pkg_share, 'models')
    
    current_gazebo_path = os.environ.get('GAZEBO_MODEL_PATH', '')
    combined_model_path = f"{current_gazebo_path}:{src_models_path}:{install_models_path}"
    
    set_gazebo_models = SetEnvironmentVariable(name='GAZEBO_MODEL_PATH', value=combined_model_path)

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    rtabmap_db_path = os.path.join(user_home, 'ros2_myws/src/my_robot/my_robot_in_house/maps/rtabmap.db')
    rviz_config_path = os.path.join(user_home, 'ros2_myws/src/my_robot/my_robot_in_house', package_name, 'rviz/vslam_rviz.rviz')

    launch_gazebo_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, 'launch', 'house_nav.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    nav2_bringup_share = get_package_share_directory('nav2_bringup')
    nav2_params_path = os.path.join(nav2_bringup_share, 'params', 'nav2_params.yaml')
    
    launch_nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_share, 'launch', 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': 'true',
            'autostart': 'true',
            'params_file': nav2_params_path
        }.items()
    )

    rtabmap_launch_dir = get_package_share_directory('rtabmap_launch')
    launch_rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(rtabmap_launch_dir, 'launch', 'rtabmap.launch.py')),
        launch_arguments={
            'database_path': rtabmap_db_path,
            'rtabmap_args': '--localization --Vis/MinInliers 5 --RGBD/OptimizeMaxError 0 --Mem/Incremental false', 
            'localization': 'true',          
            'approx_sync': 'true',           
            'queue_size': '50',              
            'wait_for_transform': '1.0',
            'rgb_topic': '/camera/image_raw',
            'depth_topic': '/camera/depth/image_raw',
            'camera_info_topic': '/camera/depth/camera_info', 
            'frame_id': 'base_link',
            'use_sim_time': use_sim_time,
            'visual_odometry': 'false',
            'odom_topic': '/odom',
            'qos': '2'
        }.items()
    )

    camera_static_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_static_tf_publisher',
        arguments=['0.2', '0', '0.1', '-1.570796', '0', '-1.570796', 'base_link', 'camera_depth_optical_link'],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    run_rviz2 = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    ld = LaunchDescription()
    ld.add_action(set_gazebo_models)
    ld.add_action(launch_gazebo_world)
    ld.add_action(launch_nav2)
    ld.add_action(launch_rtabmap)
    ld.add_action(camera_static_tf)
    ld.add_action(run_rviz2)

    return ld

