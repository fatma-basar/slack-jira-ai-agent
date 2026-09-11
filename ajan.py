import json
import os
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# ==========================================
# GÜVENLİ API BAĞLANTISI (.env üzerinden)
load_dotenv()
gemini_sifresi = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_sifresi)

# Stabil ve hızlı model
model = genai.GenerativeModel('gemini-3.5-flash') 
# ==========================================

def ajan_calistir(kullanici_mesaji, onceki_mesaj="", mevcut_bilet_key=None, adim=0):
    bugun_metin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
    Sen OTONOM bir Jira Ajanisin. Gerekirse once arama yapar, sonra islem yaparsin.
    Zaman: {bugun_metin}. Hafizadaki Bilet: {mevcut_bilet_key if mevcut_bilet_key else "YOK"}
    
    Kullanicinin Onceki Mesaji: '{onceki_mesaj}'
    Kullanicinin Yeni Mesaji: '{kullanici_mesaji}'
    
    KESIN KURALLAR (Sırasıyla uygula):
    1. 🔴 MUTLAK KURAL - SESSİZLİK: Eger 'Kullanicinin Yeni Mesaji' sadece "selam", "merhaba", "gunaydin", "naber", "yemek" gibi kelimelerden ibaretse ve teknik bir is TALEBI DEGILSE:
       - Onceki mesajlari ve biletleri TAMAMEN GORMEZDEN GEL!
       - KESINLIKLE 'sessiz_kal' aracini sec! 
       - Asla kibarlik yapma, asla yardimci olmaya calisma, asla soru_sor kullanma!

    2. YENI GOREV ACMA (Kullanici yepyeni bir is/talep veriyorsa): 
       - 'jira_post' kullan. Path: '/rest/api/2/issue', Body: {{"fields": {{"project": {{"key": "TEAM"}}, "summary": "Baslik", "description": "Detay", "issuetype": {{"name": "Task"}}}}}}
       
    3. ARAMA YAPMA (Kullanici "X duzeltildi", "hallettim" diyorsa ama bilet kodunu vermiyorsa):
       - HEMEN SORU SORMA! KESINLIKLE once 'jira_get' aracini kullanarak arama yap!
       - Path: '/rest/api/2/search?jql=text~\\"aranacak_kelime\\"'
       
    4. GOREV KAPATMA (Eger bilet numarasi verilmişse veya az once arama yapip bilet kodunu bulduysan):
       - 'jira_post' kullan. Path: '/rest/api/2/issue/BILET_KODU/transitions'. Body: {{"transition": {{"id": "31"}}}}
       
    5. EKSIK GOREV BILGISI (SADECE teknik bir is istediyse ama detay vermediyse):
       - 'soru_sor' aracini kullan ve 'mesaj' parametresi ile eksik olan detayi sor.

    SADECE asagidaki JSON formatinda cevap ver (Baska metin ekleme):
    {{
        "kullanilacak_alet": "secilen_aletin_adi",
        "parametreler": {{
            "mesaj": "deger_veya_soru"
        }}
    }}
    """

    response = model.generate_content(prompt)
    metin_cevap = response.text.replace("```json", "").replace("```", "").strip()
    
    try:
        veri = json.loads(metin_cevap)
        alet_adi = veri.get("kullanilacak_alet", "YOK")
        parametreler = veri.get("parametreler", {})
    except Exception as e:
        print(f"JSON Parse Hatasi: {e}")
        return "YOK", "YOK", {}

    if alet_adi == "YOK":
        return "YOK", "YOK", {}

    if alet_adi == "sessiz_kal":
        print(f"[ADIM {adim+1}] Ajan Karari: {alet_adi} -> İlgisiz mesaj, bot sessiz kaliyor.", flush=True)
        return "", "sessiz_kal", {} 

    print(f"[ADIM {adim+1}] Ajan Karari: {alet_adi} -> {parametreler}", flush=True)

    if alet_adi == "soru_sor":
        cevap_metni = parametreler.get("mesaj", parametreler.get("soru", "Hangi görevden bahsediyorsun?"))
        return cevap_metni, "soru_sor", parametreler

    return "", alet_adi, parametreler

def analist_detay_uret(kisa_baslik):
    print(f"🧠 Yapay zeka '{kisa_baslik}' için detayları düşünüyor...")
    
    prompt = f"""
    Sen, yazilim projelerinde gorev alan uzman bir 'Senior Is Analisti'sin.
    Asagidaki kisa gorev basligini al ve yazilim ekibi icin detayli bir Jira aciklamasina donustur.

    Gorev Basligi: "{kisa_baslik}"

    KURAL: Ciktini KESINLIKLE asagidaki Markdown sablonuna birebir uyarak uret. Ekstra sohbet metni yazma.

    ## Gorev Ozeti
    [2-3 cumlelik net aciklama]

    ## Kullanici Hikayesi
    * **Kullanici Olarak:** [Kimin icin?]
    * **Istegim:** [Ne yapilacak?]
    * **Amacim:** [Faydasi ne?]

    ## Kabul Kriterleri (Acceptance Criteria)
    * 
    * 

    ## Teknik Gereksinimler
    1. 
    2. 

    ## Test Senaryolari
    * Pozitif Senaryo:
    * Negatif Senaryo:

    ## Riskler ve Bagimliliklar
    [Varsa riskler, yoksa 'Bilinen risk yok' yaz.]
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Analiz Hatası: {e}")
        return "Detaylar üretilirken bir hata oluştu."

def bilet_eslestir_ai(kullanici_mesaji, acik_biletler):
    """Kullanıcının yazdığı mesajla, Jira'daki açık biletleri anlamsal olarak eşleştirir."""
    if not acik_biletler:
        return "YOK"
        
    # Biletleri alt alta metin haline getiriyoruz (AI okusun diye)
    biletler_metni = "\n".join([f"- {b['key']}: {b['summary']}" for b in acik_biletler])
    
    print("🧠 Yapay zeka biletler arasında anlamsal eşleştirme yapıyor...")
    
    prompt = f"""
    Sen akıllı bir asistansın. Kullanıcı bir yazılım görevini tamamladığını söylüyor.
    Kullanıcının Mesajı: "{kullanici_mesaji}"
    
    Jira'da şu an açık olan görevler şunlar:
    {biletler_metni}
    
    GÖREV: Kullanıcının mesajında bahsettiği iş, yukarıdaki biletlerden hangisi olabilir?
    (Örneğin kullanıcı 'odeme' diyorsa ve bilette 'ödeme' yazıyorsa anlamsal olarak eşleştir).
    
    KURAL: SADECE eşleşen biletin kodunu (Örn: SCRUM-9) yaz. Başka hiçbir kelime veya nokta ekleme.
    Eğer hiçbir biletle alakası yoksa sadece YOK yaz.
    """
    
    try:
        response = model.generate_content(prompt)
        sonuc = response.text.strip()
        return sonuc
    except Exception as e:
        print(f"Eşleştirme Hatası: {e}")
        return "YOK"   

def yazilimci_ai(kullanici_mesaji, mevcut_kod):
    """Yapay zekanın mevcut kodu okuyup kullanıcının isteğine göre yeniden yazmasını sağlar."""
    print("🧠 Yapay Zeka Yazılımcı (AI Coder) dosyayı inceliyor ve kodu yazıyor...")
    
    prompt = f"""
    Sen uzman bir Frontend yazılımcısısın (AI Coder).
    Kullanıcının Slack'ten gelen isteği: "{kullanici_mesaji}"
    
    Mevcut index.html dosyasının içeriği:
    {mevcut_kod}
    
    GÖREV: Kullanıcının isteğine göre yukarıdaki HTML kodunu düzelt veya istenen yeni özelliği ekle.
    
    KURAL: BANA SADECE ÇALIŞIR DURUMDAKİ YENİ HTML KODUNU VER. 
    Başına veya sonuna "İşte kodunuz", "```html" gibi hiçbir markdown, açıklama veya sohbet metni EKLEME. 
    SADECE DOĞRUDAN KODU YAZ, çünkü senin çıktın doğrudan index.html dosyasının içine kaydedilecek!
    """
    
    try:
        response = model.generate_content(prompt)
        # Bazen AI inatla ```html ekleyebilir, onu temizliyoruz ki dosya bozulmasın
        temiz_kod = response.text.replace("```html", "").replace("```", "").strip()
        return temiz_kod
    except Exception as e:
        print(f"Yapay Zeka Kodlama Hatası: {e}")
        return None     