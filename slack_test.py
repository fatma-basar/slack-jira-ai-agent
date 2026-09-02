import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# .env dosyasındaki şifreleri oku
load_dotenv()

# Botumuzu xoxb- şifresiyle ayağa kaldırıyoruz
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

# 1. BİRİ BOTA @ İLE SESLENDİĞİNDE (app_mention) ÇALIŞACAK KISIM
@app.event("app_mention")
def etiket_dinleyici(event, say):
    kullanici = event['user']
    gelen_metin = event['text']
    
    print(f" BİRİ BANA SESLENDİ: {gelen_metin}")
    say(f"Merhaba <@{kullanici}>! Etiketini gördüm, seni net bir şekilde duyuyorum! 🤖")

# 2. KANALA NORMAL MESAJ YAZILDIĞINDA ÇALIŞACAK KISIM
@app.message(".*")
def mesaj_dinleyici(message, say):
    # Botun kendi mesajlarına sonsuz döngüde cevap vermesini engelliyoruz
    if "bot_id" not in message:
        gelen_metin = message.get('text', '')
        print(f" KANALDA KONUŞULDU: {gelen_metin}")
        say(f"Kanala bir şey yazdın, bunu da duydum: '{gelen_metin}'")

if __name__ == "__main__":
    print(" Slack Botu ayağa kalktı ve kanalları dinlemeye başladı...")
    # xapp- şifresiyle canlı bağlantıyı (Socket Mode) başlatıyoruz
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()