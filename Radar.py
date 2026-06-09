import serial.tools.list_ports
import time
import subprocess
import sys
import os

# Çalıştırılacak iki ana dosyanın adı
YAZILIM_1 = "Bothatthesametime.py"
YAZILIM_2 = "yapayzeka.py"

def radar_baslat():
    print("PATTES RADAR: Arka planda gizlice dinleniyor...")
    sistem_calisiyor = False
    islem1 = None
    islem2 = None

    while True:
        # USB portlarını tara
        portlar = serial.tools.list_ports.comports()
        esp32_bagli_mi = any("CH340" in p.description or "CP210" in p.description or "UART" in p.description or "USB Serial" in p.description for p in portlar)

        # Eğer PATTES takıldıysa ve sistemler henüz çalışmıyorsa
        if esp32_bagli_mi and not sistem_calisiyor:
            print("\nPATTES TAKILDI! İki yazılım da aynı anda ateşleniyor...")
            
            # İki Python dosyasını da birbirini beklemeden aynı anda başlatır
            islem1 = subprocess.Popen([sys.executable, YAZILIM_1])
            islem2 = subprocess.Popen([sys.executable, YAZILIM_2])
            
            sistem_calisiyor = True

        # Eğer PATTES çıkarıldıysa
        elif not esp32_bagli_mi and sistem_calisiyor:
            print("\nPATTES ÇIKARILDI! Radar beklemeye dönüyor...")
            
            # İsteğe bağlı: Kablo çekildiğinde Python kodlarını da otomatik kapatmak istersen 
            # aşağıdaki iki satırın başındaki '#' işaretini kaldır:
            # if islem1: islem1.terminate() 
            # if islem2: islem2.terminate() 
            
            sistem_calisiyor = False

        time.sleep(2) # CPU'yu yormamak için 2 saniyede bir portları kontrol et

if __name__ == "__main__":
    # Kodun çalıştığı klasörü, dosyanın bulunduğu klasör olarak ayarla
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    radar_baslat()