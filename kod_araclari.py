import os

DOSYA_YOLU = "index.html"

def kodu_oku():
    """index.html dosyasının içindeki mevcut kodu okur."""
    try:
        with open(DOSYA_YOLU, "r", encoding="utf-8") as dosya:
            return dosya.read()
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return None

def kodu_yaz(yeni_kod):
    """index.html dosyasının içindeki kodu silip, yapay zekanın ürettiği yeni kodu yazar."""
    try:
        with open(DOSYA_YOLU, "w", encoding="utf-8") as dosya:
            dosya.write(yeni_kod)
        print("✅ index.html başarıyla güncellendi (Yeni kod yazıldı)!")
        return True
    except Exception as e:
        print(f"❌ Dosya yazma hatası: {e}")
        return False