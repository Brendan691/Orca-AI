"""文件上传 API"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user, require_user
from ..models.document import DocumentTags, FileUploadResponse
from ..models.user import User
from ..services.document_processor import document_processor
from ..services.embedding_service import embedding_service
from ..services.file_service import file_service
from ..services.tag_classifier import tag_classifier
from ..services.chroma_store import chroma_store

router = APIRouter(prefix="/api/files", tags=["文件上传"])

MAX_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    if not file_service.is_supported(file.filename):
        raise HTTPException(400, f"不支持的文件格式: {file.filename}。支持的格式: PDF/Word/PPT/Excel/MP3/图片/TXT")

    # 读取文件
    content_bytes = await file.read()
    if len(content_bytes) > MAX_SIZE:
        raise HTTPException(400, f"文件超过大小限制 ({MAX_SIZE // 1024 // 1024}MB)")

    # 上传到 MinIO
    object_name = file_service.upload_file(content_bytes, file.filename, file.content_type or "application/octet-stream")

    # 解析文件为文本
    markdown_text, plain_text = file_service.parse_to_markdown(content_bytes, file.filename)

    if not plain_text or plain_text.startswith("[无法解析"):
        file_service.delete_file(object_name)
        raise HTTPException(400, f"无法解析文件内容: {plain_text}")

    # 文本切片
    full_text, chunks = document_processor.process_text(plain_text, file.filename)

    # 标签分类
    tags = tag_classifier.classify(full_text, use_llm=True)

    # 向量化 & 存入 Chroma
    chunk_texts = [c.content for c in chunks]
    embeddings = embedding_service.embed_batch(chunk_texts)
    doc_id = document_processor.generate_doc_id(content=plain_text[:100])

    metadata = {
        "title": file.filename,
        "url": "",
        "source_type": "file",
        "created_at": datetime.now().isoformat(),
        "tags": {
            "business_type": tags.business_type,
            "geographic_region": tags.geographic_region,
            "topic_category": tags.topic_category,
            "event_nature": tags.event_nature,
        },
    }

    chroma_store.add_document(doc_id=doc_id, chunks=chunk_texts, embeddings=embeddings, metadata=metadata)

    # 存入 PostgreSQL 记录
    from ..models.document import Document
    doc_record = Document(
        title=file.filename,
        content_preview=plain_text[:500],
        source_type="file",
        file_path=object_name,
        file_size=len(content_bytes),
        chroma_doc_id=doc_id,
        user_id=user.id if user else None,
    )
    db.add(doc_record)
    await db.commit()

    return FileUploadResponse(
        success=True,
        file_id=doc_record.id,
        filename=file.filename,
        message=f"文件《{file.filename}》上传解析成功，共{len(chunks)}个切片",
        doc_id=doc_id,
        tags=tags,
    )


@router.get("/{file_id}/download")
async def download_file(file_id: str, db: AsyncSession = Depends(get_db)):
    from ..models.document import Document
    from sqlalchemy import select
    result = await db.execute(select(Document).where(Document.id == file_id))
    doc = result.scalar_one_or_none()
    if not doc or not doc.file_path:
        raise HTTPException(404, "文件不存在")

    url = file_service.get_file_url(doc.file_path)
    return {"url": url, "filename": doc.title}
