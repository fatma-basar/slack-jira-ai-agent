import os
from dotenv import load_dotenv
from jira import JIRA

# 1. .env dosyasindaki gizli sifreleri yukle
load_dotenv()

jira_server = os.getenv("JIRA_SERVER")
jira_email = os.getenv("JIRA_EMAIL")
jira_api_token = os.getenv("JIRA_API_TOKEN")

print("Jira'ya baglaniliyor...")

# 2. Jira'ya baglanmayi dene
try:
    jira_baglantisi = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))
    print(" TEBRIKLER! Jira'ya basariyla baglandik!")
    
    # 3. Hesaptaki projeleri bul ve ekrana yazdir
    projeler = jira_baglantisi.projects()
    for proje in projeler:
        print(f" Bulunan Proje: {proje.name} (Anahtar: {proje.key})")

except Exception as hata:
    print(" Baglanti sirasinda bir hata olustu:")
    print(hata)