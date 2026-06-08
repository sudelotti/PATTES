import time
import pyttsx3
import speech_recognition as sr
from openai import OpenAI 

# --- SİSTEM UYARILARINI SUSTURMA ---
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Kopyaladığın DeepSeek API şifren
API_KEY = "sk-71672d08cae344f88c2d481ad303114a"

if not API_KEY or API_KEY == "BURAYA_DEEPSEEK_SIFREN_GELECEK":
    print("❌ Hata: Lütfen kodun içindeki API_KEY kısmına kendi şifreni yapıştır!")
    exit()

def deepseek_cevap_uret(kullanici_sorusu):
    try:
        client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")
        print(f"\n🧠 PATTES Düşünüyor...")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "PATTES isimli sevimli, disleksi dostu, destekleyici ve zeki bir ders çalışma robotusun. Cevapların bir konuşma diline uygun, en fazla 2-3 cümle, basit, anlaşılır ve Türkçe olmalıdır. Emoji kullanma."},
                {"role": "user", "content": kullanici_sorusu}
            ],
            temperature=0.7,
            max_tokens=150 
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"❌ DeepSeek Sunucu Hatası Yakalandı: {e}")
        return "Üzgünüm, şu an sunucularıma ulaşamıyorum."

# --- BİLGİSAYAR HOPARLÖRÜ FONKSİYONU ---
def bilgisayardan_ses_ver(cevap_metni):
    print("🔊 PATTES Konuşuyor...")
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 190) 
        engine.setProperty('volume', 1.0)
        
        voices = engine.getProperty('voices')
        for voice in voices:
            if "TR" in voice.id or "Turkish" in voice.name:
                engine.setProperty('voice', voice.id)
                break
        
        engine.say(cevap_metni)
        engine.runAndWait()
            
    except Exception as e:
        print(f"❌ Ses Çıktısı Hatası: {e}")

# --- ANA ASİSTAN DÖNGÜSÜ (UYKU VE UYANMA MODU) ---
def ana_asistan_dongusu():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🤖 PATTES Sistemi Başlatıldı. PC Hoparlörü Devrede!")
        r.adjust_for_ambient_noise(source, duration=1)
        
        while True:
            print("\n💤 PATTES Uykuda... (Uyanmak için 'Pattes' demeni bekliyor)")
            try:
                # AŞAMA 1: PASİF DİNLEME (Uyandırma kelimesi)
                audio_tetik = r.listen(source, timeout=3, phrase_time_limit=3)
                tetik_metni = r.recognize_google(audio_tetik, language="tr-TR").lower()
                
                if "pattes" in tetik_metni or "patates" in tetik_metni:
                    print("🔔 Uyandırma kelimesi algılandı!")
                    bilgisayardan_ses_ver("Efendim, seni dinliyorum.")
                    
                    # AŞAMA 2: AKTİF DİNLEME (Asıl Soru)
                    print("🎤 PATTES Asıl Sorunu Dinliyor...")
                    # İlk kelime için 7 saniye bekler, toplamda 15 saniye kesintisiz dinler:
                    audio_komut = r.listen(source, timeout=5, phrase_time_limit=15)
                    komut_metni = r.recognize_google(audio_komut, language="tr-TR")
                    print(f"🗣️ Sen dedin ki: {komut_metni}")
                    
                    # Güvenli Kapatma Komutu
                    if komut_metni.lower() in ['kapat', 'çıkış', 'uyu', 'uykuya dön']:
                        bilgisayardan_ses_ver("Uyku moduna geçiyorum. Kolay gelsin!")
                        break 
                        
                    # Soruyu DeepSeek'e yolla
                    cevap = deepseek_cevap_uret(komut_metni)
                    if cevap:
                        print(f"\n🤖 PATTES'in Cevabı:\n{cevap}")
                        bilgisayardan_ses_ver(cevap)
                        
            except sr.WaitTimeoutError:
                pass 
            except sr.UnknownValueError:
                pass 
            except sr.RequestError:
                print("❌ İnternet bağlantısı koptu. Google'a ulaşılamıyor.")
                time.sleep(2)

# --- ANA ŞALTER ---
if __name__ == "__main__":
    ana_asistan_dongusu()