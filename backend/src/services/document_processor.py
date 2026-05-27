"""文档处理服务 - URL解析、PDF解析、文本切片"""
import hashlib
import re
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from ..core.config import config
from ..models.document import DocumentChunk


class DocumentProcessor:
    """文档处理器"""

    def __init__(self):
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP

    def fetch_webpage(self, url: str) -> tuple[str, str]:
        """抓取网页内容

        Args:
            url: 网页URL

        Returns:
            (title, content) 元组
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # 提取标题
        title = ""
        if soup.title:
            title = soup.title.string.strip() if soup.title.string else ""

        # 移除不需要的元素
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # 提取正文
        # 优先找 article 或 main 标签
        content_elem = soup.find("article") or soup.find("main")
        if content_elem:
            text = content_elem.get_text(separator="\n", strip=True)
        else:
            # 退而求其次，提取所有段落
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text(strip=True) for p in paragraphs)

        # 清理文本
        text = self._clean_text(text)

        return title, text

    def process_text(self, content: str, title: str = "") -> tuple[str, List[DocumentChunk]]:
        """处理纯文本内容

        Args:
            content: 文本内容
            title: 标题

        Returns:
            (清理后的全文, 切片列表)
        """
        cleaned = self._clean_text(content)
        chunks = self._split_text(cleaned)
        return cleaned, chunks

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r"\s+", " ", text)
        # 移除特殊字符但保留中文标点
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        # 移除过多的换行
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _split_text(self, text: str) -> List[DocumentChunk]:
        """将文本切分为重叠的切片

        使用滑动窗口策略，保证上下文连贯性
        """
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            # 计算当前切片的结束位置
            end = start + self.chunk_size

            if end >= len(text):
                # 最后一片
                chunk_text = text[start:]
            else:
                # 尝试在句子边界处切断
                chunk_text = text[start:end]
                # 向后找最近的句号、问号、感叹号或换行
                for sep in ["\n", "。", "？", "！", ". ", "; "]:
                    last_sep = chunk_text.rfind(sep)
                    if last_sep > self.chunk_size * 0.5:
                        chunk_text = chunk_text[:last_sep + 1]
                        end = start + len(chunk_text)
                        break

            chunk = DocumentChunk(
                chunk_id=f"chunk_{chunk_id}",
                content=chunk_text.strip(),
                start_idx=start,
                end_idx=start + len(chunk_text),
            )
            chunks.append(chunk)

            # 下一个切片的起始位置（考虑重叠）
            start = end - self.chunk_overlap
            chunk_id += 1

            # 避免无限循环
            if len(chunk_text) <= self.chunk_overlap:
                break

        return chunks

    def generate_doc_id(self, url: str = "", content: str = "") -> str:
        """生成文档唯一ID"""
        source = url or content[:100]
        return hashlib.md5(source.encode("utf-8")).hexdigest()[:16]


# 全局实例
document_processor = DocumentProcessor()
