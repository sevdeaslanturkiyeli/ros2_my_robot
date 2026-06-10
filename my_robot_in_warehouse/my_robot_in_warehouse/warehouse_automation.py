#!/usr/bin/env python3
import time
from geometry_msgs.msg import PoseStamped
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import os
    
def main():
    rclpy.init()

    navigator = BasicNavigator()

    navigator.get_logger().info('Automation Mission')
    navigator.get_logger().info('Nav2 Active')


    # Waypoints
    
    goal_poses = []

    # Waypoint 1
    goal_pose1 = PoseStamped()
    goal_pose1.header.frame_id = 'map'
    goal_pose1.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose1.pose.position.x = 0.07770351157982001
    goal_pose1.pose.position.y = -1.1712246227377296
    goal_pose1.pose.orientation.w = 1.0
    goal_poses.append(goal_pose1)

    # Waypoint 2
    goal_pose2 = PoseStamped()
    goal_pose2.header.frame_id = 'map'
    goal_pose2.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose2.pose.position.x = -2.2917424747657633
    goal_pose2.pose.position.y = -1.027470744501762
    goal_pose2.pose.orientation.w = 1.0
    goal_poses.append(goal_pose2)

    # Waypoint 3
    goal_pose3 = PoseStamped()
    goal_pose3.header.frame_id = 'map'
    goal_pose3.header.stamp = navigator.get_clock().now().to_msg()
    goal_pose3.pose.position.x = -3.71548998230989
    goal_pose3.pose.position.y = 2.7473782709808297
    goal_pose3.pose.orientation.w = 1.0
    goal_poses.append(goal_pose3)

    
    navigator.get_logger().info('Warehouse Automation Began')
    
    navigator.followWaypoints(goal_poses)


    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            navigator.get_logger().info(f'Goal Index: {feedback.current_waypoint}')
        time.sleep(2)


    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info('Successed')
    elif result == TaskResult.CANCELED:
        navigator.get_logger().info('Mission canceled.')
    elif result == TaskResult.FAILED:
        navigator.get_logger().info('Mission failed.')

    navigator.lifecycleShutdown()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
