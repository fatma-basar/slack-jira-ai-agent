import os
import asyncio

DOSYA_YOLU = "index.html"

# --- SENKRON (ARKA PLAN) İŞLEMLERİ ---
def _senkron_oku():
    with open(DOSYA_YOLU, "r", encoding="utf-8") as dosya:
        return dosya.read()

def _senkron_yaz(yeni_kod):
    with open(DOSYA_YOLU, "w", encoding="utf-8") as dosya:
        dosya.write(yeni_kod)

# --- ASENKRON (BOTUN KULLANACAĞI) FONKSİYONLAR ---
async def kodu_oku():
    """index.html dosyasının içindeki mevcut kodu okur (Event Loop'u bloklamadan)."""
    try:
        # İşlemi ana akışı dondurmadan ayrı bir thread'de (iş parçacığında) çalıştırır
        return await asyncio.to_thread(_senkron_oku)
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return None

async def kodu_yaz(yeni_kod):
    """index.html dosyasının içindeki kodu silip, yeni kodu yazar (Event Loop'u bloklamadan)."""
    try:
        await asyncio.to_thread(_senkron_yaz, yeni_kod)
        print("✅ index.html başarıyla güncellendi (Yeni kod asenkron olarak yazıldı)!")
        return True
    except Exception as e:
        print(f"❌ Dosya yazma hatası: {e}")
        return False