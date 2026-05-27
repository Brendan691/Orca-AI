"""配置管理模块"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Config:
    """应用配置"""

    # 通义千问API配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_BASE_URL = os.getenv(
        "DASHSCOPE_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # 模型配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
    CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen-max")

    # Chroma配置
    CHROMA_PERSIST_DIR = os.getenv(
        "CHROMA_PERSIST_DIR",
        str(PROJECT_ROOT / "chroma_db")
    )

    # 应用配置
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    APP_DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"

    # CORS配置
    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8000"
    ).split(",")

    # 标签配置
    TAGS_CONFIG_PATH = PROJECT_ROOT / "config" / "tags.yaml"

    # 文本切片配置
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    # 检索配置
    TOP_K = 5
    VECTOR_WEIGHT = 0.6
    KEYWORD_WEIGHT = 0.2
    TIME_WEIGHT = 0.1
    TAG_WEIGHT = 0.1


config = Config()
