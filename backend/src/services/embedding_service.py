"""向量化服务 - 调用通义千问Embedding API"""
import hashlib
from typing import List

from openai import OpenAI

from ..core.config import config


class EmbeddingService:
    """文本向量化服务"""

    def __init__(self):
        self._client = None
        self.model = config.EMBEDDING_MODEL
        self._dimension = 1024  # text-embedding-v3 输出维度

    @property
    def client(self):
        """延迟创建 OpenAI 客户端（避免无 API Key 时导入失败）"""
        if self._client is None:
            self._client = OpenAI(
                api_key=config.DASHSCOPE_API_KEY,
                base_url=config.DASHSCOPE_BASE_URL,
            )
        return self._client

    def embed_text(self, text: str) -> List[float]:
        """将单条文本转换为向量

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self._dimension,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表的列表
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self._dimension,
        )
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        return self._dimension


# 全局实例
embedding_service = EmbeddingService()
