import os
import json
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')

async def _guvenli_ai_cagrisi(prompt):
    """
    Sistemin sonsuza kadar donmasını engeller! 
    Kilitlenme olursa 20 saniye sonra hatayı basar ve botu kurtarır.
    """
    return await asyncio.wait_for(
        asyncio.to_thread(model.generate_content, prompt),
        timeout=20.0
    )

async def ajan_calistir(mesaj):
    prompt = f"""Sen akıllı bir proje yöneticisi ve Slack asistanısın. Kullanıcı mesajına göre aşağıdaki araçlardan en uygun olanı seç ve JSON formatında dön.
    
    Araçlar:
    1. "sessiz_kal": Gündelik muhabbet veya ilgisiz mesajlar. Parametre yok.
    2. "soru_sor": Talep belirsizse. Parametre: {{"mesaj": "Soru"}}
    3. "jira_post": Yeni görev. Parametre: {{"path": "/rest/api/2/issue", "body": {{"fields": {{"summary": "Başlık", "description": "Özet", "issuetype": {{"name": "Task"}}}}}}}}
    4. "jira_get": Bilet kapatma/güncelleme. Parametre: {{"path": "/rest/api/2/search"}}
    
    Mesaj: {mesaj}
    SADECE JSON DÖN.
    """
    try:
        response = await _guvenli_ai_cagrisi(prompt)
        cevap_metni = response.text.strip()
        if cevap_metni.startswith("```json"): cevap_metni = cevap_metni[7:-3].strip()
        elif cevap_metni.startswith("```"): cevap_metni = cevap_metni[3:-3].strip()
            
        karar = json.loads(cevap_metni)
        
        alet = karar.get("tool", "")
        if not alet:
            if "jira_post" in cevap_metni: alet = "jira_post"
            elif "jira_get" in cevap_metni: alet = "jira_get"
            elif "sessiz_kal" in cevap_metni: alet = "sessiz_kal"
            else: alet = "soru_sor"
            
        parametreler = karar.get("parameters", {}) if "parameters" in karar else karar
        cevap = parametreler.get("mesaj", "")
        
        print(f"[ADIM 1] Ajan Karari: {alet} -> {parametreler}", flush=True)
        return cevap, alet, parametreler
    except Exception as e:
        print(f"❌ Ajan karar hatası: {e}", flush=True)
        return "Bunu tam anlayamadım, biraz detaylandırır mısın?", "soru_sor", {}

async def analist_detay_uret(baslik):
    print(f"🧠 Yapay zeka '{baslik}' için detayları düşünüyor...", flush=True)
    prompt = f"Şu görev başlığı için profesyonel, kısa ve net bir Jira ticket açıklaması (description) yaz: {baslik}"
    try:
        response = await _guvenli_ai_cagrisi(prompt)
        return response.text.strip()
    except:
        return baslik

async def bilet_eslestir_ai(talep, arama_sonucu):
    prompt = f"""Kullanıcı talebi: {talep}
    Aşağıdaki liste içinden, kullanıcı talebiyle eşleşen biletin SADECE KEY KODUNU yaz. Yoksa YOK yaz.
    Sonuç: {arama_sonucu}"""
    try:
        response = await _guvenli_ai_cagrisi(prompt)
        sonuc = response.text.strip()
        return sonuc if sonuc else "YOK"
    except:
        return "YOK"

async def yazilimci_ai(talep, mevcut_kod):
    print("🧠 Yapay Zeka Yazılımcı (AI Coder) dosyayı inceliyor ve kodu yazıyor...", flush=True)
    prompt = f"""Sen uzman bir web geliştiricisin. Aşağıdaki mevcut HTML kodunu talebe göre güncelle.
    SADECE GÜNCEL DOSYANIN TAMAMINI VER. ```html işaretleri KESİNLİKLE KOYMA!
    Talep: {talep}\n\nKod:\n{mevcut_kod}"""
    try:
        response = await _guvenli_ai_cagrisi(prompt)
        yeni_kod = response.text.strip()
        if yeni_kod.startswith("```"):
            satirlar = yeni_kod.split('\n')
            if len(satirlar) > 2: yeni_kod = '\n'.join(satirlar[1:-1])
        return yeni_kod
    except Exception as e:
        print(f"❌ Yazılımcı AI Çöktü: {e}", flush=True)
        return None

async def ai_veri_cikar(ham_metin, ne_ariyoruz):
    print(f"🧠 AI Veri Avcısı aranıyor: '{ne_ariyoruz}'", flush=True)
    prompt = f"""Bir veri ayıklama uzmanısın. Çıktıdan istenen bilgiyi bul ve SADECE onu yaz. Yoksa YOK yaz.
    Bilgi: {ne_ariyoruz}\nÇıktı:\n{ham_metin}"""
    try:
        response = await _guvenli_ai_cagrisi(prompt)
        sonuc = response.text.strip()
        if sonuc.upper() == "YOK" or not sonuc: return None
        return sonuc
    except Exception as e:
        print(f"❌ Veri çıkarma hatası: {e}", flush=True)
        return None