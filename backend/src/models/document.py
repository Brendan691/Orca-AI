"""文档数据模型"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """文档切片"""
    chunk_id: str = Field(..., description="切片唯一ID")
    content: str = Field(..., description="切片内容")
    start_idx: int = Field(..., description="在原文档中的起始位置")
    end_idx: int = Field(..., description="在原文档中的结束位置")


class DocumentTags(BaseModel):
    """文档标签"""
    business_type: List[str] = Field(default=[], description="业务类型")
    geographic_region: List[str] = Field(default=[], description="地理区域")
    topic_category: List[str] = Field(default=[], description="主题类别")
    event_nature: List[str] = Field(default=[], description="事件性质")
    confidence: float = Field(default=0.0, description="分类置信度")


class MaritimeDocument(BaseModel):
    """海事文档模型"""
    doc_id: str = Field(..., description="文档唯一ID")
    title: str = Field(..., description="文档标题")
    url: Optional[str] = Field(default=None, description="来源URL")
    source_type: str = Field(default="web", description="来源类型: web/pdf/text")
    content: str = Field(..., description="文档全文")
    summary: str = Field(default="", description="内容摘要")
    tags: DocumentTags = Field(default_factory=DocumentTags)
    chunks: List[DocumentChunk] = Field(default=[], description="文本切片")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色: user/assistant")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    doc_filter: Optional[List[str]] = Field(default=None, description="按文档ID筛选")
    tag_filter: Optional[DocumentTags] = Field(default=None, description="按标签筛选")


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str = Field(..., description="AI回答")
    sources: List[dict] = Field(default=[], description="引用的来源文档")
    confidence: float = Field(default=0.0, description="回答置信度")


class SearchResult(BaseModel):
    """搜索结果"""
    doc_id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="匹配内容片段")
    score: float = Field(..., description="综合得分")
    vector_score: float = Field(default=0.0, description="向量相似度得分")
    keyword_score: float = Field(default=0.0, description="关键词匹配得分")
    time_score: float = Field(default=0.0, description="时间衰减得分")
    tag_score: float = Field(default=0.0, description="标签匹配得分")
    tags: DocumentTags = Field(default_factory=DocumentTags)


class UploadRequest(BaseModel):
    """上传请求"""
    url: Optional[str] = Field(default=None, description="网页URL")
    content: Optional[str] = Field(default=None, description="直接文本内容")
    title: Optional[str] = Field(default=None, description="标题")


class UploadResponse(BaseModel):
    """上传响应"""
    success: bool = Field(..., description="是否成功")
    doc_id: Optional[str] = Field(default=None, description="文档ID")
    message: str = Field(..., description="状态信息")
    tags: Optional[DocumentTags] = Field(default=None, description="自动标签")
