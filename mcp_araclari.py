import os
import sys
import codecs
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Şifreleri yükle
load_dotenv()

# Windows'ta Türkçe karakter (UTF-8) çökmesini engellemek için
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

async def _mcp_motoru_async(alet_adi, parametreler):
    """Atlassian MCP sunucusuna asenkron olarak bağlanan ana motor."""
    my_env = os.environ.copy()
    my_env["PYTHONIOENCODING"] = "utf-8"
    
    # Jira site adını URL'den otomatik çıkarma (Örn: basarf13)
    jira_tam_url = os.getenv("JIRA_SERVER", "")
    site_adi = jira_tam_url.replace("https://", "").replace("http://", "").split(".")[0]
    
    my_env["ATLASSIAN_SITE_NAME"] = site_adi
    my_env["ATLASSIAN_USER_EMAIL"] = os.getenv("JIRA_EMAIL", "")
    my_env["ATLASSIAN_API_TOKEN"] = os.getenv("JIRA_API_TOKEN", "")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@aashari/mcp-server-atlassian-jira"],
        env=my_env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                # MCP'ye alet adını (örn: jira_post) ve parametrelerini gönder
                sonuc = await session.call_tool(alet_adi, arguments=parametreler)
                return sonuc.content[0].text
    except Exception as e:
        return f"HATA: {str(e)}"