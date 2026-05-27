"""pytest 共享配置"""
import os
import sys
from pathlib import Path

# 将 backend 目录加入 Python 路径
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# 测试时不调用真实 LLM，使用规则引擎
os.environ.setdefault("DASHSCOPE_API_KEY", "")
