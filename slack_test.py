import os
import asyncio
from dotenv import load_dotenv

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

# 🚀 ai_veri_cikar fonksiyonunu içeri aktardık!
from ajan import ajan_calistir, analist_detay_uret, bilet_eslestir_ai, yazilimci_ai, ai_veri_cikar
from kod_araclari import kodu_oku, kodu_yaz
from mcp_araclari import _mcp_motoru_async

load_dotenv()
app = AsyncApp(token=os.getenv("SLACK_BOT_TOKEN"))

def aktif_projeyi_bul(kanal_id):
    kanal_ayarlari = {"C12345678": "MOBIL"}
    return kanal_ayarlari.get(kanal_id, "TEAM")

@app.message(".*")
async def mesaj_dinleyici(message, say):
    if "bot_id" not in message:
        gelen_metin = message.get('text', '')
        kanal_id = message.get('channel', '')
        print(f"\n👤 KULLANICI YAZDI: {gelen_metin}")
        
        cevap, alet, parametreler = await ajan_calistir(gelen_metin)
        
        if alet == "sessiz_kal":
            print("🤫 Ajan sessiz kalmayı seçti. Slack'e mesaj atılmadı.")
            
        elif alet == "jira_post":
            alanlar = parametreler.get('body', {}).get('fields', {})
            baslik = alanlar.get('summary', 'Yeni Görev')
            
            proje_kodu = aktif_projeyi_bul(kanal_id)
            if 'project' in alanlar:
                alanlar['project']['key'] = proje_kodu
            
            await say(f"⏳ Harika! Jira'da arka planda *'{baslik}'* adıyla {proje_kodu} projesine görevi oluşturuyorum... 🛠️")
            
            mcp_cevap = await _mcp_motoru_async("jira_post", parametreler)
            
            # 🌟 YENİ MİMARİ: Bilet Kodunu AI Buluyor (Spagetti kodlar silindi)
            bilet_kodu = await ai_veri_cikar(mcp_cevap, f"Oluşturulan biletin {proje_kodu} ile başlayan anahtar kodu (key)")
            
            if bilet_kodu:
                jira_server = os.getenv("JIRA_SERVER", "https://basarf13.atlassian.net")
                bilet_linki = f"{jira_server}/browse/{bilet_kodu}"
                await say(f"✅ Görev açıldı: {bilet_kodu}. Şimdi yapay zeka analisti detayları yazıyor... 🧠")
                
                detayli_metin = await analist_detay_uret(baslik)
                
                guncelleme_parametreleri = {
                    "path": f"/rest/api/2/issue/{bilet_kodu}",
                    "body": {"fields": {"description": detayli_metin}}
                }
                await _mcp_motoru_async("jira_put", guncelleme_parametreleri)
                await say(f"🎉 Bilet detayları dolduruldu:\n🔗 {bilet_linki}")
                
                await say("💻 Şimdi klavyeyi elime alıyorum ve senin için 'index.html' dosyasındaki kodu düzeltiyorum...")
                
                mevcut_kod = await kodu_oku()
                if mevcut_kod:
                    yeni_kod = await yazilimci_ai(gelen_metin, mevcut_kod)
                    if yeni_kod:
                        await kodu_yaz(yeni_kod)
                        await say("✨ Veee bitti! Senin klasöründeki `index.html` dosyasını güncelledim. 😎")
                        
                        gecis_param = {"path": f"/rest/api/2/issue/{bilet_kodu}/transitions"}
                        gecisler_cevap = await _mcp_motoru_async("jira_get", gecis_param)
                        
                        # 🌟 YENİ MİMARİ: Kapatma Butonu ID'sini de AI Buluyor (json.loads çökmeleri bitti!)
                        kapatma_id = await ai_veri_cikar(gecisler_cevap, "'Tamamlandı' veya 'Done' ismine sahip durumun id numarası")
                        
                        if kapatma_id:
                            kapatma_param = {
                                "path": f"/rest/api/2/issue/{bilet_kodu}/transitions",
                                "body": {"transition": {"id": kapatma_id}}
                            }
                            await _mcp_motoru_async("jira_post", kapatma_param)
                            await say(f"✅ Görevi kodda tamamladığım için *{bilet_kodu}* biletini otomatik olarak 'Done' yaptım!")
                        else:
                            await say(f"⚠️ Kodu yazdım ama Jira'da kapatma butonu bulamadığım için bilet açık kaldı.")
                            
                    else:
                        await say("⚠️ Kodu yazarken bir sorun oluştu.")
                else:
                    await say("⚠️ index.html dosyasını bulamadım veya okuyamadım.")
            else:
                await say("❌ Görevi Jira'ya kaydederken bir hata oluştu (Bilet numarası okunamadı).")
                
        elif alet == "jira_get":
            await say("🔍 Açık biletlerini çekiyorum, yapay zeka okuyor...")
            
            arama_param = {"path": "/rest/api/2/search?jql=statusCategory != Done"}
            arama_sonucu = await _mcp_motoru_async("jira_get", arama_param)
            
            eslesen_kod = await bilet_eslestir_ai(gelen_metin, arama_sonucu)
            
            if eslesen_kod != "YOK":
                await say(f"🎯 Buldum! Bahsettiğin bilet: *{eslesen_kod}*. Şimdi onu kapatıyorum...")
                
                gecis_param = {"path": f"/rest/api/2/issue/{eslesen_kod}/transitions"}
                gecisler_cevap = await _mcp_motoru_async("jira_get", gecis_param)
                
                # 🌟 YENİ MİMARİ: Arama kısmındaki bilet kapatmada da AI devrede!
                kapatma_id = await ai_veri_cikar(gecisler_cevap, "'Tamamlandı' veya 'Done' ismine sahip durumun id numarası")
                
                if kapatma_id:
                    kapatma_param = {
                        "path": f"/rest/api/2/issue/{eslesen_kod}/transitions",
                        "body": {"transition": {"id": kapatma_id}}
                    }
                    await _mcp_motoru_async("jira_post", kapatma_param)
                    await say(f"🎉 İşlem tamam! *{eslesen_kod}* bileti başarıyla kapatıldı! 😎")
                else:
                    await say("⚠️ Bileti buldum ama kapatma butonu yok.")
            else:
                await say("🤷‍♀️ Yazdığın mesajla eşleşen açık bir görev bulamadım.")
                
        elif alet == "soru_sor":
            await say(cevap)
            
        else:
            if cevap and cevap != "YOK" and cevap != "":
                await say(cevap)

async def ana_program():
    handler = AsyncSocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    await handler.start_async()

if __name__ == "__main__":
    print("🚀 Slack Botu (YENİ AI OKUMA MİMARİSİYLE) ayağa kalktı ve dinlemeye başladı...")
    asyncio.run(ana_program())