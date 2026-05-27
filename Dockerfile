# ============================================================
# 文件：Dockerfile
# 作用：将小鲸 OrcaAI 打包成 Docker 镜像
# 使用：docker build -t orcaai .（或 bash run.sh 自动执行）
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 复制所有代码
COPY backend/ backend/
COPY admin/ admin/
COPY extension/ extension/

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
