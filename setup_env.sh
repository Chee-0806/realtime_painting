#!/bin/bash
# 环境配置脚本
# 将缓存和虚拟环境路径指向 /root/autodl-tmp 数据盘

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}环境配置脚本${NC}"
echo -e "${GREEN}将缓存和虚拟环境指向数据盘${NC}"
echo -e "${GREEN}========================================${NC}"

# 数据盘路径
DATA_DIR="/root/autodl-tmp"
CACHE_DIR="${DATA_DIR}/cache"
ENV_DIR="${DATA_DIR}/conda-envs"

# 创建必要的目录
echo -e "${BLUE}创建缓存目录...${NC}"
mkdir -p "${CACHE_DIR}/pip"
mkdir -p "${CACHE_DIR}/huggingface"
mkdir -p "${CACHE_DIR}/torch"
mkdir -p "${CACHE_DIR}/transformers"
mkdir -p "${ENV_DIR}"

echo -e "${GREEN}✓ 目录创建完成${NC}"

# 生成环境变量配置文件
ENV_FILE="${DATA_DIR}/.env_cache"
cat > "${ENV_FILE}" << 'EOF'
# 环境变量配置 - 缓存和虚拟环境路径
# 此文件由 setup_env.sh 生成，请勿手动修改

# Python 相关
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="${AUTODL_CACHE_DIR}/python"

# pip 缓存
export PIP_CACHE_DIR="${AUTODL_CACHE_DIR}/pip"

# Hugging Face 缓存（模型下载）
export HF_HOME="${AUTODL_CACHE_DIR}/huggingface"
export TRANSFORMERS_CACHE="${AUTODL_CACHE_DIR}/transformers"
export HF_DATASETS_CACHE="${AUTODL_CACHE_DIR}/huggingface/datasets"

# PyTorch 缓存
export TORCH_HOME="${AUTODL_CACHE_DIR}/torch"

# XDG 缓存目录（某些库使用）
export XDG_CACHE_HOME="${AUTODL_CACHE_DIR}/xdg"

# Conda 环境路径（如果使用 conda）
export CONDA_ENVS_PATH="${AUTODL_ENV_DIR}"

# 其他缓存
export HUGGINGFACE_HUB_CACHE="${AUTODL_CACHE_DIR}/huggingface"
EOF

# 替换变量
sed -i "s|\${AUTODL_CACHE_DIR}|${CACHE_DIR}|g" "${ENV_FILE}"
sed -i "s|\${AUTODL_ENV_DIR}|${ENV_DIR}|g" "${ENV_FILE}"

echo -e "${GREEN}✓ 环境变量配置文件已生成: ${ENV_FILE}${NC}"

# 创建激活脚本
ACTIVATE_SCRIPT="${DATA_DIR}/activate_cache.sh"
cat > "${ACTIVATE_SCRIPT}" << EOF
#!/bin/bash
# 激活缓存环境变量
# 使用方法: source ${ACTIVATE_SCRIPT}

export AUTODL_CACHE_DIR="${CACHE_DIR}"
export AUTODL_ENV_DIR="${ENV_DIR}"

# 加载环境变量
source "${ENV_FILE}"

echo "缓存路径已设置:"
echo "  - Pip 缓存: \${PIP_CACHE_DIR}"
echo "  - Hugging Face 缓存: \${HF_HOME}"
echo "  - PyTorch 缓存: \${TORCH_HOME}"
echo "  - Conda 环境: \${CONDA_ENVS_PATH}"
EOF

chmod +x "${ACTIVATE_SCRIPT}"

echo -e "${GREEN}✓ 激活脚本已创建: ${ACTIVATE_SCRIPT}${NC}"

# 创建 pip 配置文件
PIP_CONFIG_DIR="${HOME}/.pip"
mkdir -p "${PIP_CONFIG_DIR}"
PIP_CONFIG="${PIP_CONFIG_DIR}/pip.conf"

cat > "${PIP_CONFIG}" << EOF
[global]
cache-dir = ${CACHE_DIR}/pip
EOF

echo -e "${GREEN}✓ Pip 配置文件已创建: ${PIP_CONFIG}${NC}"

# 创建 Hugging Face 缓存链接（如果 ~/.cache/huggingface 存在）
if [ -d "${HOME}/.cache/huggingface" ] && [ ! -L "${HOME}/.cache/huggingface" ]; then
    echo -e "${YELLOW}检测到现有 Hugging Face 缓存，创建符号链接...${NC}"
    mv "${HOME}/.cache/huggingface" "${CACHE_DIR}/huggingface_backup"
    ln -s "${CACHE_DIR}/huggingface" "${HOME}/.cache/huggingface"
    echo -e "${GREEN}✓ 已创建符号链接${NC}"
fi

# 创建 .cache 目录的符号链接（如果不存在）
CACHE_LINK="${HOME}/.cache"
if [ ! -d "${CACHE_LINK}" ]; then
    mkdir -p "${CACHE_LINK}"
fi

# 创建各个缓存的符号链接
for cache_name in huggingface transformers torch; do
    cache_path="${CACHE_LINK}/${cache_name}"
    target_path="${CACHE_DIR}/${cache_name}"
    
    if [ ! -e "${cache_path}" ]; then
        ln -s "${target_path}" "${cache_path}" 2>/dev/null || true
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}配置完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}使用方法：${NC}"
echo -e "1. 激活缓存环境变量："
echo -e "   ${YELLOW}source ${ACTIVATE_SCRIPT}${NC}"
echo ""
echo -e "2. 或者在启动脚本中添加："
echo -e "   ${YELLOW}source ${ACTIVATE_SCRIPT}${NC}"
echo -e "   ${YELLOW}./start.sh${NC}"
echo ""
echo -e "${BLUE}缓存目录：${NC}"
echo -e "  - Pip: ${CACHE_DIR}/pip"
echo -e "  - Hugging Face: ${CACHE_DIR}/huggingface"
echo -e "  - PyTorch: ${CACHE_DIR}/torch"
echo -e "  - Conda 环境: ${ENV_DIR}"
echo ""
echo -e "${BLUE}注意：${NC}"
echo -e "  - 所有缓存将存储在数据盘 ${DATA_DIR}"
echo -e "  - 不会占用系统盘空间"
echo -e "  - 建议在启动服务前先运行: source ${ACTIVATE_SCRIPT}"
echo ""

