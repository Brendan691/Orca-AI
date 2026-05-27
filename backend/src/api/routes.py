"""API路由 - FastAPI路由定义"""
import json
import traceback
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models.document import (
    ChatRequest,
    ChatResponse,
    DocumentTags,
    MaritimeDocument,
    UploadRequest,
    UploadResponse,
)
from ..services.document_processor import document_processor
from ..services.embedding_service import embedding_service
from ..services.tag_classifier import tag_classifier
from ..services.chroma_store import chroma_store
from ..services.rag_service import rag_service

router = APIRouter(prefix="/api", tags=["小鲸OrcaAI API"])


# ========== 文档管理 ==========

class DocumentListResponse(BaseModel):
    documents: List[dict] = Field(default=[], description="文档列表")
    total: int = Field(default=0, description="总数")


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(request: UploadRequest):
    """上传文档（URL或直接文本）"""
    try:
        # 获取内容
        if request.url:
            title, content = document_processor.fetch_webpage(request.url)
            source_type = "web"
            doc_id = document_processor.generate_doc_id(url=request.url)
        elif request.content:
            content = request.content
            title = request.title or "未命名文档"
            source_type = "text"
            doc_id = document_processor.generate_doc_id(content=content)
        else:
            return UploadResponse(
                success=False,
                message="请提供URL或content",
            )

        # 文本切片
        full_text, chunks = document_processor.process_text(content, title)

        # 自动标签分类（使用LLM）
        tags = tag_classifier.classify(full_text, use_llm=True)

        # 向量化
        chunk_texts = [c.content for c in chunks]
        embeddings = embedding_service.embed_batch(chunk_texts)

        # 存入Chroma
        metadata = {
            "title": title,
            "url": request.url or "",
            "source_type": source_type,
            "created_at": datetime.now().isoformat(),
            "tags": {
                "business_type": tags.business_type,
                "geographic_region": tags.geographic_region,
                "topic_category": tags.topic_category,
                "event_nature": tags.event_nature,
            },
        }

        chroma_store.add_document(
            doc_id=doc_id,
            chunks=chunk_texts,
            embeddings=embeddings,
            metadata=metadata,
        )

        return UploadResponse(
            success=True,
            doc_id=doc_id,
            message=f"文档《{title}》上传成功，共{len(chunks)}个切片",
            tags=tags,
        )

    except Exception as e:
        traceback.print_exc()
        return UploadResponse(
            success=False,
            message=f"上传失败: {str(e)}",
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """获取所有文档列表"""
    docs = chroma_store.get_all_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """删除文档"""
    try:
        chroma_store.delete_document(doc_id)
        return {"success": True, "message": f"文档 {doc_id} 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== 知识库问答 ==========

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """知识库问答"""
    try:
        return rag_service.chat(request)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


# ========== 标签体系 ==========

class TagsResponse(BaseModel):
    dimensions: dict = Field(default={}, description="标签维度")


@router.get("/tags", response_model=TagsResponse)
async def get_tags():
    """获取标签体系"""
    import yaml
    from ..core.config import config

    with open(config.TAGS_CONFIG_PATH, "r", encoding="utf-8") as f:
        tag_config = yaml.safe_load(f)

    dimensions = {}
    for dim in tag_config.get("dimensions", []):
        dimensions[dim["name"]] = {
            "display_name": dim["display_name"],
            "values": dim["values"],
        }

    return TagsResponse(dimensions=dimensions)


# ========== 搜索 ==========

class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    top_k: int = Field(default=5, description="返回数量")
    doc_filter: Optional[List[str]] = Field(default=None)
    tag_filter: Optional[DocumentTags] = Field(default=None)


class SearchResponse(BaseModel):
    results: List[dict] = Field(default=[])
    total: int = Field(default=0)


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """混合相似度搜索"""
    try:
        # 查询向量化
        query_embedding = embedding_service.embed_text(request.query)

        # 向量检索
        hits = chroma_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k * 3,
            doc_filter=request.doc_filter,
        )

        if not hits:
            return SearchResponse(results=[], total=0)

        # 混合相似度重排序
        from ..services.hybrid_search import hybrid_search
        from ..models.document import SearchResult

        results = []
        for hit in hits:
            vector_score = hybrid_search.compute_vector_score(hit.get("distance", 0.5))
            keyword_score = hybrid_search.compute_keyword_score(request.query, hit.get("content", ""))
            time_score = hybrid_search.compute_time_score(hit.get("created_at", ""))
            tag_score = hybrid_search.compute_tag_score(
                request.tag_filter,
                hit.get("tags", {}),
            )

            fused = hybrid_search.fuse_scores(vector_score, keyword_score, time_score, tag_score)

            results.append({
                "doc_id": hit.get("doc_id", ""),
                "title": hit.get("title", ""),
                "content": hit.get("content", "")[:300] + "...",
                "url": hit.get("url", ""),
                "score": round(fused, 4),
                "vector_score": round(vector_score, 4),
                "keyword_score": round(keyword_score, 4),
                "time_score": round(time_score, 4),
                "tag_score": round(tag_score, 4),
                "tags": hit.get("tags", {}),
            })

        # 排序并截取
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:request.top_k]

        return SearchResponse(results=results, total=len(results))

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


# ========== 系统状态 ==========

@router.get("/status")
async def get_status():
    """获取系统状态"""
    return {
        "status": "running",
        "document_count": chroma_store.get_document_count(),
        "version": "0.1.0",
        "name": "小鲸OrcaAI",
    }
