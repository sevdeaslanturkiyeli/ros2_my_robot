#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import math
import time
import random

class VectorFieldNavigator(Node):
    def __init__(self):
        super().__init__('vector_field_navigator')
        
        self.lidar_sub = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.hiz_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Robotun yapısal sınırları ve hızları
        self.safe_radius = 0.34        
        self.max_linear = 0.12         
        self.max_angular = 0.45        
        
        
        self.is_reversing = False
        self.reverse_start_time = 0.0
        self.chosen_escape_turn = 0.35  # Kurtulma esnasında dönülecek yön hızı
        
        self.get_logger().info('Durum Tabanlı 360° Vektörel Sürüş Modülü Aktif!')

    def lidar_callback(self, msg):
        cmd_vel_msg = Twist()
        ranges = msg.ranges
        length = len(ranges)
        
        if length == 0:
            return

        current_time = time.time()

        # ---- DURUM 1: GERİ VİTES KİLİT KIRMA DURUMU ----
        # Robot bir kez sıkışma durumuna girdiyse, 1.3 saniye boyunca Lidar vektörlerini 
        # dinlemeyi askıya alıp sadece tam güçle geri gelmeli ve yönünü değiştirmeli!
        if self.is_reversing:
            if current_time - self.reverse_start_time < 1.3:
                cmd_vel_msg.linear.x = -0.14          # Güçlü geri vites
                cmd_vel_msg.angular.z = self.chosen_escape_turn  # Keskin kaçış dönüşü
                self.hiz_pub.publish(cmd_vel_msg)
                return
            else:
                # Süre bitti, normal sürüşe geri dön
                self.is_reversing = False
                self.get_logger().info('Geri vites manevrası tamamlandı. Normal sürüşe dönülüyor.')

        # Vektörel kaçış toplamları
        force_x = 0.0
        force_y = 0.0
        obstacle_detected = False
        min_distance = float('inf')

        # 360 derecelik Lidar analizi
        for i in range(length):
            dist = ranges[i]
            if math.isnan(dist) or math.isinf(dist) or dist < msg.range_min or dist > msg.range_max:
                continue
                
            if dist < min_distance:
                min_distance = dist

            if dist < self.safe_radius:
                obstacle_detected = True
                angle = msg.angle_min + (i * msg.angle_increment)
                weight = (self.safe_radius - dist) / self.safe_radius
                
                # Zıt yön vektörleri
                force_x -= math.cos(angle) * weight
                force_y -= math.sin(angle) * weight

        # ---- DURUM 2: ENGEL SEZİLME VE TETİKLENME ANI ----
        if obstacle_detected:
            # Karşılıklı kuvvetler birbirini sıfırladıysa veya robot dar bir koridora girdiyse
            # Anlık titremeyi kesmek için GERİ VİTES DURUMUNU tetikle!
            self.is_reversing = True
            self.reverse_start_time = current_time
            
            # Dönüş yönünü rastgele veya Y ekseni kuvvetinin baskınlığına göre seç
            if abs(force_y) < 0.05:
                # Tam dengeli sıkışmaysa şansına bir yöne kaç
                self.chosen_escape_turn = random.choice([-self.max_angular, self.max_angular])
            elif force_y > 0:
                self.chosen_escape_turn = self.max_angular   # Sola keskin kır
            else:
                self.chosen_escape_turn = -self.max_angular  # Sağa keskin kır
                
            self.get_logger().error(f'🚨 DAR ALAN SIKIŞMASI! {min_distance:.2f}m mesafeden 1.3 saniye geri kaçış başlatıldı!')
            
            # İlk emri hemen gönder
            cmd_vel_msg.linear.x = -0.14
            cmd_vel_msg.angular.z = self.chosen_escape_turn
        
        # ---- DURUM 3: YOL TEMİZ ----
        else:
            cmd_vel_msg.linear.x = self.max_linear
            cmd_vel_msg.angular.z = 0.0

        self.hiz_pub.publish(cmd_vel_msg)

def main(args=None):
    rclpy.init(args=args)
    node = VectorFieldNavigator()
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
