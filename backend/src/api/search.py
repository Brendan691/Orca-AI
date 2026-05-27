"""联网搜索 API"""
from fastapi import APIRouter

from ..services.search_service import search_service

router = APIRouter(prefix="/api/search/internet", tags=["联网搜索"])


@router.get("/")
async def search_internet(q: str = "", num: int = 5):
    """联网搜索"""
    if not q:
        return {"results": [], "total": 0}
    results = await search_service.search(q, num)
    return {"results": results, "total": len(results)}
