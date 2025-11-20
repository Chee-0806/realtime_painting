#!/bin/bash
# StreamDiffusion 前后端启动脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}StreamDiffusion 前后端启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 加载缓存环境变量（如果存在）
CACHE_SCRIPT="/root/autodl-tmp/activate_cache.sh"
if [ -f "${CACHE_SCRIPT}" ]; then
    echo -e "${BLUE}加载缓存环境变量...${NC}"
    source "${CACHE_SCRIPT}"
    echo -e "${GREEN}✓ 缓存路径已设置到数据盘${NC}"
fi

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${YELLOW}激活虚拟环境...${NC}"
    source venv/bin/activate
elif [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo -e "${GREEN}使用 Conda 环境: $CONDA_DEFAULT_ENV${NC}"
else
    echo -e "${YELLOW}警告: 未检测到虚拟环境，建议使用虚拟环境${NC}"
fi

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Python 版本: $PYTHON_VERSION${NC}"

# 检查配置文件
if [ ! -f "app/config/config.yaml" ]; then
    echo -e "${RED}错误: 配置文件不存在: app/config/config.yaml${NC}"
    exit 1
fi
echo -e "${GREEN}配置文件: app/config/config.yaml${NC}"

# 检查必要的目录
mkdir -p engines
mkdir -p logs

# 设置环境变量（可选）
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# 设置 CUDA 库路径（让 cuda-python 和 TensorRT 能找到 CUDA runtime 和 cuDNN）
# 优先使用系统 CUDA（TensorRT 通常需要系统级 CUDA）
if [ -d "/usr/local/cuda-11.8/lib64" ]; then
    export LD_LIBRARY_PATH="/usr/local/cuda-11.8/lib64:${LD_LIBRARY_PATH}"
elif [ -d "/usr/local/cuda/lib64" ]; then
    export LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
fi

# 然后添加 conda 环境中的 CUDA 库（作为备选）
if [ -n "$CONDA_PREFIX" ]; then
    CUDA_LIB_PATH="${CONDA_PREFIX}/lib/python3.10/site-packages/nvidia"
    # cuDNN 库路径（TensorRT 需要）
    if [ -d "${CUDA_LIB_PATH}/cudnn/lib" ]; then
        export LD_LIBRARY_PATH="${CUDA_LIB_PATH}/cudnn/lib:${LD_LIBRARY_PATH}"
    fi
    if [ -d "${CUDA_LIB_PATH}/cudnn_cu12/lib" ]; then
        export LD_LIBRARY_PATH="${CUDA_LIB_PATH}/cudnn_cu12/lib:${LD_LIBRARY_PATH}"
    fi
    # CUDA runtime 库路径
    if [ -d "${CUDA_LIB_PATH}/cuda_runtime/lib" ]; then
        export LD_LIBRARY_PATH="${CUDA_LIB_PATH}/cuda_runtime/lib:${LD_LIBRARY_PATH}"
    fi
    if [ -d "${CUDA_LIB_PATH}/cu13/lib" ]; then
        export LD_LIBRARY_PATH="${CUDA_LIB_PATH}/cu13/lib:${LD_LIBRARY_PATH}"
    fi
    # PyTorch 的 CUDA 库路径
    if [ -d "${CONDA_PREFIX}/lib/python3.10/site-packages/torch/lib" ]; then
        export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib/python3.10/site-packages/torch/lib:${LD_LIBRARY_PATH}"
    fi
fi

# 清理函数：当脚本退出时停止所有后台进程
cleanup() {
    echo -e "\n${YELLOW}正在停止服务...${NC}"
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    fi
    exit 0
}

# 注册清理函数
trap cleanup SIGINT SIGTERM EXIT

# 检查并清理占用端口的进程
check_and_free_port() {
    local port=$1
    local service_name=$2
    
    # 使用 Python 检查端口是否被占用
    if python3 -c "import socket; s = socket.socket(); result = s.connect_ex(('127.0.0.1', $port)); s.close(); exit(0 if result == 0 else 1)" 2>/dev/null; then
        echo -e "${YELLOW}检测到端口 $port 被占用，正在查找并停止相关进程...${NC}"
        
        # 使用 Python 通过 /proc/net/tcp 精确查找占用端口的进程
        local pids=$(python3 <<PYEOF
import os
port = $port
port_hex = format(port, '04X')
pids = set()

try:
    with open('/proc/net/tcp', 'r') as f:
        lines = f.readlines()[1:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                local_addr = parts[1]
                if local_addr.split(':')[1] == port_hex:
                    inode = parts[9]
                    for pid_dir in os.listdir('/proc'):
                        if pid_dir.isdigit():
                            try:
                                for fd in os.listdir(f'/proc/{pid_dir}/fd'):
                                    fd_path = f'/proc/{pid_dir}/fd/{fd}'
                                    if os.path.islink(fd_path):
                                        link = os.readlink(fd_path)
                                        if f'socket:[{inode}]' in link:
                                            pids.add(pid_dir)
                            except (PermissionError, FileNotFoundError):
                                pass
except Exception:
    pass

# 如果没找到，查找所有 uvicorn 相关进程作为备选
if not pids:
    import subprocess
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'uvicorn' in line.lower() or ('python' in line.lower() and 'main:app' in line):
                parts = line.split()
                if len(parts) > 1:
                    pids.add(parts[1])
    except Exception:
        pass

print(' '.join(pids))
PYEOF
)
        
        if [ -n "$pids" ]; then
            for pid in $pids; do
                if kill -0 $pid 2>/dev/null; then
                    echo -e "${YELLOW}停止进程 PID: $pid 及其子进程...${NC}"
                    # 先停止子进程
                    pkill -P $pid 2>/dev/null || true
                    sleep 0.3
                    # 再停止主进程
                    kill -9 $pid 2>/dev/null || true
                fi
            done
            sleep 1
            
            # 再次查找并清理可能残留的进程
            local remaining_pids=$(ps aux | grep -E "[u]vicorn|python.*main:app" | awk '{print $2}')
            if [ -n "$remaining_pids" ]; then
                for pid in $remaining_pids; do
                    echo -e "${YELLOW}清理残留进程 PID: $pid...${NC}"
                    kill -9 $pid 2>/dev/null || true
                    pkill -P $pid 2>/dev/null || true
                done
                sleep 1
            fi
            
            # 验证端口是否已释放
            if python3 -c "import socket; s = socket.socket(); result = s.connect_ex(('127.0.0.1', $port)); s.close(); exit(0 if result == 0 else 1)" 2>/dev/null; then
                echo -e "${RED}警告: 端口 $port 仍被占用，可能需要手动检查${NC}"
            else
                echo -e "${GREEN}✓ 端口 $port 已释放${NC}"
            fi
        else
            echo -e "${YELLOW}警告: 无法找到占用端口的进程，但端口被占用，可能需要手动检查${NC}"
        fi
    else
        echo -e "${GREEN}端口 $port 可用${NC}"
    fi
}

# 检查后端端口
check_and_free_port 8000 "后端服务"

# 启动后端服务
echo -e "${GREEN}启动后端服务...${NC}"
python3 -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端服务启动
sleep 3

# 检查后端是否启动成功
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}错误: 后端服务启动失败${NC}"
    cat logs/backend.log
    exit 1
fi
echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}后端日志: logs/backend.log${NC}"

# 检查前端目录
if [ ! -d "frontend" ]; then
    echo -e "${YELLOW}警告: 前端目录不存在，仅启动后端服务${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
    wait $BACKEND_PID
    exit 0
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}前端依赖未安装，正在安装...${NC}"
    cd frontend
    npm install
    cd ..
fi

# 启动前端服务
echo -e "${GREEN}启动前端服务...${NC}"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 等待前端服务启动
sleep 3

# 检查前端是否启动成功
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}错误: 前端服务启动失败${NC}"
    cat logs/frontend.log
    exit 1
fi
echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
echo -e "${BLUE}前端日志: logs/frontend.log${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}所有服务已启动${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}后端服务: http://0.0.0.0:8000${NC}"
echo -e "${BLUE}前端服务: http://127.0.0.1:6006${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 等待所有后台进程
wait

