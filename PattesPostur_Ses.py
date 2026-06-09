import cv2
import mediapipe as mp
import time
from datetime import datetime
import serial
import serial.tools.list_ports
import pyttsx3
import threading
import queue

# ====================================================================
# 0. YEREL SES MOTORU (PC HOPARLÖRÜ)
# ====================================================================
ses_kuyrugu = queue.Queue()

def ses_motoru_isci():
    engine = pyttsx3.init()
    engine.setProperty('rate', 140) 
    
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'tolga' in voice.name.lower() or 'turkish' in voice.name.lower() or 'tr' in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break
            
    while True:
        mesaj = ses_kuyrugu.get()
        if mesaj is None:
            break
            
        global kitap_modu
        # Sadece EKRAN MODUNDAYSAK sesi bilgisayardan çıkar
        if not kitap_modu:
            try:
                engine.say(mesaj)
                engine.runAndWait()
            except Exception as e:
                print(f"Ses Motoru Hatası: {e}")
                
        ses_kuyrugu.task_done()

threading.Thread(target=ses_motoru_isci, daemon=True).start()

# ====================================================================
# 1. OTOMATİK ESP32 RADARI
# ====================================================================
def otomatik_esp32_bul():
    print("Sistem Taraması: PATTES aranıyor...")
    portlar = serial.tools.list_ports.comports()
    for port in portlar:
        if "CH340" in port.description or "CP210" in port.description or "UART" in port.description or "USB Serial" in port.description:
            print(f"Hedef Tespit Edildi! PATTES {port.device} portunda bulundu.")
            return port.device
    print("HATA: PATTES USB portlarında bulunamadı!")
    return None

hedef_port = otomatik_esp32_bul()
esp32_bagli = False

if hedef_port:
    try:
        esp32 = serial.Serial(hedef_port, 115200, timeout=1)
        esp32_bagli = True
        time.sleep(2) 
        print("BAŞARILI: PATTES ile donanımsal iletişim kilitlendi!")
    except Exception as e:
        print(f"Port bulundu ama erişim reddedildi. Hata: {e}")

son_gonderilen_sinyal = "0" 

# ====================================================================
# 2. YAPAY ZEKA MODELLERİ
# ====================================================================
pose_model_path = 'pose_landmarker_lite.task'
face_model_path = 'face_landmarker.task'

BaseOptions = mp.tasks.BaseOptions
VisionRunningMode = mp.tasks.vision.RunningMode

pose_options = mp.tasks.vision.PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=pose_model_path), running_mode=VisionRunningMode.IMAGE)
face_options = mp.tasks.vision.FaceLandmarkerOptions(base_options=BaseOptions(model_asset_path=face_model_path), running_mode=VisionRunningMode.IMAGE, num_faces=1)

# ====================================================================
# 3. DEĞİŞKENLER
# ====================================================================
kalibrasyon_yapildi = False
kitap_modu = False  
ref_omuz_genisligi, ref_dikey_mesafe, ref_yatay_oran, ref_dikey_oran = 0.0, 0.0, 0.0, 0.0
anlik_omuz_genisligi, anlik_dikey_mesafe, anlik_yatay_oran, anlik_dikey_oran = 0.0, 0.0, 0.0, 0.0
insan_goruldu = False

IHLAL_ESIK_SURESI = 5.0  
postur_ihlal_baslangic = None
odak_ihlal_baslangic = None
postur_alarm_verildi = False
odak_alarm_verildi = False

baslangic_zamani = time.time()
istatistikler = {"yakinlasma": 0, "kambur": 0, "kaykilma": 0, "yan_bakis": 0, "asagi_bakis": 0, "yukari_bakis": 0}

frame_sayaci = 0
AI_ISLEM_SIKLIGI = 5  
son_postur_mesaj, son_postur_renk = "BEKLENIYOR...", (0, 255, 255)
son_odak_mesaj, son_odak_renk = "BEKLENIYOR...", (0, 255, 255)

# ====================================================================
# 4. ANA DÖNGÜ VE ÇİFT ÇEKİRDEKLİ İZLEME
# ====================================================================
with mp.tasks.vision.PoseLandmarker.create_from_options(pose_options) as pose_tracker, \
     mp.tasks.vision.FaceLandmarker.create_from_options(face_options) as face_tracker:
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    ses_kuyrugu.put("PATTES sistemi başlatıldı. Lütfen kalibrasyon için C tuşuna basın.")
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        frame_sayaci += 1
        simdi = time.time()
        guncel_sinyal = "0" 
        
        if frame_sayaci % AI_ISLEM_SIKLIGI == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            pose_result = pose_tracker.detect(mp_image)
            face_result = face_tracker.detect(mp_image)
            insan_goruldu = False
            
            # --- POSTÜR ---
            if pose_result.pose_landmarks:
                p_marks = pose_result.pose_landmarks[0]
                burun_p, sol_omuz, sag_omuz = p_marks[0], p_marks[11], p_marks[12]
                anlik_omuz_genisligi = abs(sol_omuz.x - sag_omuz.x)
                anlik_dikey_mesafe = ((sol_omuz.y + sag_omuz.y) / 2.0) - burun_p.y
                insan_goruldu = True
                
                if kalibrasyon_yapildi:
                    gecici_postur_hata = None
                    if anlik_omuz_genisligi > (ref_omuz_genisligi * 1.25): gecici_postur_hata = "YAKINLASMA"
                    elif anlik_dikey_mesafe < (ref_dikey_mesafe * 0.70): gecici_postur_hata = "KAMBUR"
                    elif anlik_dikey_mesafe > (ref_dikey_mesafe * 1.30): gecici_postur_hata = "KAYKILMA"

                    if gecici_postur_hata is not None:
                        if postur_ihlal_baslangic is None: postur_ihlal_baslangic = simdi
                        gecen_postur_sure = simdi - postur_ihlal_baslangic
                        kalan_sure = max(0, int(IHLAL_ESIK_SURESI - gecen_postur_sure))
                        
                        if gecen_postur_sure >= IHLAL_ESIK_SURESI:
                            son_postur_mesaj = f"POSTUR ALARMI! ({gecici_postur_hata})"
                            son_postur_renk = (0, 0, 255)
                            guncel_sinyal = "1" 
                            
                            if not postur_alarm_verildi:
                                postur_alarm_verildi = True
                                if gecici_postur_hata == "YAKINLASMA": 
                                    istatistikler["yakinlasma"] += 1
                                    ses_kuyrugu.put("Ekrana çok yaklaştın, lütfen geri çekil.")
                                elif gecici_postur_hata == "KAMBUR": 
                                    istatistikler["kambur"] += 1
                                    ses_kuyrugu.put("Duruşun bozuldu, lütfen dik otur.")
                                elif gecici_postur_hata == "KAYKILMA": 
                                    istatistikler["kaykilma"] += 1
                                    ses_kuyrugu.put("Arkanı çok yasladın, toparlan.")
                        else:
                            son_postur_mesaj = f"DURUS BOZUK! Alarm: {kalan_sure}sn"
                            son_postur_renk = (0, 255, 255)
                    else:
                        postur_ihlal_baslangic = None
                        postur_alarm_verildi = False
                        son_postur_mesaj = "POSTUR: IDEAL"
                        son_postur_renk = (0, 255, 0)
            
            # --- ODAK ---
            if face_result.face_landmarks and kalibrasyon_yapildi:
                f_marks = face_result.face_landmarks[0]
                burun_f, sol_yan, sag_yan = f_marks[1], f_marks[234], f_marks[454]
                alin, cene = f_marks[10], f_marks[152]
                
                # 1. Yüzün ekrandaki büyüklüğünden (kameraya uzaklıktan) bağımsız olması için oranlama
                yuz_genisligi = abs(sag_yan.x - sol_yan.x)
                yuz_uzunlugu = abs(cene.y - alin.y)
                
                if yuz_genisligi == 0: yuz_genisligi = 0.001
                if yuz_uzunlugu == 0: yuz_uzunlugu = 0.001
                
                anlik_yatay_oran = (burun_f.x - ((sol_yan.x + sag_yan.x) / 2.0)) / yuz_genisligi
                anlik_dikey_oran = (burun_f.y - ((alin.y + cene.y) / 2.0)) / yuz_uzunlugu
                
                yatay_sapma = anlik_yatay_oran - ref_yatay_oran
                dikey_sapma = anlik_dikey_oran - ref_dikey_oran
                
                # 2. Yeni Oransal Eşikler (Örn: Burun, yüz genişliğinin %15'i kadar sağa/sola kayarsa)
                gecici_odak_hata = None
                if yatay_sapma > 0.15 or yatay_sapma < -0.15: gecici_odak_hata = "YAN_BAKIS"
                elif dikey_sapma < -0.12: gecici_odak_hata = "YUKARI_BAKIS"
                elif dikey_sapma > 0.12 and not kitap_modu: gecici_odak_hata = "ASAGI_BAKIS"

                if gecici_odak_hata is not None:
                    if odak_ihlal_baslangic is None: odak_ihlal_baslangic = simdi
                    gecen_odak_sure = simdi - odak_ihlal_baslangic
                    
                    # Odak ihlali için bekleme süresini 3 saniyeye düşürdük (Daha hızlı tepki verir)
                    kalan_odak_sure = max(0, int(3.0 - gecen_odak_sure)) 
                    
                    if gecen_odak_sure >= 3.0:
                        son_odak_mesaj = f"ODAK ALARMI! ({gecici_odak_hata})"
                        son_odak_renk = (0, 0, 255)
                        if guncel_sinyal == "0": guncel_sinyal = "2" 
                            
                        if not odak_alarm_verildi:
                            odak_alarm_verildi = True
                            if gecici_odak_hata == "YAN_BAKIS": 
                                istatistikler["yan_bakis"] += 1
                                ses_kuyrugu.put("Lütfen ekrana odaklan.")
                            elif gecici_odak_hata == "YUKARI_BAKIS": 
                                istatistikler["yukari_bakis"] += 1
                                ses_kuyrugu.put("Yukarı bakıyorsun, işine dön.")
                            elif gecici_odak_hata == "ASAGI_BAKIS": 
                                istatistikler["asagi_bakis"] += 1
                                ses_kuyrugu.put("Aşağı bakıyorsun, odağını topla.")
                    else:
                        son_odak_mesaj = f"ODAK BOZUK! Alarm: {kalan_odak_sure}sn"
                        son_odak_renk = (0, 255, 255)
                else:
                    odak_ihlal_baslangic = None
                    odak_alarm_verildi = False
                    if kitap_modu and dikey_sapma > 0.12:
                        son_odak_mesaj = "ODAK: KITAP OKUNUYOR"
                        son_odak_renk = (255, 255, 0)
                    else:
                        son_odak_mesaj = "ODAK: EKRANDA"
                        son_odak_renk = (0, 255, 0)
            # --- HABERLEŞME (YENİ SİSTEM) ---
            if guncel_sinyal != son_gonderilen_sinyal:
                if esp32_bagli:
                    try:
                        if guncel_sinyal == "0":
                            komut = "0\n" # Her şey yolunda
                        else:
                            # İhlal varsa moda göre PATTES'e emir ver
                            komut = "K\n" if kitap_modu else "E\n"
                        esp32.write(komut.encode())
                    except Exception as e:
                        print(f"Seri Port Hatası: {e}")
                son_gonderilen_sinyal = guncel_sinyal

        # --- EKRAN ---
        if not kalibrasyon_yapildi:
            cv2.putText(frame, "DIK OTUR, EKRANA BAK VE 'c' TUSUNA BAS", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            cv2.putText(frame, son_postur_mesaj, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, son_postur_renk, 2)
            cv2.putText(frame, son_odak_mesaj, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, son_odak_renk, 2)
            if kitap_modu: cv2.putText(frame, "[KITAP MODU AKTIF]", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.imshow("PATTES Akilli Asistan", frame)
        
        # --- TUŞLAR ---
        tus = cv2.waitKey(1) & 0xFF
        if tus == ord('c') and insan_goruldu:
            ref_omuz_genisligi, ref_dikey_mesafe = anlik_omuz_genisligi, anlik_dikey_mesafe
            ref_yatay_oran, ref_dikey_oran = anlik_yatay_oran, anlik_dikey_oran
            kalibrasyon_yapildi = True
            ses_kuyrugu.put("Sistem kilitlendi. İyi çalışmalar.")
        elif tus == ord('k'):
            kitap_modu = not kitap_modu
            if kitap_modu:
                ses_kuyrugu.put("Kitap modu açıldı.")
                if esp32_bagli: esp32.write("0\n".encode()) # Mod değişince alarmı sustur
            else:
                ses_kuyrugu.put("Kitap modu kapatıldı.")
                if esp32_bagli: esp32.write("0\n".encode())
        elif tus == ord('q'):
            break

# ====================================================================
# 5. KAPANIS VE RAPORLAMA
# ====================================================================

ses_kuyrugu.put(None) 
cap.release()
cv2.destroyAllWindows()

if esp32_bagli:
    try:
        esp32.write("0\n".encode()) 
        esp32.close()
    except:
        pass

bitis_zamani = time.time()
gecen_sure = int(bitis_zamani - baslangic_zamani)
dakika = gecen_sure // 60
saniye = gecen_sure % 60

# Gelişmiş İstatistik Hesaplamaları
toplam_ihlal = sum(istatistikler.values())
toplam_postur_ihlali = istatistikler['yakinlasma'] + istatistikler['kambur'] + istatistikler['kaykilma']
toplam_odak_ihlali = istatistikler['yan_bakis'] + istatistikler['yukari_bakis'] + istatistikler['asagi_bakis']

# Her 1 ihlal odaklanma skorunu 2 puan düşürür
verimlilik_puani = max(0, 100 - (toplam_ihlal * 2))

rapor_metni = f"""
==================================================
      PATTES DETAYLI ÇALIŞMA OTURUMU RAPORU
==================================================
Tarih: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Toplam Çalışma Süresi: {dakika} dakika {saniye} saniye
Genel Odaklanma Skoru: %{verimlilik_puani}

[POSTÜR (DURUŞ) İHLALLERİ] - Toplam: {toplam_postur_ihlali}
- Ekrana Fazla Yaklaşma : {istatistikler['yakinlasma']} kez
- Öne Eğilme / Kambur   : {istatistikler['kambur']} kez
- Arkaya Yaslanma       : {istatistikler['kaykilma']} kez

[ODAK (DİKKAT) İHLALLERİ] - Toplam: {toplam_odak_ihlali}
- Sağa/Sola Bakma       : {istatistikler['yan_bakis']} kez
- Yukarı Bakma          : {istatistikler['yukari_bakis']} kez
- İzinsiz Aşağı Bakma   : {istatistikler['asagi_bakis']} kez
==================================================
"""

# Yapay Zeka (PATTES) Değerlendirme Yorumu
if verimlilik_puani >= 90:
    rapor_metni += "PATTES YORUMU: Harika bir çalışma seansıydı! Mükemmel odaklandın.\n"
elif verimlilik_puani >= 70:
    rapor_metni += "PATTES YORUMU: İyi iş çıkardın ama duruşuna ve odağına biraz daha dikkat etmelisin.\n"
else:
    rapor_metni += "PATTES YORUMU: Bugün çok fazla bölündün. Bir dahaki sefere telefonu ve çevreyi unutmalısın!\n"

rapor_metni += "==================================================\n"

with open("PATTES_Rapor.txt", "w", encoding="utf-8") as dosya:
    dosya.write(rapor_metni)

print(f"\nOturum kapatıldı. Detaylı rapor 'PATTES_Rapor.txt' dosyasına başarıyla işlendi!")
"""

with open("PATTES_Rapor.txt", "w", encoding="utf-8") as dosya:
    dosya.write(rapor_metni)

print(f"\nOturum kapatıldı. Rapor 'PATTES_Rapor.txt' dosyasına başarıyla işlendi!")
