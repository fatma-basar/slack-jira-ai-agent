import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# 🧠 BEYİN: Yapay zeka fonksiyonlarımızı içe aktarıyoruz
from ajan import ajan_calistir, analist_detay_uret, bilet_eslestir_ai, yazilimci_ai 
# 🦾 KASLAR: Jira ve Kod işlem fonksiyonlarımızı içe aktarıyoruz
from jira_tools import bilet_olustur, bileti_guncelle, acik_biletleri_getir, bileti_kapat
from kod_araclari import kodu_oku, kodu_yaz

# Şifreleri yükle ve botu başlat
load_dotenv()
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.message(".*")
def mesaj_dinleyici(message, say):
    # Botun kendi kendine cevap vermesini engelliyoruz
    if "bot_id" not in message:
        gelen_metin = message.get('text', '')
        print(f"\n👤 KULLANICI YAZDI: {gelen_metin}")
        
        # 1. BEYİN KARAR VERİYOR (Ajanı çalıştır)
        cevap, alet, parametreler = ajan_calistir(gelen_metin)
        
        # 2. GELEN KARARA GÖRE AKSİYON AL
        if alet == "sessiz_kal":
            print("🤫 Ajan sessiz kalmayı seçti. Slack'e mesaj atılmadı.")
            
        elif alet == "jira_post":
            # --- YENİ BİLET AÇMA VE DETAYLANDIRMA ---
            alanlar = parametreler.get('body', {}).get('fields', {})
            baslik = alanlar.get('summary', 'Yeni Görev')
            aciklama = alanlar.get('description', gelen_metin)
            
            proje_kodu = "SCRUM" 
            say(f"⏳ Harika! Bu teknik bir talep. Jira'da arka planda *'{baslik}'* adıyla görevi oluşturuyorum... 🛠️")
            
            # Adım A: Bileti Kısa Haliyle Oluştur
            yeni_bilet = bilet_olustur(proje_kodu, baslik, aciklama)
            
            if yeni_bilet:
                jira_server = os.getenv("JIRA_SERVER", "https://basarf13.atlassian.net")
                bilet_linki = f"{jira_server}/browse/{yeni_bilet.key}"
                say(f"✅ Görev açıldı: {yeni_bilet.key}. Şimdi yapay zeka analisti arka planda detayları yazıyor, lütfen bekle... 🧠")
                
                # Adım B: Yapay Zeka (Senior Analist) Detayları Üretsin
                detayli_metin = analist_detay_uret(baslik)
                
                # Adım C: Jira'yı Detaylı Metinle Güncelle
                bileti_guncelle(yeni_bilet.key, detayli_metin)
                
                say(f"🎉 Bilet detayları kusursuzca dolduruldu! Linke tıklayarak muazzam analizi görebilirsin:\n🔗 {bilet_linki}")
                
                # --- YENİ EKLENEN AI YAZILIMCI (CODER) KISMI ---
                say("💻 Şimdi klavyeyi elime alıyorum ve senin için 'index.html' dosyasındaki kodu düzeltiyorum...")
                
                mevcut_kod = kodu_oku()
                if mevcut_kod:
                    yeni_kod = yazilimci_ai(gelen_metin, mevcut_kod)
                    if yeni_kod:
                        kodu_yaz(yeni_kod)
                        say("✨ Veee bitti! Senin klasöründeki `index.html` dosyasını güncelledim. Açıp kontrol edebilirsin patron! 😎")
                    else:
                        say("⚠️ Kodu yazarken bir sorun oluştu.")
                else:
                    say("⚠️ index.html dosyasını bulamadım veya okuyamadım.")
                    
            else:
                say("❌ Görevi Jira'ya kaydederken bir hata oluştu. Lütfen botun terminalini kontrol et.")
                
        elif alet == "jira_get":
            # --- JIRA'DA AKILLI ARAMA YAPMA VE BİLET KAPATMA ---
            say("🔍 Açık biletlerini çekiyorum, yapay zeka ne demek istediğini anlamak için okuyor...")
            
            # Adım A: Jira'dan tüm açık biletleri al
            acik_biletler = acik_biletleri_getir("SCRUM")
            
            # Adım B: AI'a kullanıcının mesajını ve biletleri verip anlamsal eşleştirmesini iste
            eslesen_kod = bilet_eslestir_ai(gelen_metin, acik_biletler)
            
            if eslesen_kod != "YOK":
                say(f"🎯 Buldum! Kelime oyunlarına takılmadım, bahsettiğin bilet: *{eslesen_kod}*")
                say(f"✅ Madem düzelttin, *{eslesen_kod}* biletini senin için Jira'da 'Tamamlandı' (Done) yapıyorum...")
                
                # Adım C: Bileti Kapat (Done durumuna al)
                basarili_mi = bileti_kapat(eslesen_kod)
                
                if basarili_mi:
                    say(f"🎉 İşlem tamam! *{eslesen_kod}* bileti başarıyla kapatıldı. Başka bir isteğin var mı patron? 😎")
                else:
                    say("⚠️ Bileti buldum ama kapatırken bir sorun oluştu (Jira izinlerini/workflow durumlarını kontrol et).")
            else:
                say("🤷‍♀️ Açık biletlerini okudum ama yazdığın mesajla eşleşen bir görev bulamadım. Belki de çoktan kapanmıştır?")
                
        elif alet == "soru_sor":
            # Yapay zeka eksik bir bilgi tespit edip soru sormak isterse
            say(cevap)
            
        else:
            # Diğer tüm durumlar
            if cevap and cevap != "YOK" and cevap != "":
                say(cevap)

if __name__ == "__main__":
    print("🚀 Slack Botu (AI Ajanı) ayağa kalktı ve dinlemeye başladı...")
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()