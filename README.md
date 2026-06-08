# PATTES 🥔 - Masaüstü Çalışma Asistanı

PATTES, öğrencilerin ders çalışırken odaklarını artırmayı, sağlıklı bir oturuş pozisyonu kazanmalarını ve en büyük dikkat dağıtıcı olan telefondan uzaklaşmalarını sağlayan yapay zeka destekli, interaktif bir masaüstü asistan robotudur.

## 🌟 Temel Özellikler

### 🗣️ Sesli Yapay Zeka Asistanı ("Hey Pattes")
Sürekli dinleme yaparak gereksiz kaynak tüketiminin ve API çağrılarının önüne geçmek için sistem bir uyandırma kelimesiyle çalışır. Robota **"Hey Pattes"** dediğinizde yapay zeka aktifleşir, sorunuzu veya isteğinizi dinler ve size sesli olarak yanıt verir.

### 🧘‍♀️ Postür ve Odak Takibi
Kamera aracılığıyla kullanıcının oturuşunu ve odağını analiz eder. Kullanıcı ders çalışırken yamuk oturursa veya odağı dersten/ekrandan başka bir yere kayarsa, PATTES duruşunu düzeltmesi için kullanıcıyı uyarır.

### 📱 Telefonsuz "Ders Çalışma" Modu
PATTES ile çalışmaya başlamanın ilk kuralı telefondan uzaklaşmaktır. Robotun sol tarafında entegre bir hassas teraziye sahip telefon standı bulunur. Sistemin ders çalışma moduna geçebilmesi ve menülerin açılabilmesi için telefonun bu standa yerleştirilmesi zorunludur.

### ⏱️ Özelleştirilebilir Zamanlayıcılar ve Modlar
Telefon standa yerleştirildikten sonra çalışma ortamına göre **Ekran** veya **Kitap** modu seçilir. Bu ana modların altında farklı çalışma rutinlerine uygun zamanlayıcılar bulunur:
* **Hazır Modlar:** Ders (40 dk), TYT (165 dk), AYT, Tekrar, Test, Mola, Pomodoro.
* **Manuel Mod:** Kullanıcı dokunmatik sensör (Touch Sensor) ile kendi süresini belirleyebilir. 
    * Sensöre her dokunuş süreyi **5 dakika** artırır.
    * Sensöre **3 saniye basılı tutulduğunda** ekrandaki süre onaylanır ve geri sayım başlar.

### 💡 Görsel Geri Bildirim (Adreslenebilir LED)
Robotun durumu, üzerinde bulunan adreslenebilir LED'ler ile kullanıcıya anlık olarak yansıtılır. (Örn: Uyarı durumlarında kırmızı, mola zamanlarında sarı, ekran modunda mavi vb.)

## 🛠️ Kullanılan Teknolojiler ve Donanımlar

* **Yazılım:** Python (Yapay zeka, görüntü işleme ve postür analizi), Arduino C/C++
* **Donanım Bileşenleri:**
    * ESP32 S
    * Hassas Terazi (Telefon algılama)
    * Oled Ekran
    * Dokunmatik Sensör (Manuel zamanlayıcı kontrolü)
    * Buzzer (Uyarı verici)
    * Adreslenebilir LED (Durum bildirimleri)
    * Hoparlör ve Amfi (Sesli iletişim) (Mikrofon olarak pc mikrofonu kullanılmıştır.)

## 🚀 Nasıl Çalışır?

1.  Telefonunuzu robotun sol tarafındaki akıllı standa yerleştirin.
2.  Aktifleşen menüden çalışma türünüze göre **Ekran** veya **Kitap** modunu seçin.
3.  İhtiyacınıza uygun zamanlayıcıyı (Örn: TYT, Pomodoro) veya Manuel modu ayarlayarak süreyi başlatın.
4.  Çalışmanız sırasında dikkatiniz dağılırsa veya duruşunuz bozulursa Pattes'in uyarılarını dikkate alın.
5.  Bir soru sormak istediğinizde "Hey Pattes" diyerek asistanınızdan sesli yardım alın.

## 🔌 Devre Şeması ve Pin Bağlantıları

Projenin donanım bileşenlerinin ESP32 üzerindeki bağlantı şeması, pin detayları ve görevleri aşağıda belirtilmiştir. 

> ⚠️ **Önemli Not:** Sağlıklı bir iletişim ve güç dağıtımı için tabloda belirtilen tüm modüllerin toprak (GND) hatları "Ortak GND" noktasında birleştirilmelidir.

### 📊 Pin Bağlantı Tablosu

| Bileşen (Modül) | Modül Pini | ESP32 Pini / Güç Kaynağı | Görev Türü |
| :--- | :--- | :--- | :--- |
| **OLED Ekran (SPI)** | GND | Ortak GND | Toprak |
| | VCC | 3.3V | Güç |
| | SCK (D0) | 18 | SPI Saat Sinyali |
| | SDA (D1) | 23 | SPI Veri (MOSI) |
| | RES | 14 | Ekran Reset |
| | DC | 27 | Veri/Komut Seçimi |
| | CS | 5 | Çip Seçimi |
| **Aktif Buzzer** | GND | Ortak GND | Toprak |
| | VCC | 3.3V | Güç |
| | IO | 32 | Dijital Tetikleyici |
| **I2S Dijital Amfi** | GND | Ortak GND | Toprak |
| | VIN | 5V | Ana Güç |
| | GAIN | 5V | Kazanç (Yüksek Ses) |
| | LRC | 25 | I2S Sol/Sağ Saat |
| | BLCK | 26 | I2S Bit Saati |
| | DIN | 22 | I2S Veri Girişi |
| **Hoparlör** | (+ / -) | Amfi Çıkışlarına | Ses Çıkışı |
| **Adreslenebilir LED** | GND | Ortak GND | Toprak |
| | 5V | 5V | Güç |
| | DIN | 33 | Veri Sinyali |
| **HX711 (Loadcell)** | GND | Ortak GND | Toprak |
| | VCC | 3.3V | Güç |
| | SCK | 16 | Saat Sinyali |
| | DT | 4 | Veri Sinyali |
| **Touch Pad** | GND | Ortak GND | Toprak |
| | VCC | 3.3V | Güç |
| | IO | 2 | Dokunma Sinyali |

### 🗺️ Devre Şeması Görseli

### 🧠 Sistem Mimarisi ve Veri Akışı

PATTES'in bilgisayar/yapay zeka (OS) katmanı ile donanım katmanı arasındaki iletişim protokolleri ve veri akış yönleri aşağıdaki şemada gösterilmiştir:

```text
         +-------------------------+
         |    PATTES OS (PC/YAI)   |
         +-------------------------+
                      |
         Seri Port (UART - 115200 Baud)
                      |
                      v
+---------------------------------------------------+
|                     ESP32 MCU                     |
+---------------------------------------------------+
   |         |         |         |         |         |
  SPI       I2S       PWM     Digital   Digital    HX711
Bus (O)   Bus (O)   Bus (O)   In (I)    Out (O)  Bus (I/O)
   |         |         |         |         |         |
   v         v         v         v         v         v
+------+  +------+  +-------+ +-------+ +-------+ +-------+
| OLED |  | I2S  |  | Aktif | | Touch | | Adres.| | HX711 |
| Ekran|  | Amfi |  | Buzzer| |  Pad  | |  LED  | | Modülü|
+------+  +------+  +-------+ +-------+ +-------+ +-------+
             |                                       |
           Analog                                  Analog
             |                                       |
             v                                       v
         +--------+                              +-------+
         |Hoparlör|                              | Yük   |
         +--------+                              |Hücresi|
                                                 +-------+
