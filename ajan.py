import asyncio
import os
import sys
import codecs
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Windows konsolundaki kodlama hatasini (UnicodeDecodeError) kükten cözmek icin:
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def main():
    # Arka plandaki alt islemin de (jira_mcp.py) UTF-8 kullanmasini zorluyoruz
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"

    # 1. MCP Sunucumuzu perde arkasinda baslatma ayarlari
    server_params = StdioServerParameters(
        command="python",
        args=["jira_mcp.py"],
        env=my_env
    )

    print("Ajan: Jira MCP Sunucusuna baglaniliyor...")
    
    # 2. Sunucuya baglaniyoruz
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Ajan: Sunucuya basariyla baglandi!\n")
            
            # 3. ZEKANIN DEVREYE GIRDIGI YER: Yetenekleri sor
            tools = await session.list_tools()
            print("Jira'dan Gelen Evrensel Yetenekler:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # 4. Aletin Test Edilmesi
            print("\nAjan: Kendi kendine 'bilet_olustur' yetenegini kullaniyor...")
            
            result = await session.call_tool(
                "bilet_olustur",
                arguments={
                    "proje_kodu": "SCRUM",
                    "baslik": "Giris Ekrani Hatasi (Acil)",
                    "aciklama": "Kullanicilar sisteme giris yapamiyor, acil mudahale lazim."
                }
            )
            
            print(f"\nJIRA'DAN GELEN CEVAP: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(main())