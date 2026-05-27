#!/bin/bash
# ============================================================
# 文件：backend/run.sh
# 作用：一键启动小鲸 OrcaAI 后端服务
# 用法：
#   bash run.sh        → 启动后端（前台运行，Ctrl+C 停止）
#   bash run.sh -d     → 后台运行
# ============================================================

set -e

# 进入脚本所在目录
cd "$(dirname "$0")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  🐳  小鲸 OrcaAI 启动中..."
echo "  ========================="
echo -e "${NC}"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠  未找到 .env 文件，正在从模板创建...${NC}"
    cp .env.example .env 2>/dev/null || true
    echo -e "${RED}❌ 请先编辑 .env 文件，填入你的 DASHSCOPE_API_KEY${NC}"
    echo -e "   用法：打开 backend/.env，将 your_dashscope_api_key_here 替换为你的真实 API Key"
    echo -e "   获取 Key：https://dashscope.console.aliyun.com/"
    exit 1
fi

# 检查 API Key 是否已填写
if grep -q "your_dashscope_api_key_here" .env 2>/dev/null; then
    echo -e "${RED}❌ .env 文件中的 API Key 还未填写！${NC}"
    echo -e "   请打开 backend/.env，将 DASHSCOPE_API_KEY 替换为你的真实 API Key"
    echo -e "   获取 Key：https://dashscope.console.aliyun.com/"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3，请先安装 Python 3.10+${NC}"
    exit 1
fi

# 检查依赖是否安装
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⏳ 正在安装依赖...${NC}"
    pip3 install -r requirements.txt
    echo ""
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"
echo ""
echo -e "  后端地址：    ${BLUE}http://localhost:8000${NC}"
echo -e "  API 文档：    ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  健康检查：    ${BLUE}http://localhost:8000/health${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
echo ""

# 启动
if [ "$1" = "-d" ]; then
    nohup python3 -m uvicorn src.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        > /tmp/orcaai.log 2>&1 &
    echo -e "${GREEN}✅ 已在后台启动！日志文件：/tmp/orcaai.log${NC}"
    echo -e "   查看日志：tail -f /tmp/orcaai.log"
    echo -e "   停止服务：pkill -f 'uvicorn src.main:app'"
else
    python3 -m uvicorn src.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload
fi
