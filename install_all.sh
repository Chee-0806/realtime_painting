#!/bin/bash
# StreamDiffusion Backend 完整安装脚本
# 一键安装所有依赖

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}StreamDiffusion Backend 完整安装脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否在项目根目录
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}错误: 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 1. 创建环境（如果不存在）
ENV_NAME="rp"
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${BLUE}创建 Conda 环境: ${ENV_NAME}...${NC}"
    conda create -n ${ENV_NAME} python=3.10 -y
    echo -e "${GREEN}✓ 环境创建完成${NC}"
else
    echo -e "${YELLOW}环境 ${ENV_NAME} 已存在，跳过创建${NC}"
fi

# 2. 激活环境
echo -e "${BLUE}激活 Conda 环境...${NC}"
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate ${ENV_NAME}

# 检查 Python 版本
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python 版本: ${PYTHON_VERSION}${NC}"

# 3. 配置缓存（可选）
if [ -f "./setup_env.sh" ]; then
    echo -e "${BLUE}配置缓存路径...${NC}"
    ./setup_env.sh
    if [ -f "/root/autodl-tmp/activate_cache.sh" ]; then
        source /root/autodl-tmp/activate_cache.sh 2>/dev/null || true
        echo -e "${GREEN}✓ 缓存路径已配置${NC}"
    fi
else
    echo -e "${YELLOW}⚠ setup_env.sh 不存在，跳过缓存配置${NC}"
fi

# 4. 升级 pip
echo -e "${BLUE}升级 pip...${NC}"
pip install --upgrade pip -q

# 5. 安装基础依赖
echo -e "${BLUE}安装基础依赖...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}✓ 基础依赖安装完成${NC}"

       # 7. 询问是否安装 TensorRT 依赖
echo ""
read -p "是否安装 TensorRT 加速依赖？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}安装 TensorRT 依赖（严格按照 StreamDiffusion 的版本）...${NC}"
    
       # 检测 CUDA 版本（严格按照 StreamDiffusion install-tensorrt.py）
           CUDA_VER=$(python -c "import torch; print(torch.version.cuda.split('.')[0])" 2>/dev/null || echo "12")
           echo -e "${BLUE}检测到 CUDA 版本: ${CUDA_VER}${NC}"
           
           if [ "$CUDA_VER" = "12" ]; then
               echo -e "${BLUE}安装 TensorRT 9.0.1.post12.dev4 (CUDA 12)...${NC}"
               # cuDNN 使用 StreamDiffusion install-tensorrt.py 要求的版本
               pip install "nvidia-cudnn-cu12==8.9.4.25" --no-cache-dir
               pip install --pre --extra-index-url https://pypi.nvidia.com "tensorrt==9.0.1.post12.dev4" --no-cache-dir
           elif [ "$CUDA_VER" = "11" ]; then
               echo -e "${BLUE}安装 TensorRT 9.0.1.post11.dev4 (CUDA 11)...${NC}"
               pip install "nvidia-cudnn-cu11==8.9.4.25" --no-cache-dir
               pip install --pre --extra-index-url https://pypi.nvidia.com "tensorrt==9.0.1.post11.dev4" --no-cache-dir
           else
               echo -e "${YELLOW}无法检测 CUDA 版本，使用 CUDA 12 版本${NC}"
               pip install "nvidia-cudnn-cu12==8.9.4.25" --no-cache-dir
               pip install --pre --extra-index-url https://pypi.nvidia.com "tensorrt==9.0.1.post12.dev4" --no-cache-dir
           fi
    
    # 安装其他 TensorRT 依赖
    echo -e "${BLUE}安装其他 TensorRT 依赖...${NC}"
    pip install -r requirements-tensorrt.txt
    
    echo -e "${GREEN}✓ TensorRT 依赖安装完成${NC}"
else
    echo -e "${YELLOW}跳过 TensorRT 依赖安装${NC}"
fi

       # 8. 验证安装
echo ""
echo -e "${BLUE}验证安装...${NC}"

# 检查关键依赖
python -c "import torch; print('✓ PyTorch:', torch.__version__)" 2>/dev/null || echo -e "${RED}✗ PyTorch 未安装${NC}"
python -c "import diffusers; print('✓ Diffusers:', diffusers.__version__)" 2>/dev/null || echo -e "${RED}✗ Diffusers 未安装${NC}"
python -c "import fastapi; print('✓ FastAPI:', fastapi.__version__)" 2>/dev/null || echo -e "${RED}✗ FastAPI 未安装${NC}"

# 检查 TensorRT（如果安装了）
if python -c "import tensorrt" 2>/dev/null; then
    python -c "import tensorrt; print('✓ TensorRT:', tensorrt.__version__)"
    python -c "import onnxscript; print('✓ ONNX Script:', onnxscript.__version__)"
    python -c "import cuda.bindings.runtime as cudart; print('✓ CUDA Python: OK')" 2>/dev/null || echo -e "${YELLOW}⚠ CUDA Python 导入失败${NC}"
else
    echo -e "${YELLOW}⚠ TensorRT 未安装（如果不需要 TensorRT 加速可以忽略）${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}下一步：${NC}"
echo "1. 检查配置文件: ${YELLOW}app/config/config.yaml${NC}"
echo "2. 启动服务: ${YELLOW}./start.sh${NC}"
echo ""
echo -e "${BLUE}详细文档请查看: ${YELLOW}INSTALL.md${NC}"

