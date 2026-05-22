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
        

        self.kritik_on_mesafe = 0.45  
        self.sikisma_mesafesi = 0.35  
        
        self.get_logger().info('Labirent Kaşifi Aktif! Direksiyon Mikro Robotta...')

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


        if en_yakin_on < self.sikisma_mesafesi and en_yakin_sag < self.sikisma_mesafesi and en_yakin_sol < self.sikisma_mesafesi:
            cmd_vel_msg.linear.x = -0.08   
            cmd_vel_msg.angular.z = 0.4    
            
            self.get_logger().error('ÇIKMAZ SOKAK! Geri vitesle kurtarma manevrası yapılıyor...')


        elif en_yakin_on > self.kritik_on_mesafe:
            cmd_vel_msg.linear.x = 0.12    
            cmd_vel_msg.angular.z = 0.0    
            self.get_logger().info('Koridor temiz, ilerliyorum...', throttle_duration_sec=2.0)
            

        else:
            cmd_vel_msg.linear.x = 0.02    
            
            if en_yakin_sag > en_yakin_sol:
                cmd_vel_msg.angular.z = -0.6  # Sağ taraf daha geniş, sağa keskin dön
                self.get_logger().warn(f'Önde Duvar Var! Sağ koridora sapıyorum (Sağ: {en_yakin_sag:.2f}m)')
            else:
                cmd_vel_msg.angular.z = 0.6   # Sol taraf daha geniş, sola keskin dön
                self.get_logger().warn(f'Önde Duvar Var! Sol koridora sapıyorum (Sol: {en_yakin_sol:.2f}m)')

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
