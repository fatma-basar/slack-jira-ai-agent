import os
from dotenv import load_dotenv
from jira import JIRA

# 1. Şifreleri yükle ve Jira'ya bağlan
load_dotenv()
jira_server = os.getenv("JIRA_SERVER")
jira_email = os.getenv("JIRA_EMAIL")
jira_api_token = os.getenv("JIRA_API_TOKEN")

jira_baglantisi = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))

def bilet_olustur(proje_anahtari, baslik, aciklama, bilet_tipi="Task"):
    """ Jira'da otomatik olarak yeni bir görev (task) oluşturur. """
    try:
        yeni_bilet_verisi = {
            'project': {'key': proje_anahtari},
            'summary': baslik,
            'description': aciklama,
            'issuetype': {'name': bilet_tipi},
        }
        
        yeni_bilet = jira_baglantisi.create_issue(fields=yeni_bilet_verisi)
        print(f"✅ Bilet başarıyla oluşturuldu! Kodu: {yeni_bilet.key}")
        return yeni_bilet
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        return None

def bileti_guncelle(bilet_kodu, detayli_aciklama):
    """ Açılmış olan bir biletin açıklamasını (description) günceller. """
    try:
        bilet = jira_baglantisi.issue(bilet_kodu)
        bilet.update(description=detayli_aciklama)
        print(f"✅ [{bilet_kodu}] detayları Jira'ya başarıyla yazıldı!")
        return True
    except Exception as e:
        print(f"❌ Bilet Güncelleme Hatası: {e}")
        return False
def acik_biletleri_getir(proje_kodu="SCRUM"):
    """Jira'daki kapanmamış (açık) biletleri AI'ın okuması için liste halinde getirir."""
    try:
        # Sadece açık olan son 20 bileti getiriyoruz
        jql = f'project = {proje_kodu} AND statusCategory != Done'
        biletler = jira_baglantisi.search_issues(jql, maxResults=20)
        
        # Yapay zekanın okuyabileceği basit bir sözlük (dictionary) listesi oluşturuyoruz
        bilet_listesi = []
        for bilet in biletler:
            bilet_listesi.append({
                "key": bilet.key, 
                "summary": bilet.fields.summary
            })
        return bilet_listesi
    except Exception as e:
        print(f"❌ Açık biletleri çekerken hata: {e}")
        return []
def bileti_kapat(bilet_kodu):
    """Jira'daki bir bileti otomatik bularak 'Done' veya 'Tamamlandı' durumuna çeker."""
    try:
        bilet = jira_baglantisi.issue(bilet_kodu)
        gecisler = jira_baglantisi.transitions(bilet)
        
        kapatma_id = None
        # Jira'nın projedeki kapatma butonunun ID'sini buluyoruz
        for gecis in gecisler:
            isim = gecis['name'].lower()
            if isim in ['done', 'tamamlandı', 'closed', 'kapat','Tamam']:
                kapatma_id = gecis['id']
                break
                
        if kapatma_id:
            jira_baglantisi.transition_issue(bilet, kapatma_id)
            print(f"✅ [{bilet_kodu}] başarıyla kapatıldı!")
            return True
        else:
            print("❌ Kapatma durumu (Done) bulunamadı. Jira Workflow ayarlarını kontrol et.")
            return False
    except Exception as e:
        print(f"❌ Kapatma hatası: {e}")
        return False        