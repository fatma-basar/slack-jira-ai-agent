import asyncio
from mcp_araclari import _mcp_motoru_async

async def test_et():
    print("🚀 MCP Motoru çalıştırılıyor, Jira'ya bilet gönderiliyor...")
    
    parametreler = {
        "path": "/rest/api/2/issue",
        "body": {
            "fields": {
                "project": {"key": "TEAM"},
                "summary": "Sistem Mimarı Test Bileti",
                "description": "Bu bilet sistem testidir.",
                "issuetype": {"name": "Task"}
            }
        }
    }
    
    cevap = await _mcp_motoru_async("jira_post", parametreler)
    
    print("\n📦 İŞTE JIRA'DAN GELEN O GİZEMLİ CEVAP:")
    print("-" * 50)
    print(repr(cevap))  # repr() ile gizli karakterleri de göreceğiz
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_et())