import asyncio
import os
import sys
import codecs
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = FastAPI()

async def mcp_ile_guncelle(alet_adi, parametreler):
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
        return f"Hata: {str(e)}"

async def gorevi_detaylandir_ve_jiraya_yaz(bilet_kodu: str, kisa_baslik: str):
    print(f"\n--- YENI GOREV YAKALANDI: [{bilet_kodu}] ---")
    print(f"Baslik: '{kisa_baslik}' - Yapay zeka analizine baslaniyor...")

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
        chat = gemini_client.chats.create(model='gemini-3.5-flash')
        cevap = chat.send_message(prompt)
        detayli_aciklama = cevap.text.strip()
        
        print(f"[{bilet_kodu}] Yapay zeka ciktisi uretildi. Jira'ya yaziliyor...")
        
        parametreler = {
            "path": f"/rest/api/2/issue/{bilet_kodu}",
            "body": {
                "fields": {
                    "description": detayli_aciklama
                }
            }
        }
        
        sonuc = await mcp_ile_guncelle("jira_put", parametreler)
        print(f"[{bilet_kodu}] ISLEM TAMAMLANDI! Sonuc: Basarili.")
    except Exception as e:
        print(f"[{bilet_kodu}] Islem sirasinda hata olustu: {str(e)}")

# JIRA'NIN BIZE VERI GONDERECEGI KAPi (WEBHOOK ENDPOINT)
@app.post("/jira-webhook")
async def jira_tetikleyici(request: Request, background_tasks: BackgroundTasks):
    try:
        veri = await request.json()
        
        # Jira'dan gelen devasa verinin icinden sadece bize lazim olanlari (ID ve Baslik) cimbizliyoruz.
        bilet_kodu = veri.get("issue", {}).get("key")
        kisa_baslik = veri.get("issue", {}).get("fields", {}).get("summary")
        
        # Eger yeni bir gorev acildiysa islemi arka planda baslat
        if bilet_kodu and kisa_baslik:
            background_tasks.add_task(gorevi_detaylandir_ve_jiraya_yaz, bilet_kodu, kisa_baslik)
            return {"mesaj": f"Gorev {bilet_kodu} alindi ve isleniyor."}
        else:
            return {"mesaj": "Gecersiz veya eksik veri."}
            
    except Exception as e:
        return {"hata": str(e)}

if __name__ == "__main__":
    print("--- 2. FAZ: OTOMATIK JIRA DINLEYICISI BASLATILDI ---")
    print("Sistem su an Jira'dan gelecek yeni bilet sinyallerini bekliyor...")
    uvicorn.run(app, host="0.0.0.0", port=8000)