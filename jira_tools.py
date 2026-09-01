import os
from dotenv import load_dotenv
from jira import JIRA

# 1. Şifreleri yükle ve Jira'ya bağlan
load_dotenv()
jira_server = os.getenv("JIRA_SERVER")
jira_email = os.getenv("JIRA_EMAIL")
jira_api_token = os.getenv("JIRA_API_TOKEN")

jira_baglantisi = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))

# 2. Yapay zekanın kullanacağı alet (Fonksiyon)
def bilet_olustur(proje_anahtari, baslik, aciklama, bilet_tipi="Task"):
    """
    Jira'da otomatik olarak yeni bir görev (task) oluşturur.
    """
    try:
        yeni_bilet_verisi = {
            'project': {'key': proje_anahtari},
            'summary': baslik,
            'description': aciklama,
            'issuetype': {'name': bilet_tipi},
        }
        
        yeni_bilet = jira_baglantisi.create_issue(fields=yeni_bilet_verisi)
        
        print(f"✅ Bilet başarıyla oluşturuldu! Kodu: {yeni_bilet.key}")
        print(f" Tıklayıp görebilirsin: {jira_server}/browse/{yeni_bilet.key}")
        return yeni_bilet
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        return None

# 3. Dosyayı doğrudan çalıştırırsak bir test bileti açsın
if __name__ == "__main__":
    print("test ediliyor...")
    
    # Slack olmadan kendi kendimize test ediyoruz
    TEST_PROJE = "SCRUM"
    TEST_BASLIK = " AI Ajan Test Bileti 1"
    TEST_ACIKLAMA = "Bu bilet, yapay zeka alet çantası kodlanırken terminal üzerinden saniyeler içinde otomatik olarak açılmıştır!"
    
    bilet_olustur(TEST_PROJE, TEST_BASLIK, TEST_ACIKLAMA)