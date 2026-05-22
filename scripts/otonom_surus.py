#!/usr/bin/env tuple
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math

class OtonomMaviArac(Node):
    def __init__(self):
        super().__init__('otonom_surus_node')
        
        # 1. Hız Göndermek İçin Publisher (Mavi araca yön vereceğiz)
        self.hiz_yayinici = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 2. Konum Okumak İçin Subscriber (Gazebo'dan gelen tekerlek konumunu dinliyoruz)
        self.konum_dinleyici = self.create_subscription(
            Odometry, 
            '/model/vehicle_blue/odometry', 
            self.odometry_callback, 
            10)
            
        # Robotun başlangıç konumunu kilitlemek için değişkenler
        self.baslangic_x = None
        self.baslangic_y = None
        self.hedef_mesafe = 2.0 # Robot tam 2 metre gidip duracak
        
        self.get_logger().info('Otonom Sürüş Düğümü Başlatıldı! Hedef: 2 Metre İleri Gitmek.')

    def odometry_callback(self, msg):
        # Robotun anlık X ve Y koordinatları
        anlik_x = msg.pose.pose.position.x
        anlik_y = msg.pose.pose.position.y
        
        # Eğer simülasyon yeni başladıysa ilk konumu kaydet
        if self.baslangic_x is None:
            self.baslangic_x = anlik_x
            self.baslangic_y = anlik_y
            return

        # Öklid bağıntısı ile başlangıçtan itibaren ne kadar yol gittiğimizi hesaplıyoruz
        gidilen_yol = math.sqrt((anlik_x - self.baslangic_x)**2 + (anlik_y - self.baslangic_y)**2)
        
        hiz_komutu = Twist()

        if gidilen_yol < self.hedef_mesafe:
            # Hedefe henüz ulaşılmadıysa ileri gitmeye devam et
            hiz_komutu.linear.x = 0.3 # 0.3 m/s hız
            hiz_komutu.angular.z = 0.0
            self.get_logger().info(f'Robot ilerliyor... Gidilen Yol: {gidilen_yol:.2f} metre')
        else:
            # 2 metre dolduysa Zınk diye dur!
            hiz_komutu.linear.x = 0.0
            hiz_komutu.angular.z = 0.0
            self.get_logger().info('HEDEFE ULAŞILDI! Robot güvenli bir şekilde durduruldu.')

        # Hesaplanan hızı robota gönder
        self.hiz_yayinici.publish(hiz_komutu)

def main(args=None):
    rclpy.init(args=args)
    node = OtonomMaviArac()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
