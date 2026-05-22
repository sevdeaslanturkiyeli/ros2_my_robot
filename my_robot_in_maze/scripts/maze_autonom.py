#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class LabirentOtonomNode(Node):
    def __init__(self):
        super().__init__('labirent_otonom_node')
        
        self.lidar_sub = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.hiz_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.kritik_on_mesafe = 0.42  
        self.get_logger().info('Labirent Kaşifi Aktif!')

    def lidar_callback(self, msg):
        cmd_vel_msg = Twist()
        ranges = msg.ranges
        uzunluk = len(ranges)
        
        if uzunluk == 0:
            return

        uc_te_biri = uzunluk // 3
        sag_isinlar = ranges[:uc_te_biri]
        on_isinlar = ranges[uc_te_biri : 2*uc_te_biri]
        sol_isinlar = ranges[2*uc_te_biri:]

        def temiz_en_yakin_bul(isinlar):
            gecerli = [x for x in isinlar if msg.range_min < x < msg.range_max]
            return min(gecerli) if gecerli else float('inf')

        en_yakin_sag = temiz_en_yakin_bul(sag_isinlar)
        en_yakin_on = temiz_en_yakin_bul(on_isinlar)
        en_yakin_sol = temiz_en_yakin_bul(sol_isinlar)

        if en_yakin_on > self.kritik_on_mesafe:
            cmd_vel_msg.linear.x = 0.12    
            cmd_vel_msg.angular.z = 0.0    
            self.get_logger().info('Koridor açık, ilerliyorum...', throttle_duration_sec=2.0)
            
        else:
            if en_yakin_on < 0.28:
                cmd_vel_msg.linear.x = -0.10   
                if en_yakin_sag > en_yakin_sol:
                    cmd_vel_msg.angular.z = 0.4   
                else:
                    cmd_vel_msg.angular.z = -0.4
                self.get_logger().error(f'KÖŞEYE SIKIŞTIM! Geri vites yapılıyor... (Ön: {en_yakin_on:.2f}m)')
            
            else:
                cmd_vel_msg.linear.x = 0.02   
                if en_yakin_sag > en_yakin_sol:
                    cmd_vel_msg.angular.z = -0.6  
                    self.get_logger().warn('Önde duvar var, sağa sapıyorum.')
                else:
                    cmd_vel_msg.angular.z = 0.6   
                    self.get_logger().warn('Önde duvar var, sola sapıyorum.')

        self.hiz_pub.publish(cmd_vel_msg)

def main(args=None):
    rclpy.init(args=args)
    node = LabirentOtonomNode()
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
