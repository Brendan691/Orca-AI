#!/bin/bash
# ============================================================
# 小鲸 OrcaAI v0.2.0 — 一键启动全部服务
# 用法：
#   bash run.sh          → 启动全部服务
#   bash run.sh stop     → 停止全部服务
#   bash run.sh status   → 查看运行状态
#   bash run.sh dev      → 本地开发模式（仅后端 + Web）
# ============================================================

set -e
cd "$(dirname "$0")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

banner() {
  echo ""
  echo -e "${BLUE}  🐳  小鲸 OrcaAI v0.2.0${NC}"
  echo -e "${CYAN}  AI 驱动的一站式海事知识管理工具${NC}"
  echo ""
}

CMD="${1:-start}"

if [ "$CMD" = "stop" ]; then
  echo -e "${YELLOW}正在停止所有服务...${NC}"
  docker compose down 2>/dev/null || true
  pkill -f "uvicorn src.main:app" 2>/dev/null || true
  pkill -f "streamlit run admin/app.py" 2>/dev/null || true
  pkill -f "next dev" 2>/dev/null || true
  echo -e "${GREEN}✅ 已停止${NC}"
  exit 0
fi

if [ "$CMD" = "status" ]; then
  echo -e "${BLUE}服务状态：${NC}"
  echo ""
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  🟢 后端 API    — http://localhost:8000"
  else
    echo -e "  🔴 后端 API    — 未运行"
  fi
  if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "  🟢 Web 前端    — http://localhost:3000"
  else
    echo -e "  🔴 Web 前端    — 未运行"
  fi
  if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo -e "  🟢 管理后台    — http://localhost:8501"
  else
    echo -e "  🔴 管理后台    — 未运行"
  fi
  exit 0
fi

banner

# 确保 .env 存在
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}📋 首次运行，配置环境...${NC}"
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  请编辑 .env 文件，填入你的 API Key 和密钥${NC}"
    echo -e "${YELLOW}   然后重新运行 bash run.sh${NC}"
    exit 1
  fi
fi

# 生成图标
if [ ! -f "extension/icons/icon16.png" ]; then
  python3 extension/icons/generate_icons.py 2>/dev/null || true
fi

# Docker 模式
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
  echo -e "${BLUE}🐋 Docker 模式启动全部服务...${NC}"
  echo ""
  docker compose up -d --build
  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  🎉 小鲸 OrcaAI 已启动！${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""
  echo -e "  📡 后端 API：  ${BLUE}http://localhost:8000${NC}"
  echo -e "  🌐 Web 前端：  ${BLUE}http://localhost:3000${NC}"
  echo -e "  📊 管理后台：  ${BLUE}http://localhost:8501${NC}"
  echo -e "  📖 API 文档：  ${BLUE}http://localhost:8000/docs${NC}"
  echo -e "  🔍 搜索面板：  ${BLUE}http://localhost:7700${NC}"
  echo -e "  🗄️  MinIO：    ${BLUE}http://localhost:9001${NC}"
  echo ""
  echo -e "  停止服务：    ${YELLOW}bash run.sh stop${NC}"
  echo -e "  查看状态：    ${YELLOW}bash run.sh status${NC}"
  echo ""
else
  # 本地 Python 模式
  echo -e "${BLUE}🐍 Python 本地模式...${NC}"

  if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3。请安装 Python 3.10+ 或 Docker。${NC}"
    exit 1
  fi

  if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
    python3 -m venv .venv
  fi

  source .venv/bin/activate

  if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}📥 安装依赖...${NC}"
    pip install -r backend/requirements.txt -q
  fi

  echo -e "${BLUE}🚀 启动后端...${NC}"
  cd backend
  nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/orcaai-backend.log 2>&1 &
  cd ..

  echo -e "${BLUE}🚀 启动管理后台...${NC}"
  nohup python3 -m streamlit run admin/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false > /tmp/orcaai-admin.log 2>&1 &

  sleep 3

  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  🎉 小鲸 OrcaAI 已启动！${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""
  echo -e "  📡 后端 API：  ${BLUE}http://localhost:8000${NC}"
  echo -e "  📊 管理后台：  ${BLUE}http://localhost:8501${NC}"
  echo -e "  📖 API 文档：  ${BLUE}http://localhost:8000/docs${NC}"
  echo ""
  echo -e "  停止服务：    ${YELLOW}bash run.sh stop${NC}"
  echo ""

  if command -v open &> /dev/null; then
    sleep 1
    open http://localhost:8501 2>/dev/null || true
  fi

  deactivate 2>/dev/null || true
fi
