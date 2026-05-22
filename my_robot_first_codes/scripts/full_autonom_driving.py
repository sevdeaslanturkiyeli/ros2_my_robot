#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class OtonomSurusNode(Node):
    def __init__(self):
        super().__init__('otonom_surus_node')
        
        # LIDAR konusunu dinliyoruz
        self.lidar_dinleyici = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        
        # Robota doğrudan hız yönlendirmesi yapıyoruz
        self.hiz_yayinici = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Kontrol parametreleri
        self.kritik_mesafe = 1.2  # Kaçış manevrasına başlama mesafesi (metre)
        
        self.get_logger().info('Tam Otonom Engelden Kaçma Modülü Aktif! Direksiyon Robotta...')

    def lidar_callback(self, msg):
        cmd_vel_msg = Twist()
        
        # LIDAR ışın dizisini alıyoruz
        ranges = msg.ranges
        uzunluk = len(ranges)
        
        if uzunluk == 0:
            return

        # Işın dizisini 3 ana sektöre bölüyoruz (Sağ, Merkez/Ön, Sol)
        # Örnek: 640 ışın varsa; ~213 sağ, ~213 ön, ~214 sol
        uc_te_biri = uzunluk // 3
        
        sag_isinlar = ranges[:uc_te_biri]
        on_isinlar = ranges[uc_te_biri : 2*uc_te_biri]
        sol_isinlar = ranges[2*uc_te_biri:]

        # Geçersiz (.inf veya 0.0) değerleri temizleyip sektörlerin en yakın engellerini buluyoruz
        def en_yakin_bul(isinlar):
            gecerli = [x for x in isinlar if x > msg.range_min and x < msg.range_max]
            return min(gecerli) if gecerli else float('inf')

        en_yakin_sag = en_yakin_bul(sag_isinlar)
        en_yakin_on = en_yakin_bul(on_isinlar)
        en_yakin_sol = en_yakin_bul(sol_isinlar)

        # --- OTONOM KARAR MEKANİZMASI ---
        
        # Durum 1: Önümüz tamamen temiz, bas gaza!
        if en_yakin_on > self.kritik_mesafe:
            cmd_vel_msg.linear.x = 0.15   # Güvenli ileri hız
            cmd_vel_msg.angular.z = 0.0   # Düz git
            self.get_logger().info('Önüm temiz, otonom ilerliyorum...', throttle_duration_sec=2.0)
            
        # Durum 2: Önümüzde engel var! Kaçış manevrası başlasın
        else:
            cmd_vel_msg.linear.x = 0.02   # Çarpmamak için hızı iyice düşür
            
            # Sağ taraf sol taraftan daha boşsa -> Sağa dön
            if en_yakin_sag > en_yakin_sol:
                cmd_vel_msg.angular.z = -0.5  # ROS 2'de eksi açısal hız SAĞA dönüştür
                self.get_logger().warn(f'Engel algılandı! Sağ taraf daha boş ({en_yakin_sag:.2f}m). Sağa kaçıyorum!')
            
            # Sol taraf sağ taraftan daha boşsa veya eşitse -> Sola dön
            else:
                cmd_vel_msg.angular.z = 0.5   # Artı açısal hız SOLA dönüştür
                self.get_logger().warn(f'Engel algılandı! Sol taraf daha boş ({en_yakin_sol:.2f}m). Sola kaçıyorum!')

        # Karar verilen otonom hızı robota gönder
        self.hiz_yayinici.publish(cmd_vel_msg)

def main(args=None):
    rclpy.init(args=args)
    node = OtonomSurusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Kapatırken robotu durdurma komutu gönder
        durma_hizi = Twist()
        node.hiz_yayinici.publish(durma_hizi)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
