# StreamDiffusion Backend Dockerfile
# 基于 NVIDIA CUDA 镜像，支持 GPU 加速

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt requirements-xformers.txt requirements-tensorrt.txt ./

# 安装 Python 依赖
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install -r requirements.txt

# 可选：安装 xformers（默认加速方式）
RUN pip3 install -r requirements-xformers.txt || echo "xformers installation failed, continuing..."

# 可选：安装 TensorRT（如果需要）
# RUN pip3 install -r requirements-tensorrt.txt

# 复制应用代码
COPY app/ ./app/
COPY .env.example .env

# 创建必要的目录
RUN mkdir -p engines logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/api/health', timeout=5)"

# 启动命令
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
