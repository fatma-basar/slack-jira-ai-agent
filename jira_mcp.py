import os
import requests
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

# Şifreleri .env dosyasından okuyoruz
load_dotenv()
JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

mcp = MCPServer("Jira MCP Sunucusu")
@mcp.tool()
def bilet_olustur(proje_kodu: str, baslik: str, aciklama: str) -> str:
    """Yeni bir Jira bileti açar. Kullanıcı bir hata bildirdiğinde veya görev istediğinde bunu kullan."""
    try:
        # 1. Şifrelerin gerçekten okunup okunmadığını kontrol ediyoruz
        if not JIRA_URL or not JIRA_EMAIL or not JIRA_API_TOKEN:
            return " HATA: .env dosyasındaki Jira bilgileri okunamadı! Lütfen kontrol et."

        # 2. URL'nin sonundaki fazladan slash '/' işaretini temizliyoruz ki link bozulmasın
        url = f"{JIRA_URL.rstrip('/')}/rest/api/2/issue"
        
        payload = {
            "fields": {
                "project": {"key": proje_kodu},
                "summary": baslik,
                "description": aciklama,
                # Eğer firmanızda "Task" yoksa, hatayı görünce burayı "Bug" yapacağız
                "issuetype": {"name": "Task"} 
            }
        }
        
        response = requests.post(
            url,
            json=payload,
            auth=(JIRA_EMAIL, JIRA_API_TOKEN)
        )
        
        if response.status_code == 201:
            bilet_anahtari = response.json().get("key")
            return f" GERÇEK BAŞARI: Jira'da {bilet_anahtari} kodlu bilet oluşturuldu!"
        else:
            return f" JIRA REDDETTİ: (Kod: {response.status_code}) Detay: {response.text}"
            
    except Exception as e:
        return f" YAZILIM HATASI: Alet çalışırken arka planda şu hata koptu: {str(e)}"

@mcp.tool()
def bilet_guncelle(bilet_kodu: str, oncelik: str = None, etiket: str = None) -> str:
    """Var olan bir biletin önceliğini (High, Medium, Low) veya etiketini (Backend, Web, iOS) günceller."""
    try:
        url = f"{JIRA_URL.rstrip('/')}/rest/api/2/issue/{bilet_kodu}"
        
        # Güncellenecek alanları dinamik olarak hazırlıyoruz
        guncellemeler = {}
        if oncelik:
            # Jira'da öncelikler genelde High, Medium, Low şeklindedir
            guncellemeler["priority"] = [{"set": {"name": oncelik}}]
        if etiket:
            guncellemeler["labels"] = [{"add": etiket}]
            
        payload = {"update": guncellemeler}
        
        response = requests.put(
            url,
            json=payload,
            auth=(JIRA_EMAIL, JIRA_API_TOKEN)
        )
        
        if response.status_code == 204:
            return f" BAŞARILI: {bilet_kodu} kodlu bilet güncellendi! (Öncelik: {oncelik}, Etiket: {etiket})"
        else:
            return f" JIRA REDDETTİ: (Kod: {response.status_code}) Detay: {response.text}"
            
    except Exception as e:
        return f" YAZILIM HATASI: {str(e)}"
@mcp.tool()
def bilet_durumunu_guncelle(bilet_kodu: str, yeni_durum: str) -> str:
    """Var olan bir biletin durumunu (To Do, In Progress, Done) değiştirir."""
    return f"SİMÜLASYON: {bilet_kodu} durumu '{yeni_durum}' aşamasına taşındı."

@mcp.tool()
def proje_biletlerini_listele(proje_kodu: str) -> str:
    """Bir projedeki açık olan tüm görevleri listeler."""
    return f"SİMÜLASYON: {proje_kodu} projesindeki biletler okundu."

if __name__ == "__main__":
    mcp.run()