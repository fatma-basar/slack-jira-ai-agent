from mcp.server.mcpserver import MCPServer

# 1. MCP Sunucumuzu (Evrensel Prizimizi) oluşturuyoruz. (FastMCP yerine MCPServer oldu)
mcp = MCPServer("Jira MCP Sunucusu")

# 2. Yetenekleri (Tools) Tanımlıyoruz
@mcp.tool()
def bilet_olustur(proje_kodu: str, baslik: str, aciklama: str) -> str:
    """Yeni bir Jira bileti açar. Kullanıcı bir hata bildirdiğinde veya görev istediğinde bunu kullan."""
    
    return f" SİMÜLASYON BAŞARILI: {proje_kodu} projesinde '{baslik}' bileti açıldı!"


@mcp.tool()
def bilet_durumunu_guncelle(bilet_kodu: str, yeni_durum: str) -> str:
    """Var olan bir biletin durumunu (To Do, In Progress, Done) değiştirir."""
    
    return f" SİMÜLASYON BAŞARILI: {bilet_kodu} numaralı görev '{yeni_durum}' aşamasına taşındı!"


@mcp.tool()
def proje_biletlerini_listele(proje_kodu: str) -> str:
    """Bir projedeki açık olan tüm görevleri listeler."""
    
    return f" SİMÜLASYON BAŞARILI: {proje_kodu} projesindeki biletler okundu."

if __name__ == "__main__":
    print(" Jira MCP Sunucusu başlatılıyor... Prizi taktık!")
    # Sunucuyu standart giriş/çıkış (stdio) üzerinden dinlemeye alıyoruz
    mcp.run()