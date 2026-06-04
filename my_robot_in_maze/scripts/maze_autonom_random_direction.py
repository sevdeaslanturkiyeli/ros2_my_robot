#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import random  

class MazeAutonomousNode(Node):
    def __init__(self):
        super().__init__('maze_autonomous_node')
        
        self.lidar_sub = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.hiz_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.target_linear_speed = 0.15  
        self.turn_speed = 0.32            
        self.critical_distance = 0.40  
        self.emergency_distance = 0.26  
        
        self.get_logger().info('SLAM-Optimized Smooth Turn & Randomness Module Activated!')

    def lidar_callback(self, msg):
        cmd_vel_msg = Twist()
        ranges = msg.ranges
        length = len(ranges)
        
        if length == 0:
            return

        one_third = length // 3
        right_beams = ranges[:one_third]
        front_beams = ranges[one_third : 2*one_third]
        left_beams = ranges[2*one_third:]

        def get_clean_closest(beams):
            valid = [x for x in beams if msg.range_min < x < msg.range_max]
            return min(valid) if valid else float('inf')

        closest_right = get_clean_closest(right_beams)
        closest_front = get_clean_closest(front_beams)
        closest_left = get_clean_closest(left_beams)

        if closest_front < self.emergency_distance:
            cmd_vel_msg.linear.x = -0.18  
            

            if abs(closest_right - closest_left) < 0.05:
                cmd_vel_msg.angular.z = random.choice([-0.35, 0.35])
            elif closest_right > closest_left:
                cmd_vel_msg.angular.z = 0.35  
            else:
                cmd_vel_msg.angular.z = -0.35 
                
            self.get_logger().error('Stuck! Executing FAST smooth reverse maneuver.')

        elif closest_front < self.critical_distance:
            cmd_vel_msg.linear.x = 0.0 
            if abs(closest_right - closest_left) < 0.08:
                cmd_vel_msg.angular.z = random.choice([-self.turn_speed, self.turn_speed])
                self.get_logger().warn('Symmetric wall! Choosing RANDOM DIRECTION.')
            elif closest_right > closest_left:
                cmd_vel_msg.angular.z = -self.turn_speed
                self.get_logger().warn('Wall ahead! Turning SMOOTH RIGHT.')
            else:
                cmd_vel_msg.angular.z = self.turn_speed
                self.get_logger().warn('Wall ahead! Turning SMOOTH LEFT.')

        else:
            if closest_right < 0.24:
                cmd_vel_msg.linear.x = 0.08
                cmd_vel_msg.angular.z = 0.20
                self.get_logger().warn('Too close to RIGHT wall! Nudging left to avoid clipping.')
            elif closest_left < 0.24:
                cmd_vel_msg.linear.x = 0.08
                cmd_vel_msg.angular.z = -0.20
                self.get_logger().warn('Too close to LEFT wall! Nudging right to avoid clipping.')
            else:
                cmd_vel_msg.linear.x = self.target_linear_speed
                cmd_vel_msg.angular.z = 0.0
                self.get_logger().info('Path clear, center-driving...', throttle_duration_sec=3.0)

        self.hiz_pub.publish(cmd_vel_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MazeAutonomousNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.hiz_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
