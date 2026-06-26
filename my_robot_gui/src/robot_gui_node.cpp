#include <QApplication>
#include <QWidget>
#include <QPushButton>
#include <QLabel>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QImage>
#include <QPixmap>
#include <thread>
#include <mutex>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "sensor_msgs/msg/image.hpp"
#include "cv_bridge/cv_bridge.h"
#include "opencv2/opencv.hpp"

// -------------------------------------------------------------------
// 1. ROS 2 DÜĞÜM SINIFIMIZ (Ağ İletişimi ve Sensör Dinleme)
// -------------------------------------------------------------------
class RobotGuiBackend : public rclcpp::Node {
public:
    // Dışarıdan bir fonksiyon (callback) alarak yeni kamera görüntüsü geldiğinde Qt'ye haber vereceğiz
    RobotGuiBackend(std::function<void(const cv::Mat&)> image_callback) 
    : Node("robot_gui_backend"), image_received_callback_(image_callback) 
    {
        // Hız komut publisher'ı
        cmd_vel_pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);

        // Kamera görüntüsünü dinleyen subscriber
        image_sub_ = this->create_subscription<sensor_msgs::msg::Image>(
            "/camera/image_raw", 10, 
            std::bind(&RobotGuiBackend::image_callback, this, std::placeholders::_1)
        );
    }

    // Robotu hareket ettirecek fonksiyon
    void move_robot(double linear_x, double angular_z) {
        auto msg = geometry_msgs::msg::Twist();
        msg.linear.x = linear_x;
        msg.angular.z = angular_z;
        cmd_vel_pub_->publish(msg);
    }

private:
    void image_callback(const sensor_msgs::msg::Image::SharedPtr msg) {
        try {
            // ROS Image mesajını OpenCV Matrisine (BGR8 formatında) çeviriyoruz
            cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg, sensor_msgs::image_encodings::BGR8);
            if (!cv_ptr->image.empty() && image_received_callback_) {
                image_received_callback_(cv_ptr->image);
            }
        } catch (cv_bridge::Exception& e) {
            RCLCPP_ERROR(this->get_logger(), "cv_bridge hatası: %s", e.what());
        }
    }

    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
    std::function<void(const cv::Mat&)> image_received_callback_;
};

// -------------------------------------------------------------------
// 2. ANA FONKSİYON (MAIN) - UI Yerleşimi ve Döngüler
// -------------------------------------------------------------------
int main(int argc, char *argv[]) {
    // ROS 2 Başlatılıyor
    rclcpp::init(argc, argv);

    // Qt Dünyası Başlatılıyor
    QApplication app(argc, argv);

    // Ana Pencere Ayarları
    QWidget window;
    window.setWindowTitle("Savunma Sanayii Robot Kontrol Merkezi");
    window.resize(800, 450);

    // Düzenleyiciler (Layouts)
    QHBoxLayout *main_layout = new QHBoxLayout(&window); // Yan yana bölmeler
    QVBoxLayout *control_layout = new QVBoxLayout();     // Üst üste butonlar

    // UI Elemanları
    QLabel *camera_label = new QLabel(&window);
    camera_label->setText("Kamera Akışı Bekleniyor...");
    camera_label->setAlignment(Qt::AlignCenter);
    camera_label->setStyleSheet("border: 2px solid gray; background-color: black; color: white;");
    camera_label->setFixedSize(540, 400); // 16:9 oranına yakın şık bir ekran

    QPushButton *btn_forward = new QPushButton("▲ İLERİ", &window);
    QPushButton *btn_left    = new QPushButton("◀ SOLA DÖN", &window);
    QPushButton *btn_right   = new QPushButton("SAĞA DÖN ▶", &window);
    QPushButton *btn_backward = new QPushButton("▼ GERİ", &window);
    QPushButton *btn_stop     = new QPushButton("🛑 DUR", &window);

    // Butonları sağdaki kontrol paneline diziyoruz
    control_layout->addWidget(btn_forward);
    control_layout->addWidget(btn_left);
    control_layout->addWidget(btn_right);
    control_layout->addWidget(btn_backward);
    control_layout->addWidget(btn_stop);

    // Sol tarafa kamera ekranını, sağ tarafa butonları yerleştiriyoruz
    main_layout->addWidget(camera_label);
    main_layout->addLayout(control_layout);

    std::mutex img_mutex;

    // ROS 2 Arka Plan Sınıfını Tetikliyoruz (Kamera görüntüsü gelince burası çalışacak)
    auto ros_node = std::make_shared<RobotGuiBackend>([&](const cv::Mat& frame) {
        std::lock_guard<std::mutex> lock(img_mutex);
        
        // OpenCV (BGR) formatını Qt (RGB) formatına dönüştürüyoruz
        cv::Mat rgb_frame;
        cv::cvtColor(frame, rgb_frame, cv::COLOR_BGR2RGB);
        
        QImage q_img(rgb_frame.data, rgb_frame.cols, rgb_frame.rows, rgb_frame.step, QImage::Format_RGB888);
        
        // Görüntüyü arayüz kutusuna sığacak şekilde ölçekleyip ekrana basıyoruz
        camera_label->setPixmap(QPixmap::fromImage(q_img).scaled(camera_label->width(), camera_label->height(), Qt::KeepAspectRatio));
    });

    // SİHİRLİ DOKUNUŞ: ROS 2'yi Qt'den bağımsız bir thread'de spin ettiriyoruz
    std::thread ros_thread([ros_node]() {
        rclcpp::spin(ros_node);
    });

    // Butonların Sinyal-Slot Bağlantıları (Butona basıldığında arka plandaki ROS düğümü tetiklenir)
    QObject::connect(btn_forward, &QPushButton::clicked, [&]() { ros_node->move_robot(0.3, 0.0); });
    QObject::connect(btn_backward, &QPushButton::clicked, [&]() { ros_node->move_robot(-0.3, 0.0); });
    QObject::connect(btn_left, &QPushButton::clicked, [&]() { ros_node->move_robot(0.0, 0.5); });
    QObject::connect(btn_right, &QPushButton::clicked, [&]() { ros_node->move_robot(0.0, -0.5); });
    QObject::connect(btn_stop, &QPushButton::clicked, [&]() { ros_node->move_robot(0.0, 0.0); });

    // Arayüzü göster
    window.show();

    // Qt Döngüsü başlar (Pencere açık olduğu sürece program burada döner)
    int qt_ret = app.exec();

    // Program kapatıldığında thread'leri güvenli bir şekilde bitiriyoruz
    rclcpp::shutdown();
    if (ros_thread.joinable()) {
        ros_thread.join();
    }

    return qt_ret;
}
