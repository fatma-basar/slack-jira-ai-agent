import os
from google import genai
from dotenv import load_dotenv

# 1. Şifreleri yükle
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    print("❌ HATA: GEMINI_API_KEY bulunamadı.")
    exit()

print("Gemini'ye (Yeni 3.5 Flash Modeli) bağlanılıyor...")

try:
    client = genai.Client(api_key=gemini_api_key)

    # 3. Test mesajı gönder (Listenden seçtiğimiz güncel model)
    cevap = client.models.generate_content(
        model='gemini-3.5-flash',
        contents="Merhaba Gemini! Sen benim Slack-Jira ajanımın beyni olacaksın. Kısa ve heyecanlı bir cevap ver, hazır mısın?"
    )
    
    print("\n🎉 TEBRİKLER! Gemini'den cevap geldi:")
    print("-" * 40)
    print(cevap.text)
    print("-" * 40)
    
except Exception as hata:
    print(f"❌ Bağlantı sırasında hata oluştu: {hata}")