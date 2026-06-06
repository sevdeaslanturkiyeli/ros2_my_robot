#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import math
import time
import random

class WarehouseWanderer(Node):
    def __init__(self):
        super().__init__('warehouse_wanderer')
        
        self.lidar_sub = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.hiz_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Hız ve mesafe limitleri
        self.max_linear = 0.14         
        self.max_angular = 0.45        
        
        # Durum yönetimleri
        self.is_reversing = False
        self.reverse_start_time = 0.0
        self.chosen_escape_turn = 0.0
        
        # Rutin kırmayı sağlayan zamanlayıcı
        self.last_direction_change = time.time()
        self.random_turn_duration = 0.0
        self.is_doing_random_turn = False
        
        self.get_logger().info('Dinamik Gezgin Aktif!')

    def lidar_callback(self, msg):
        cmd_vel_msg = Twist()
        ranges = msg.ranges
        length = len(ranges)
        
        if length == 0:
            return

        current_time = time.time()

        # SIKIŞMA / GERİ KAÇIŞ MANEVRASI 
        if self.is_reversing:
            if current_time - self.reverse_start_time < 0.8:
                cmd_vel_msg.linear.x = -0.14
                cmd_vel_msg.angular.z = self.chosen_escape_turn
                self.hiz_pub.publish(cmd_vel_msg)
                return
            else:
                self.is_reversing = False
                self.last_direction_change = current_time # Zamanlayıcıyı sıfırla

        # Lidar Sektörleri
        front_beams = ranges[0:int(length*0.06)] + ranges[int(length*0.94):length]
        right_beams = ranges[int(length*0.10):int(length*0.28)]
        left_beams = ranges[int(length*0.72):int(length*0.90)]

        def get_min_dist(beams):
            valid = [x for x in beams if msg.range_min < x < msg.range_max and not math.isnan(x) and not math.isinf(x)]
            return min(valid) if valid else 5.0

        f_dist = get_min_dist(front_beams)
        r_dist = get_min_dist(right_beams)
        l_dist = get_min_dist(left_beams)

        # ACİL DUVAR KORUMASI 
        if f_dist < 0.38 or r_dist < 0.22 or l_dist < 0.22:
            self.is_reversing = True
            self.is_doing_random_turn = False
            self.reverse_start_time = current_time
            self.chosen_escape_turn = self.max_angular if r_dist < l_dist else -self.max_angular
            
            cmd_vel_msg.linear.x = -0.14
            cmd_vel_msg.angular.z = self.chosen_escape_turn
            self.hiz_pub.publish(cmd_vel_msg)
            return

        # ZAMAN AYARLI RASTGELE KORİDOR DEĞİŞTİRME ----
        # Eğer robot 7 saniyedir dümdüz gidiyorsa, bir koridora hapsolmuş veya daire çiziyor olabilir.
        # Açık alanda rastgele 1 saniye boyunca sağa veya sola keskin kırarak yeni koridorlara dalmasını sağlıyoruz.
        if not self.is_doing_random_turn and (current_time - self.last_direction_change > 7.0):
            self.is_doing_random_turn = True
            self.random_turn_duration = current_time
            self.chosen_escape_turn = random.choice([-self.max_angular, self.max_angular])
            self.get_logger().info('Rastgele yeni bir yöne sapıyorum!')

        if self.is_doing_random_turn:
            if current_time - self.random_turn_duration < 1.0:
                cmd_vel_msg.linear.x = 0.06 # Yavaşça dön
                cmd_vel_msg.angular.z = self.chosen_escape_turn
                self.hiz_pub.publish(cmd_vel_msg)
                return
            else:
                self.is_doing_random_turn = False
                self.last_direction_change = current_time

        # STANDART KORİDOR SÜRÜŞÜ MANTIĞI ----
        if f_dist < 0.85:
            # Önü kapandıysa en açık tarafa keskin dön
            cmd_vel_msg.linear.x = 0.02
            cmd_vel_msg.angular.z = -self.max_angular if r_dist > l_dist else self.max_angular
        else:
            # Önü temizse güvenle ilerle, sağ ve sol dengesine göre hafif koridoru ortala
            cmd_vel_msg.linear.x = self.max_linear
            # Sağ ve sol yakınlık farkından yumuşak bir sapma üret (Daire çizmesini tamamen engeller)
            side_diff = r_dist - l_dist
            cmd_vel_msg.angular.z = max(min(side_diff * 0.15, 0.2), -0.2)

        self.hiz_pub.publish(cmd_vel_msg)

def main(args=None):
    rclpy.init(args=args)
    node = WarehouseWanderer()
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
