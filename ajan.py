import asyncio
import os
import sys
import codecs
import json
from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

async def main():
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"

    server_params = StdioServerParameters(
        command="python",
        args=["jira_mcp.py"],
        env=my_env
    )

    print("🔄 Ajan: Sistemler baslatiliyor...\n")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            ai_client = genai.Client(api_key=gemini_api_key)
            
            # KULLANICI MESAJI
            kullanici_mesaji = "TEAM-1 kodlu biletin önceliğini High yapıp Backend etiketini ekler misin? Çok acil!"
            
            print(f"👤 KULLANICI MESAJI: {kullanici_mesaji}\n")
            print("🧠 BEYİN (Gemini): Durumu analiz edip hangi aleti kullanacağına karar veriyor...\n")

            prompt = f"""
            Sen, Atlassian Jira üzerinde tam yetkiye sahip, Agile (Scrum/Kanban) süreçlerine hakim 'Kıdemli Yapay Zeka Yöneticisi'sin.
            Kullanıcıdan gelen mesajı analiz et ve aşağıdaki YETENEKLER LİSTESİ'nden uygun olanı seç.

            YETENEKLER LİSTESİ:
            1. bilet_olustur (Parametreler: proje_kodu, baslik, aciklama) - Yeni iş, görev, bug açılacağı zaman.
            2. bilet_guncelle (Parametreler: bilet_kodu, oncelik, etiket) - Bir biletin önemi (High/Medium/Low) veya alanı (Backend/Web/iOS) değişeceği zaman.
            3. bilet_durumunu_guncelle (Parametreler: bilet_kodu, yeni_durum) - Bir iş 'To Do', 'In Progress' veya 'Done' aşamasına alınacağı zaman.

            KULLANICI MESAJI: '{kullanici_mesaji}'

            Lütfen analizini yap ve bana SADECE aşağıdaki formatta bir JSON döndür. Kodu markdown block (```json) içine ALMA. Sadece süslü parantezlerle başla ve bitir:
            {{
                "kullanilacak_alet": "secilen_aletin_adi",
                "parametreler": {{
                    "parametre_adi": "parametre_değeri"
                }}
            }}
            """
            
            cevap = ai_client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt
            )
            
            try:
                # Gemini bazen inatla başına ```json ekler, onu temizliyoruz
                temiz_cevap = cevap.text.strip()
                if temiz_cevap.startswith("```json"):
                    temiz_cevap = temiz_cevap[7:-3].strip()
                elif temiz_cevap.startswith("```"):
                    temiz_cevap = temiz_cevap[3:-3].strip()

                # 4. JSON'ı Okuma ve Dinamik Alet Çalıştırma
                karar = json.loads(temiz_cevap)
                alet_adi = karar.get("kullanilacak_alet")
                parametreler = karar.get("parametreler", {})
                
                print(f" AJAN KARARI: '{alet_adi}' aleti kullanılacak!")
                print(f"    Parametreler: {parametreler}\n")
                
                result = await session.call_tool(
                    alet_adi,
                    arguments=parametreler
                )
                print(f" JİRA'DAN GELEN CEVAP: {result.content[0].text}")
                
            except json.JSONDecodeError:
                print(f" Gemini düzgün formatta cevap veremedi. Gelen Cevap: \n{cevap.text}")
            except Exception as e:
                print(f" Hata oluştu: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())