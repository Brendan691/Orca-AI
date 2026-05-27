# ============================================================
# 文件：Dockerfile
# 作用：将小鲸 OrcaAI 后端打包成 Docker 镜像
# 用法：docker build -t orcaai .
# 依赖：项目根目录需要有 backend/ 文件夹
# ============================================================
FROM python:3.11-slim

LABEL name="小鲸OrcaAI" \
      version="0.1.0" \
      description="AI驱动的一站式海事知识管理工具"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY backend/ backend/

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
