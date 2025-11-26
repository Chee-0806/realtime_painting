#!/bin/bash
# ArtFlow - 实时AI图像生成应用完整安装脚本
# 一键安装所有依赖（后端 + 前端）

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎨 ArtFlow v1.0.0 完整安装脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否在项目根目录
if [ ! -f "requirements.txt" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}错误: 请在ArtFlow项目根目录运行此脚本${NC}"
    exit 1
fi

# 检测系统环境
echo -e "${BLUE}🔍 检测系统环境...${NC}"
OS_TYPE=$(uname -s)
PYTHON_CMD=""

# 检测Python管理工具
if command -v conda &> /dev/null; then
    PYTHON_CMD="conda"
    echo -e "${GREEN}✓ 检测到 Conda 环境${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}✓ 检测到 Python3${NC}"
else
    echo -e "${RED}错误: 未找到 Python3 或 Conda，请先安装 Python 环境${NC}"
    exit 1
fi

# 检测 Node.js (前端需要)
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠ 警告: 未检测到 Node.js，前端安装可能会失败${NC}"
    echo -e "${CYAN}💡 请访问 https://nodejs.org 安装 Node.js 16+${NC}"
fi

# 1. 创建Python环境（如果使用Conda）
if [ "$PYTHON_CMD" = "conda" ]; then
    ENV_NAME="artflow"
    if ! conda env list | grep -q "^${ENV_NAME} "; then
        echo -e "${BLUE}🐍 创建 Conda 环境: ${ENV_NAME}...${NC}"
        conda create -n ${ENV_NAME} python=3.10 -y
        echo -e "${GREEN}✓ 环境创建完成${NC}"
    else
        echo -e "${YELLOW}环境 ${ENV_NAME} 已存在，跳过创建${NC}"
    fi

    # 激活环境
    echo -e "${BLUE}激活 Conda 环境...${NC}"
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate ${ENV_NAME}
elif [ "$PYTHON_CMD" = "python3" ]; then
    echo -e "${BLUE}使用系统 Python3 环境${NC}"
    # 建议使用虚拟环境
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}建议创建虚拟环境: python3 -m venv venv${NC}"
    fi
fi

# 检查 Python 版本
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python 版本: ${PYTHON_VERSION}${NC}"

# 2. 配置缓存（可选）
if [ -f "./setup_env.sh" ]; then
    echo -e "${BLUE}📁 配置缓存路径...${NC}"
    ./setup_env.sh
    if [ -f "/root/autodl-tmp/activate_cache.sh" ]; then
        source /root/autodl-tmp/activate_cache.sh 2>/dev/null || true
        echo -e "${GREEN}✓ 缓存路径已配置${NC}"
    fi
else
    echo -e "${YELLOW}⚠ setup_env.sh 不存在，跳过缓存配置${NC}"
fi

# 3. 升级 pip 和安装基础工具
echo -e "${BLUE}🔧 升级 pip 和安装基础工具...${NC}"
pip install --upgrade pip setuptools wheel -q

# 4. 安装后端基础依赖
echo -e "${BLUE}🐍 安装后端依赖...${NC}"
echo -e "${CYAN}正在安装基础依赖包...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✓ 后端基础依赖安装完成${NC}"

# 5. 安装 xformers 加速
echo ""
echo -e "${BLUE}⚡ 安装 xformers 内存优化加速...${NC}"
if [ -f "requirements-xformers.txt" ]; then
    pip install -r requirements-xformers.txt
    echo -e "${GREEN}✓ xformers 依赖安装完成${NC}"
else
    echo -e "${YELLOW}requirements-xformers.txt 不存在，尝试直接安装...${NC}"
    pip install "xformers>=0.0.22" || echo -e "${YELLOW}⚠ xformers 安装失败，可能需要从源码编译${NC}"
fi


# 6. 安装前端依赖
echo ""
echo -e "${BLUE}🎨 安装前端依赖...${NC}"

if command -v node &> /dev/null; then
    cd frontend
    echo -e "${CYAN}正在安装 npm 依赖...${NC}"

    # 检查是否有 package-lock.json，如果有优先使用 npm ci
    if [ -f "package-lock.json" ]; then
        npm ci --silent
    else
        npm install --silent
    fi

    echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
    cd ..
else
    echo -e "${RED}❌ Node.js 未安装，跳过前端依赖安装${NC}"
    echo -e "${CYAN}💡 请手动安装 Node.js 后运行: cd frontend && npm install${NC}"
fi

# 7. 创建配置文件（如果不存在）
echo ""
echo -e "${BLUE}⚙️ 检查配置文件...${NC}"

if [ ! -f "app/config.yaml" ]; then
    echo -e "${YELLOW}⚠ 配置文件 app/config.yaml 不存在${NC}"
    if [ -f "app/config.yaml.example" ]; then
        cp app/config.yaml.example app/config.yaml
        echo -e "${GREEN}✓ 已从示例文件创建配置文件${NC}"
    else
        echo -e "${YELLOW}⚠ 请手动创建配置文件 app/config.yaml${NC}"
    fi
else
    echo -e "${GREEN}✓ 配置文件存在${NC}"
fi

# 8. 环境文件检查
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env 文件不存在，从示例文件创建...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ 已创建 .env 文件${NC}"
    fi
else
    echo -e "${GREEN}✓ .env 文件存在${NC}"
fi

# 9. 验证安装
echo ""
echo -e "${BLUE}🔍 验证安装...${NC}"

# 检查后端关键依赖
echo -e "${CYAN}后端依赖检查:${NC}"
python -c "import torch; print('✓ PyTorch:', torch.__version__)" 2>/dev/null || echo -e "${RED}✗ PyTorch 未安装${NC}"
python -c "import diffusers; print('✓ Diffusers:', diffusers.__version__)" 2>/dev/null || echo -e "${RED}✗ Diffusers 未安装${NC}"
python -c "import fastapi; print('✓ FastAPI:', fastapi.__version__)" 2>/dev/null || echo -e "${RED}✗ FastAPI 未安装${NC}"
python -c "import transformers; print('✓ Transformers:', transformers.__version__)" 2>/dev/null || echo -e "${RED}✗ Transformers 未安装${NC}"

# 检查加速库
echo -e "${CYAN}加速库检查:${NC}"
if python -c "import xformers" 2>/dev/null; then
    python -c "import xformers; print('✓ xFormers:', xformers.__version__)"
else
    echo -e "${YELLOW}⚠ xFormers 未安装（不影响基础功能）${NC}"
fi


# 检查前端依赖
echo -e "${CYAN}前端依赖检查:${NC}"
if [ -d "frontend/node_modules" ]; then
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✓ Node.js: ${NODE_VERSION}${NC}"
        echo -e "${GREEN}✓ npm: ${NPM_VERSION}${NC}"

        # 检查关键前端依赖
        cd frontend
        if [ -d "node_modules/svelte" ]; then
            echo -e "${GREEN}✓ Svelte 已安装${NC}"
        fi
        if [ -d "node_modules/@sveltejs" ]; then
            echo -e "${GREEN}✓ SvelteKit 已安装${NC}"
        fi
        if [ -d "node_modules/tailwindcss" ]; then
            echo -e "${GREEN}✓ Tailwind CSS 已安装${NC}"
        fi
        cd ..
    else
        echo -e "${RED}✗ Node.js 未安装${NC}"
    fi
else
    echo -e "${RED}✗ 前端依赖未安装${NC}"
fi

# 10. 安装完成总结
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 ArtFlow 安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📋 安装摘要:${NC}"
echo -e "  • Python 环境: ${PYTHON_VERSION}"
echo -e "  • 后端依赖: 已安装"
echo -e "  • 前端依赖: $([ -d "frontend/node_modules" ] && echo "已安装" || echo "未安装")"
echo -e "  • 加速库: $([ python -c "import xformers" 2>/dev/null ] && echo "xFormers ✓" || echo "xFormers ✗")"
echo ""
echo -e "${BLUE}🚀 下一步操作:${NC}"
echo ""
echo -e "${CYAN}1. 配置检查:${NC}"
echo "   - 检查配置文件: ${YELLOW}app/config.yaml${NC}"
echo "   - 检查环境变量: ${YELLOW}.env${NC}"
echo ""
echo -e "${CYAN}2. 启动服务:${NC}"
echo "   - 完整启动: ${YELLOW}./start.sh${NC}"
echo "   - 仅后端: ${YELLOW}python -m uvicorn app.main:app --host 0.0.0.0 --port 8000${NC}"
echo "   - 仅前端: ${YELLOW}cd frontend && npm run dev${NC}"
echo ""
echo -e "${CYAN}3. 访问应用:${NC}"
echo "   - 前端界面: ${YELLOW}http://localhost:5173${NC}"
echo "   - API文档: ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo -e "${CYAN}4. 更多信息:${NC}"
echo "   - 详细文档: ${YELLOW}README.md${NC}"
echo "   - 问题反馈: ${YELLOW}GitHub Issues${NC}"
echo ""
echo -e "${GREEN}祝您使用愉快！🎨${NC}"

