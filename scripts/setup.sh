#!/bin/bash
# ============================================================
# 文件：scripts/setup.sh
# 作用：一键初始化项目环境
# 用法：bash scripts/setup.sh
#
# 这个脚本会帮你：
#   1. 检查 Python 是否安装
#   2. 创建虚拟环境（可选）
#   3. 安装所有依赖包
#   4. 创建 .env 配置文件（如果还没有的话）
# ============================================================

set -e

# 进入项目根目录
cd "$(dirname "$0")/.."
PROJECT_DIR=$(pwd)

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  🐳  小鲸 OrcaAI - 项目初始化"
echo "  ============================"
echo -e "${NC}"

# ==========================================
# 1. 检查 Python
# ==========================================
echo -e "${BLUE}[1/4] 检查 Python...${NC}"
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}  ✅ Python $PY_VERSION${NC}"
else
    echo -e "${RED}  ❌ 未找到 python3${NC}"
    echo "  请先安装 Python 3.10+：https://www.python.org/downloads/"
    exit 1
fi

# ==========================================
# 2. 创建 .env 配置文件（如果还没有）
# ==========================================
echo -e "${BLUE}[2/4] 创建 .env 配置...${NC}"
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}  ✅ .env 已存在，跳过${NC}"
else
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}  ⚠️  .env 已从模板创建${NC}"
    echo ""
    echo -e "${RED}  🔑  请务必完成这一步：${NC}"
    echo "      1. 打开 backend/.env 文件"
    echo "      2. 将 DASHSCOPE_API_KEY=your_dashscope_api_key_here"
    echo "         替换为你的真实 API Key"
    echo "      3. 获取 Key：https://dashscope.console.aliyun.com/"
    echo ""
fi

# ==========================================
# 3. 安装依赖
# ==========================================
echo -e "${BLUE}[3/4] 安装 Python 依赖...${NC}"
cd "$PROJECT_DIR/backend"
pip3 install -r requirements.txt
echo -e "${GREEN}  ✅ 依赖安装完成${NC}"

# ==========================================
# 4. 生成 Chrome 插件图标
# ==========================================
echo -e "${BLUE}[4/4] 生成 Chrome 插件图标...${NC}"
cd "$PROJECT_DIR/extension/icons"
python3 generate_icons.py
echo -e "${GREEN}  ✅ 图标生成完成${NC}"

# ==========================================
# 完成
# ==========================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🎉  初始化完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  下一步："
echo "  1. 填写 API Key：编辑 backend/.env"
echo "  2. 启动后端：  bash backend/run.sh"
echo "  3. 管理后台：  streamlit run admin/app.py"
echo "  4. 加载插件：  Chrome → chrome://extensions → 加载 extension/ 文件夹"
echo ""
echo "  有问题？查看 README.md"
echo ""
