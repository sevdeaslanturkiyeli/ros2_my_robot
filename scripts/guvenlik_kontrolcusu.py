#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class GuvenlikKontrolcusu(Node):
    def __init__(self):
        super().__init__('guvenlik_kontrol_node')
        
        # 1. Konuları Dinliyoruz (Subscribers)
        self.lidar_dinleyici = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.klavye_dinleyici = self.create_subscription(Twist, '/cmd_vel_manuel', self.klavye_callback, 10)
        
        # 2. Gerçek Robota Hız Basacak Konu (Publisher)
        self.hiz_yayinici = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Kritik Mesafe Sınırı (1 metre)
        self.kritik_mesafe = 1.0
        self.en_yakin_mesafe = float('inf')
        
        self.get_logger().info('Güvenlik Kontrol Düğümü Aktif! Gözümüz LIDAR verilerinde...')

    def lidar_callback(self, msg):
        # LIDAR'dan gelen tüm ışın dizisini alıyoruz
        isatli_mesafeler = msg.ranges
        
        # 0.0 (hata/yakın temas) ve .inf (sonsuzluk) değerlerini filtreleyip en yakın engeli buluyoruz
        gecerli_mesafeler = [x for x in isatli_mesafeler if x > msg.range_min and x < msg.range_max]
        
        if gecerli_mesafeler:
            self.en_yakin_mesafe = min(gecerli_mesafeler)
        else:
            self.en_yakin_mesafe = float('inf')

    def klavye_callback(self, msg):
        guvenli_hiz = Twist()
        
        # Eğer önümüzde engel çok yakınsa (1 metreden küçükse)
        if self.en_yakin_mesafe < self.kritik_mesafe:
            # Kullanıcı geri vitese taktıysa (linear.x < 0) kaçmasına İZİN VER
            if msg.linear.x < 0:
                guvenli_hiz.linear.x = msg.linear.x
                guvenli_hiz.angular.z = msg.angular.z
                self.get_logger().warn(f'Engel yakın ({self.en_yakin_mesafe:.2f} m) ama geri vitesle kaçışa izin veriliyor.')
            
            # Kullanıcı ileri gitmeye veya olduğu yerde dönmeye çalışıyorsa ENGELLE (Fren yap)
            else:
                self.get_logger().error(f'ACİL DURUM! Çarpışma Riski! Mesafe: {self.en_yakin_mesafe:.2f} m. Tüm ileri ve dönüş hareketleri KİLİTLENDİ!')
                guvenli_hiz.linear.x = 0.0
                guvenli_hiz.angular.z = 0.0
        
        # Önümüz tamamen boşsa klavye komutunu aynen geçir
        else:
            guvenli_hiz.linear.x = msg.linear.x
            guvenli_hiz.angular.z = msg.angular.z

        # Son kararı robota gönder
        self.hiz_yayinici.publish(guvenli_hiz)

def main(args=None):
    rclpy.init(args=args)
    node = GuvenlikKontrolcusu()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
