#!/bin/bash
# ============================================================
# 文件：run.sh
# 作用：一键启动小鲸 OrcaAI（自动检测环境，零配置）
# 用法：
#   bash run.sh          → 启动全部服务
#   bash run.sh stop     → 停止全部服务
#   bash run.sh status   → 查看运行状态
# ============================================================

set -e
cd "$(dirname "$0")"

# 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

banner() {
  echo ""
  echo -e "${BLUE}  🐳  小鲸 OrcaAI${NC}"
  echo -e "${CYAN}  AI 驱动的一站式海事知识管理工具${NC}"
  echo ""
}

# ============================================================
# 命令：stop / status
# ============================================================
CMD="${1:-start}"

if [ "$CMD" = "stop" ]; then
  echo -e "${YELLOW}正在停止服务...${NC}"
  docker compose down 2>/dev/null || true
  pkill -f "uvicorn src.main:app" 2>/dev/null || true
  pkill -f "streamlit run admin/app.py" 2>/dev/null || true
  echo -e "${GREEN}✅ 已停止${NC}"
  exit 0
fi

if [ "$CMD" = "status" ]; then
  if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}🟢 后端运行中${NC} — http://localhost:8000"
  else
    echo -e "${RED}🔴 后端未运行${NC}"
  fi
  if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo -e "${GREEN}🟢 管理后台运行中${NC} — http://localhost:8501"
  else
    echo -e "${RED}🔴 管理后台未运行${NC}"
  fi
  exit 0
fi

# ============================================================
# 启动流程
# ============================================================
banner

# ---- 第一步：确保 .env 存在 ----
if [ ! -f ".env" ]; then
  echo -e "${YELLOW}📋 首次运行，需要配置 API Key${NC}"
  echo ""

  # 交互式输入 API Key
  read -p "  请输入通义千问 API Key（从 https://dashscope.console.aliyun.com 获取）: " USER_KEY

  if [ -z "$USER_KEY" ]; then
    echo -e "${RED}❌ 未输入 API Key，无法启动${NC}"
    echo "  获取 Key：https://dashscope.console.aliyun.com/"
    exit 1
  fi

  # 写入 .env
  cat > .env << ENVEOF
DASHSCOPE_API_KEY=${USER_KEY}
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v3
CHAT_MODEL=qwen-max
CHROMA_PERSIST_DIR=./chroma_db
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,chrome-extension://*
ENVEOF

  echo -e "${GREEN}✅ .env 配置完成${NC}"
  echo ""
fi

# ---- 第二步：选择启动方式 ----
USE_DOCKER=false
if command -v docker &> /dev/null && docker info &> /dev/null 2>&1; then
  USE_DOCKER=true
fi

if $USE_DOCKER; then
  # ==================== Docker 方式 ====================
  echo -e "${BLUE}🐋 使用 Docker 启动...${NC}"
  echo ""

  # 生成 Chrome 插件图标（如果还没有）
  if [ ! -f "extension/icons/icon16.png" ]; then
    python3 extension/icons/generate_icons.py 2>/dev/null || true
  fi

  docker compose up -d --build

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
  echo -e "  查看状态：    ${YELLOW}bash run.sh status${NC}"
  echo ""

else
  # ==================== Python 本地方式 ====================
  echo -e "${BLUE}🐍 使用 Python 本地启动...${NC}"

  # 检查 Python
  if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3，请安装 Python 3.10+${NC}"
    echo "  https://www.python.org/downloads/"
    echo -e "  或安装 Docker 后重试：${BLUE}bash run.sh${NC}"
    exit 1
  fi

  # 自动创建虚拟环境
  if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
  fi

  # 激活虚拟环境
  source .venv/bin/activate

  # 检查/安装依赖
  if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}📥 安装依赖（首次需等待 2-3 分钟）...${NC}"
    pip install -r backend/requirements.txt -q
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
  fi

  # 生成图标
  if [ ! -f "extension/icons/icon16.png" ]; then
    python3 extension/icons/generate_icons.py 2>/dev/null || true
  fi

  echo ""

  # 启动后端（后台运行）
  echo -e "${BLUE}🚀 启动后端服务...${NC}"
  cd backend
  nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/orcaai-backend.log 2>&1 &
  BACKEND_PID=$!
  cd ..

  # 启动管理后台（后台运行）
  echo -e "${BLUE}🚀 启动管理后台...${NC}"
  nohup python3 -m streamlit run admin/app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false > /tmp/orcaai-admin.log 2>&1 &
  ADMIN_PID=$!

  # 等待启动
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
  echo -e "  📝 后端 PID：  ${BACKEND_PID}（日志: /tmp/orcaai-backend.log）"
  echo -e "  📝 管理 PID：  ${ADMIN_PID}（日志: /tmp/orcaai-admin.log）"
  echo ""
  echo -e "  停止服务：    ${YELLOW}bash run.sh stop${NC}"
  echo -e "  查看状态：    ${YELLOW}bash run.sh status${NC}"
  echo ""

  # 尝试打开浏览器
  if command -v open &> /dev/null; then
    sleep 2
    open http://localhost:8501 2>/dev/null || true
  fi

  deactivate 2>/dev/null || true
fi
