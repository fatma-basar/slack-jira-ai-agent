import asyncio
import os
import sys
import codecs
import json
import re
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

async def jira_islemini_yap(kullanici_mesaji: str) -> str:
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"

    server_params = StdioServerParameters(
        command="python",
        args=["jira_mcp.py"],
        env=my_env
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # YENİ PROMPT: Artık sohbet edebiliyor ve eksik bilgileri sorabiliyor!
            prompt = f"""
            Sen Jira üzerinde yetkili bir Proje Yöneticisi Yapay Zekasısın.
            Gelen Mesaj: '{kullanici_mesaji}'

            YETENEKLER:
            1. bilet_olustur (Parametreler: proje_kodu, baslik, aciklama, oncelik(SADECE: Highest, High, Medium, Low veya Lowest yaz), etiket)
            2. bilet_guncelle (Parametreler: bilet_kodu, oncelik, etiket)
            3. bilet_durumunu_guncelle (Parametreler: bilet_kodu, yeni_durum)
            4. sohbet_et (Eğer kullanıcının isteği eksikse, proje kodu yoksa, ne yapacağını anlamadıysan veya sana sadece selam veriyorsa bu aleti seç. Parametreler: cevap_mesaji)

            Bana SADECE şu JSON formatında cevap ver, markdown kullanma:
            {{
                "kullanilacak_alet": "secilen_aletin_adi",
                "parametreler": {{
                    "parametre_adi": "deger"
                }}
            }}
            """

            cevap = gemini_client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt
            )

            temiz = cevap.text.strip()
            if temiz.startswith("```json"):
                temiz = temiz[7:-3].strip()
            elif temiz.startswith("```"):
                temiz = temiz[3:-3].strip()

            try:
                karar = json.loads(temiz)
            except:
                return "Yapay zeka bir hata yaptı, lütfen tekrar dener misin?"

            alet_adi = karar.get("kullanilacak_alet")
            parametreler = karar.get("parametreler", {})

            print(f"Ajan Kararı: {alet_adi} -> {parametreler}")

            # EĞER EKSİK BİLGİ VARSA VEYA SOHBET EDİYORSA JİRA'YA GİTME, DİREKT CEVAP VER:
            if alet_adi == "sohbet_et":
                return parametreler.get("cevap_mesaji", "Nasıl yardımcı olabilirim?")

            # DİĞER DURUMLARDA JİRA MCP'Yİ ÇALIŞTIR
            try:
                sonuc = await session.call_tool(alet_adi, arguments=parametreler)
                return sonuc.content[0].text
            except Exception as e:
                return f"Jira aracı çalıştırılamadı. Hata: {str(e)}"


# YENİ YAPI: İşlemi arka plana atarak Slack'in 3 saniye kuralını (panik atak krizini) aşıyoruz!
async def arka_planda_islem_yap(event, say):
    raw_text = event.get('text', '')
    kullanici = event.get('user')
    temiz_mesaj = re.sub(r'<@.*?>', '', raw_text).strip()
    
    print(f"\nSlack'ten gelen talimat: {temiz_mesaj}")
    await say(f"İsteğini aldım <@{kullanici}>, hemen ilgileniyorum... ⏳")

    try:
        jira_cevabi = await jira_islemini_yap(temiz_mesaj)
        await say(f"İşlem Sonucu: \n{jira_cevabi}")
    except Exception as e:
        print(f"Hata: {str(e)}")
        await say(f"Bir sorun çıktı: {str(e)}")

@slack_app.event("app_mention")
async def handle_mention(event, say):
    # Slack'e anında "tamam" deyip görevi arka plana yolluyoruz (Tekrarlayan mesajları çözer)
    asyncio.create_task(arka_planda_islem_yap(event, say))


async def main():
    print("Süper Akıllı Jira AI Ajanı Devrede! (Timeout korumalı)")
    handler = AsyncSocketModeHandler(slack_app, os.getenv("SLACK_APP_TOKEN"))
    await handler.start_async()

if __name__ == "__main__":
    asyncio.run(main())