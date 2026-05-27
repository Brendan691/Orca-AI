"""文件上传与多模态解析服务 — PDF/Word/PPT/MP3 → Markdown → 索引"""
import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional

from minio import Minio
from minio.error import S3Error

from ..core.config import settings


class FileService:
    """MinIO 文件存储 + 多格式解析"""

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
        ".txt", ".md", ".csv", ".json", ".xml",
        ".mp3", ".wav", ".m4a", ".ogg",
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
    }

    def __init__(self):
        self._client: Optional[Minio] = None
        self.bucket = settings.S3_BUCKET

    @property
    def client(self) -> Minio:
        if self._client is None:
            endpoint = settings.S3_ENDPOINT
            self._client = Minio(
                endpoint,
                access_key=settings.S3_ACCESS_KEY_ID,
                secret_key=settings.S3_SECRET_ACCESS_KEY,
                secure=settings.S3_SECURE,
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_file(self, file_data: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
        """上传文件到 MinIO，返回 object_name"""
        ext = Path(filename).suffix.lower()
        object_name = f"{uuid.uuid4().hex}{ext}"
        import io
        self.client.put_object(
            self.bucket, object_name,
            io.BytesIO(file_data), len(file_data),
            content_type=content_type,
        )
        return object_name

    def download_file(self, object_name: str) -> bytes:
        """从 MinIO 下载文件"""
        response = self.client.get_object(self.bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete_file(self, object_name: str):
        """删除 MinIO 文件"""
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error:
            pass

    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """生成预签名 URL"""
        return self.client.presigned_get_object(self.bucket, object_name, expires=timedelta(seconds=expires))

    def parse_to_markdown(self, file_data: bytes, filename: str) -> tuple[str, str]:
        """解析文件为 Markdown 文本。
        使用 markitdown (微软开源) 统一解析 PDF/Word/PPT/Excel/图片等。

        Returns:
            (markdown_text, plain_text)
        """
        ext = Path(filename).suffix.lower()

        # MP3 音频 → 需要先用 whisper 转文字（这里先返回提示）
        if ext in (".mp3", ".wav", ".m4a", ".ogg"):
            return self._parse_audio(file_data, filename)

        # 纯文本系列直接读取
        if ext in (".txt", ".md", ".csv", ".json", ".xml"):
            text = file_data.decode("utf-8", errors="replace")
            return text, text

        # 其他格式使用 markitdown
        try:
            from markitdown import MarkItDown
            md = MarkItDown()
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_data)
                tmp_path = tmp.name

            result = md.convert(tmp_path)
            os.unlink(tmp_path)
            markdown_text = result.text_content
            # 提取纯文本（去除 markdown 标记）
            plain_text = self._strip_markdown(markdown_text)
            return markdown_text, plain_text
        except ImportError:
            return self._fallback_parse(file_data, ext)

    def _parse_audio(self, file_data: bytes, filename: str) -> tuple[str, str]:
        """音频文件解析 — 需要 OpenAI Whisper API"""
        return (
            f"[音频文件: {filename}]\n\n语音转文字功能需要配置 OpenAI Whisper API。",
            f"[音频文件: {filename}]"
        )

    def _fallback_parse(self, file_data: bytes, ext: str) -> tuple[str, str]:
        """回退解析方案（无 markitdown 时）"""
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                import io
                reader = PdfReader(io.BytesIO(file_data))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text, text
            except Exception:
                pass
        elif ext in (".docx", ".doc"):
            try:
                from docx import Document
                import io
                doc = Document(io.BytesIO(file_data))
                text = "\n".join(p.text for p in doc.paragraphs)
                return text, text
            except Exception:
                pass
        return f"[无法解析的文件: {ext}]", f"[无法解析的文件: {ext}]"

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """简单去除 Markdown 标记，保留纯文本"""
        import re
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*{1,3}(.+?)\*{1,3}', r'\1', text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)
        text = re.sub(r'[|>\-]', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def is_supported(filename: str) -> bool:
        ext = Path(filename).suffix.lower()
        return ext in FileService.SUPPORTED_EXTENSIONS


file_service = FileService()
