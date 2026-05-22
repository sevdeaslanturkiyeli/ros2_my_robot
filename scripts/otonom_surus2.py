#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_srvs.srv import Trigger
import math

class AkilliMaviArac(Node):
    def __init__(self):
        super().__init__('akilli_surus_node')
        
        # 1. Topic Publisher & Subscriber
        self.hiz_yayinici = self.create_publisher(Twist, '/cmd_vel', 10)
        self.konum_dinleyici = self.create_subscription(
            Odometry, 
            '/model/vehicle_blue/odometry', 
            self.odometry_callback, 
            10)
        
        # 2. Service Server
        self.servis_sunucusu = self.create_service(
            Trigger, 
            '/baslangica_don', 
            self.geri_don_callback)
            
        # Durum Değişkenleri
        self.baslangic_x = None
        self.baslangic_y = None
        self.anlik_x = 0.0
        self.anlik_y = 0.0
        
        self.hedef_mesafe = 2.0
        self.geri_donus_modu = False
        self.gorev_bitti = False  # YENİ: Robotun tamamen durmasını sağlayacak kilit
        
        self.get_logger().info('Akıllı Sürüş ve Servis Düğümü Başlatıldı!')

    def odometry_callback(self, msg):
        self.anlik_x = msg.pose.pose.position.x
        self.anlik_y = msg.pose.pose.position.y
        
        if self.baslangic_x is None:
            self.baslangic_x = self.anlik_x
            self.baslangic_y = self.anlik_y
            return

        hiz_komutu = Twist()

        # MOD 0: TÜM GÖREVLER BİTTİ, PARKA ÇEKİLDİ
        if self.gorev_bitti:
            hiz_komutu.linear.x = 0.0
            hiz_komutu.angular.z = 0.0
            self.hiz_yayinici.publish(hiz_komutu)
            return

        # MOD 1: İLERİ GİTME MODU
        if not self.geri_donus_modu:
            gidilen_yol = math.sqrt((self.anlik_x - self.baslangic_x)**2 + (self.anlik_y - self.baslangic_y)**2)
            
            if self.check_tolerance(gidilen_yol, self.hedef_mesafe):
                hiz_komutu.linear.x = 0.3
                self.get_logger().info(f'İleri gidiyor... Mesafe: {gidilen_yol:.2f} m', throttle_duration_sec=1.0)
            else:
                hiz_komutu.linear.x = 0.0
                self.get_logger().info('2 Metre tamamlandı. Servis isteği bekleniyor...', throttle_duration_sec=2.0)
        
        # MOD 2: GERİ DÖNME MODU
        else:
            baslangica_kalan_mesafe = math.sqrt((self.anlik_x - self.baslangic_x)**2 + (self.anlik_y - self.baslangic_y)**2)
            
            if baslangica_kalan_mesafe > 0.05:
                hiz_komutu.linear.x = -0.3
                self.get_logger().info(f'Geri dönüyor... Başlangıca kalan: {baslangica_kalan_mesafe:.2f} m', throttle_duration_sec=1.0)
            else:
                hiz_komutu.linear.x = 0.0
                self.geri_donus_modu = False
                self.gorev_bitti = True  # YENİ: Geri dönünce kilidi kapat, sistem dursun!
                self.get_logger().info('BAŞLANGIÇ NOKTASINA DÖNÜLDÜ VE PARK EDİLDİ!')

        self.hiz_yayinici.publish(hiz_komutu)

    def check_tolerance(self, current, target):
        return current < target

    def geri_don_callback(self, request, response):
        self.get_logger().warn('Başlangıca dön servis isteği alındı! Robot geri çağrılıyor...')
        self.geri_donus_modu = True
        self.gorev_bitti = False  # Servis gelirse kilidi açıyoruz
        response.success = True
        response.message = "Robot otonom olarak başlangıç noktasına geri döndürülüyor."
        return response

def main(args=None):
    rclpy.init(args=args)
    node = AkilliMaviArac()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
