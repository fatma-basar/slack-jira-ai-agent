import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- GEMİNİ YAPILANDIRMASI ---
# Gelecekte Google uyarılarını almamak için yeni API mantığına geçiş hazırlığı yapıldı
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

async def ajan_calistir(mesaj):
    """
    Kullanıcıdan gelen mesajı anlar ve hangi aksiyonu alması gerektiğine karar verir.
    """
    prompt = f"""Sen akıllı bir proje yöneticisi ve Slack asistanısın. Kullanıcı mesajına göre aşağıdaki araçlardan en uygun olanı seç ve JSON formatında dön.
    
    Araçlar:
    1. "sessiz_kal": Gündelik muhabbet, selamlama ("merhaba", "nasılsın"), dedikodu veya ilgisiz mesajlar. Parametre yok.
    2. "soru_sor": Talep çok belirsizse (Örn: "Bir şey bozuk"). Parametre: {{"mesaj": "Sormak istediğin soru"}}
    3. "jira_post": Yeni bir görev, kod veya tasarım değişikliği isteniyorsa. Parametre: {{"path": "/rest/api/2/issue", "body": {{"fields": {{"summary": "Başlık", "description": "Talebin kısa özeti", "issuetype": {{"name": "Task"}}}}}}}}
    4. "jira_get": Açık olan veya önceden konuşulmuş bir biletin kapatılması/güncellenmesi isteniyorsa. Parametre: {{"path": "/rest/api/2/search"}}
    
    Mesaj: {mesaj}
    
    SADECE JSON DÖN.
    """
    try:
        response = await model.generate_content_async(prompt)
        # Markdown etiketlerini temizle
        cevap_metni = response.text.strip()
        if cevap_metni.startswith("```json"):
            cevap_metni = cevap_metni[7:-3].strip()
        elif cevap_metni.startswith("```"):
            cevap_metni = cevap_metni[3:-3].strip()
            
        karar = json.loads(cevap_metni)
        
        # Senin loglarındaki formata uyması için değerleri ayıklıyoruz:
        alet = karar.get("tool", "")
        if not alet: # Eğer json formatı farklıysa manuel bul
            if "jira_post" in cevap_metni: alet = "jira_post"
            elif "jira_get" in cevap_metni: alet = "jira_get"
            elif "sessiz_kal" in cevap_metni: alet = "sessiz_kal"
            else: alet = "soru_sor"
            
        parametreler = karar.get("parameters", {}) if "parameters" in karar else karar
        cevap = parametreler.get("mesaj", "")
        
        print(f"[ADIM 1] Ajan Karari: {alet} -> {parametreler}")
        return cevap, alet, parametreler
    except Exception as e:
        print(f"Ajan karar hatası: {e}")
        return "Bunu tam anlayamadım, biraz detaylandırır mısın?", "soru_sor", {}

async def analist_detay_uret(baslik):
    """Bilet başlığına göre profesyonel bir açıklama (description) yazar."""
    print(f"🧠 Yapay zeka '{baslik}' için detayları düşünüyor...")
    prompt = f"Şu görev başlığı için profesyonel, kısa ve net bir Jira ticket açıklaması (description) yaz: {baslik}"
    try:
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except:
        return baslik

async def bilet_eslestir_ai(talep, arama_sonucu):
    """Açık biletler arasından kullanıcının bahsettiği bileti bulur."""
    prompt = f"""
    Kullanıcı talebi: {talep}
    Aşağıdaki açık bilet listesi içinden, kullanıcının talebiyle en çok eşleşen biletin SADECE KEY KODUNU (Örn: TEAM-25) yaz. 
    Eğer eşleşen bilet yoksa SADECE YOK yaz. Başka hiçbir kelime kullanma.
    
    Arama Sonucu: {arama_sonucu}
    """
    try:
        response = await model.generate_content_async(prompt)
        sonuc = response.text.strip()
        return sonuc if sonuc else "YOK"
    except:
        return "YOK"

async def yazilimci_ai(talep, mevcut_kod):
    """
    HTML kodunu okur ve günceller (KURŞUNGEÇİRMEZ VERSİYON).
    Markdown işaretlerini engeller.
    """
    print("🧠 Yapay Zeka Yazılımcı (AI Coder) dosyayı inceliyor ve kodu yazıyor...")
    
    prompt = f"""
    Sen uzman bir web geliştiricisin. Aşağıdaki mevcut HTML kodunu, kullanıcının talebine göre güncelle.
    
    ÇOK ÖNEMLİ KURALLAR:
    1. BANA SADECE GÜNCEL DOSYANIN TAMAMINI VER.
    2. Kodların başına veya sonuna ```html veya ``` GİBİ İŞARETLER KESİNLİKLE KOYMA! (Bunu yaparsan sistem çöker).
    3. Hiçbir açıklama metni veya "İşte kodunuz" gibi cümleler yazma. SADECE SAF KOD!
    
    TALEP: {talep}
    
    MEVCUT KOD:
    {mevcut_kod}
    """
    try:
        response = await model.generate_content_async(prompt)
        yeni_kod = response.text.strip()
        
        # Yapay zeka inat edip ```html işareti koyduysa, kodla temizle
        if yeni_kod.startswith("```"):
            satirlar = yeni_kod.split('\n')
            if len(satirlar) > 2:
                yeni_kod = '\n'.join(satirlar[1:-1])
                
        return yeni_kod
    except Exception as e:
        print(f"❌ Yazılımcı AI Çöktü: {e}")
        return None

async def ai_veri_cikar(ham_metin, ne_ariyoruz):
    """
    MCP'den gelen karmaşık Atlassian (YAML/JSON benzeri) metinlerini Python yerine AI'a okutur.
    Böylece sistem hiçbir zaman 'Expecting value' hatası verip çökmez.
    """
    print(f"🧠 AI Veri Avcısı, karmaşık metinden şu veriyi arıyor: '{ne_ariyoruz}'")
    
    prompt = f"""
    Sen bir veri ayıklama uzmanısın. Aşağıdaki karmaşık sistem çıktısından, istenen bilgiyi bul.
    SADECE VE SADECE bulduğun değeri yaz. Hiçbir açıklama, boşluk, nokta veya cümle ekleme.
    Eğer bulamazsan sadece YOK yaz.
    
    İstenen Bilgi: {ne_ariyoruz}
    
    Sistem Çıktısı:
    {ham_metin}
    """
    try:
        response = await model.generate_content_async(prompt)
        sonuc = response.text.strip()
        if sonuc.upper() == "YOK" or not sonuc:
            return None
        return sonuc
    except Exception as e:
        print(f"❌ Veri çıkarma hatası: {e}")
        return None