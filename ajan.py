import asyncio
import os
import sys
import codecs
import json
import re
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

slack_app = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

bilet_hafizasi = {}
sohbet_gecmisi = {} 

async def mcp_ile_calistir(alet_adi, parametreler):
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    jira_tam_url = os.getenv("JIRA_URL", "")
    site_adi = jira_tam_url.replace("https://", "").replace("http://", "").split(".")[0]
    my_env["ATLASSIAN_SITE_NAME"] = site_adi
    my_env["ATLASSIAN_USER_EMAIL"] = os.getenv("JIRA_EMAIL", "")
    my_env["ATLASSIAN_API_TOKEN"] = os.getenv("JIRA_API_TOKEN", "")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@aashari/mcp-server-atlassian-jira"],
        env=my_env
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                sonuc = await session.call_tool(alet_adi, arguments=parametreler)
                return sonuc.content[0].text
    except Exception as e:
        return f"Hata olustu: {str(e)}"

async def jira_islemini_yap(kullanici_mesaji: str, kullanici: str) -> tuple:
    match = re.search(r'([a-zA-Z]+-\d+)', kullanici_mesaji)
    if match:
        bilet_hafizasi[kullanici] = match.group(1).upper()
        
    mevcut_bilet_key = bilet_hafizasi.get(kullanici)
    onceki_mesaj = sohbet_gecmisi.get(kullanici, "YOK")

    su_an = datetime.now()
    gunler = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]
    aylar = ["Ocak", "Subat", "Mart", "Nisan", "Mayis", "Haziran", "Temmuz", "Agustos", "Eylul", "Ekim", "Kasim", "Aralik"]
    bugun_metin = f"{su_an.day} {aylar[su_an.month - 1]} {su_an.year} {gunler[su_an.weekday()]}, Saat: {su_an.strftime('%H:%M')}"

    ek_bilgi = ""
    
    for adim in range(2): 
        prompt = f"""
        Sen OTONOM bir Jira Ajanisin. Gerekirse once arama yapar, sonra islem yaparsin.
        Zaman: {bugun_metin}. Hafizadaki Bilet: {mevcut_bilet_key if mevcut_bilet_key else "YOK"}
        
        Kullanicinin Onceki Mesaji: '{onceki_mesaj}'
        Kullanicinin Yeni Mesaji: '{kullanici_mesaji}'
        
        {ek_bilgi}
        
        KESIN KURALLAR:
        1. YENI GOREV ACMA: 'jira_post' kullan. Path: '/rest/api/2/issue', Body: {{"fields": {{"project": {{"key": "TEAM"}}, "summary": "Baslik", "description": "Detay", "issuetype": {{"name": "Task"}}}}}}
        
        2. ARAMA YAPMA (Kullanici "X isini hallettim" diyor ama X isi hafizadaki bilet degilse):
           - KESINLIKLE once 'jira_get' aracini kullanip dogru bileti bul!
           - Path: '/rest/api/2/search?jql=text~"kullanicinin_bahsettigi_kelime"'
           
        3. GOREV BITIRME/KAPATMA (Eger bilet numarasi kesinlesmisse veya az once arama yapip bulduysan):
           - 'jira_post' kullan. Path: '/rest/api/2/issue/BILET_KODU/transitions'. Body: {{"transition": {{"id": "31"}}}}
           
        4. Eger bilet bulamadiysan veya emin degilsen: 'soru_sor' aracini kullan.

        SADECE asagidaki JSON formatinda cevap ver:
        {{
            "kullanilacak_alet": "secilen_aletin_adi",
            "parametreler": {{
                "parametre_adi": "deger"
            }}
        }}
        """

        chat = gemini_client.chats.create(model='gemini-3.5-flash')
        cevap = chat.send_message(prompt)

        sohbet_gecmisi[kullanici] = kullanici_mesaji

        temiz = cevap.text.strip()
        if temiz.startswith("```json"):
            temiz = temiz[7:-3].strip()
        elif temiz.startswith("```"):
            temiz = temiz[3:-3].strip()

        try:
            karar = json.loads(temiz)
        except:
            return "YOK", "YOK", {}

        alet_adi = karar.get("kullanilacak_alet")
        parametreler = karar.get("parametreler", {})

        if alet_adi == "YOK" or alet_adi == "sohbet_et":
            return "YOK", "YOK", {}

        print(f"[ADIM {adim+1}] Ajan Karari: {alet_adi} -> {parametreler}", flush=True)

        if alet_adi == "soru_sor":
            return parametreler.get("mesaj", "Hangi görevden bahsediyorsun?"), "soru_sor", parametreler

        mcp_sonucu = await mcp_ile_calistir(alet_adi, parametreler)

        # --- YENİ EKLENEN KISIM: KATI EMİR VE VERİ KISALTMA ---
        if alet_adi == "jira_get" and "/search" in parametreler.get("path", ""):
            kisaltilmis_sonuc = mcp_sonucu[:2000] # Veriyi kucult ki kafasi karismasin
            ek_bilgi = f"\n[SISTEMDEN ZORUNLU EMIR]: Az once arama yaptin ve su sonucu buldun: {kisaltilmis_sonuc}\nDIKKAT: KESINLIKLE 2. KEZ ARAMA YAPMA! Eger sonuclar icinde 'key' (Orn: TEAM-XX) degeri goruyorsan, hemen 'jira_post' aracini kullanarak KAPATMA (/transitions) islemini yap. Eger sonuc bossa 'soru_sor' aracini kullan."
            print("Ajan arama yapti, 2. adima (karar/kapatma) geciliyor...", flush=True)
            continue 
        
        else:
            return mcp_sonucu, alet_adi, parametreler

    return "Ajan islemi 2 adimda tamamlayamadi. Lutfen bilet kodunu (Orn: TEAM-15) belirterek tekrar deneyin.", "YOK", {}

async def arka_planda_islem_yap(event, say):
    raw_text = event.get('text', '')
    kullanici = event.get('user')
    temiz_mesaj = re.sub(r'<@.*?>', '', raw_text).strip()
    
    try:
        jira_cevabi, kullanilan_alet, parametreler = await jira_islemini_yap(temiz_mesaj, kullanici)
        
        if jira_cevabi != "YOK":
            kapatilan_bilet_match = re.search(r'issue/([A-Z]+-\d+)', parametreler.get("path", ""))
            aktif_bilet = kapatilan_bilet_match.group(1) if kapatilan_bilet_match else bilet_hafizasi.get(kullanici, "")

            if kullanilan_alet == "jira_post" and "/transitions" in parametreler.get("path", ""):
                jira_cevabi = f"Harika! Senin icin arastirdim, {aktif_bilet} numarali gorevi buldum ve basariyla 'Tamamlandi' (Done) olarak isaretledim."
                bilet_hafizasi[kullanici] = None 
            
            elif kullanilan_alet == "jira_put":
                jira_cevabi = f"{aktif_bilet} numarali bilet basariyla guncellendi."
                
            elif kullanilan_alet == "jira_post":
                match = re.search(r'([A-Z]+-\d+)', jira_cevabi)
                if match:
                    yeni_bilet = match.group(1).upper()
                    bilet_hafizasi[kullanici] = yeni_bilet 
                    print(f"HAFIZAYA KAYDEDILDI: Kullanici({kullanici}) -> {yeni_bilet}", flush=True)
                    
            gercek_thread_ts = event.get('thread_ts')
            if gercek_thread_ts:
                await say(text=f"<@{kullanici}>\n{jira_cevabi}", thread_ts=gercek_thread_ts)
            else:
                await say(f"<@{kullanici}>\n{jira_cevabi}")
            
    except Exception as e:
        print(f"Arka plan islem hatasi: {str(e)}", flush=True)

@slack_app.event("message")
async def handle_message(event, say):
    if "bot_id" in event:
        return
    asyncio.create_task(arka_planda_islem_yap(event, say))

@slack_app.event("app_mention")
async def handle_mention(event, say):
    if "bot_id" in event:
        return
    asyncio.create_task(arka_planda_islem_yap(event, say))

async def main():
    print("ENTERPRISE JIRA AJANI (V5.1 - OTONOM ARAMA HATASI GIDERILDI)", flush=True)
    handler = AsyncSocketModeHandler(slack_app, os.getenv("SLACK_APP_TOKEN"))
    await handler.start_async()

if __name__ == "__main__":
    asyncio.run(main())