"""联网搜索服务 — 集成 SearXNG 进行互联网搜索"""
from typing import List, Optional

import httpx

from ..core.config import settings


class SearchService:
    """互联网搜索（SearXNG 聚合引擎）"""

    def __init__(self):
        self.base_url = settings.SEARXNG_BASE_URL.rstrip("/")

    async def search(self, query: str, num: int = 5) -> List[dict]:
        """搜索互联网"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "format": "json", "engines": "bing,duckduckgo,google", "limit": num},
                )
                resp.raise_for_status()
                data = resp.json()
                results = []
                for r in data.get("results", [])[:num]:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:500],
                        "engine": r.get("engine", ""),
                    })
                return results
        except Exception:
            return []

    async def search_and_format(self, query: str, num: int = 5) -> str:
        """搜索并格式化为上下文文本"""
        results = await self.search(query, num)
        if not results:
            return ""

        parts = ["\n[互联网搜索结果]\n"]
        for i, r in enumerate(results, 1):
            parts.append(f"[网络结果{i}] {r['title']}\n{r['content']}\n来源: {r['url']}\n")
        return "\n".join(parts)


search_service = SearchService()
