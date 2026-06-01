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
                    'use_sim_time': True,
                    

                    'resolution': 0.02,             
                    'max_laser_range': 6.0,         
                    'minimum_travel_distance': 0.1,  
                    'minimum_travel_heading': 0.1,   
                    

                    'scan_matcher_search_space_size': 0.4, 
                    'scan_matcher_beta': 0.5,
                    

                    'minimum_cooperative_proportion': 0.8,
                    'link_match_minimum_response_coarse': 0.1,
                    'link_match_minimum_response_fine': 0.7,
                    
                    'transform_timeout': 0.2,
                    'tf_buffer_duration': 30.0
                }
            ]
        )
    ])
