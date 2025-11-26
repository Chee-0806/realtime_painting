# 多阶段构建 - 基础镜像
FROM python:3.10-slim as base

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    unzip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 安装Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 检查CUDA可用性并安装PyTorch
RUN python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>/dev/null \
    && echo "Installing PyTorch with CUDA support" \
    && pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121 \
    || (echo "CUDA not available, installing CPU-only PyTorch" \
    && pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu)

# 复制requirements文件
COPY requirements.txt requirements-xformers.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && (pip install --no-cache-dir -r requirements-xformers.txt || echo "xformers installation failed, continuing without it")

# 多阶段构建 - 前端构建阶段
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# 复制package文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 生产阶段 - 后端服务
FROM base as artflow-backend

# 复制应用代码
COPY . .

# 复制前端构建结果
COPY --from=frontend-builder /app/frontend/build ./static

# 创建必要的目录
RUN mkdir -p /app/logs /app/temp /app/models/lora /app/uploads

# 设置权限
RUN chmod +x /app/docker-entrypoint.sh 2>/dev/null || true

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 设置启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 开发阶段 - 前端开发服务
FROM base as artflow-frontend

WORKDIR /app/frontend

# 复制package文件
COPY frontend/package*.json ./

# 安装开发依赖
RUN npm ci

# 复制源代码
COPY frontend/ ./

# 暴露端口
EXPOSE 5173

# 开发启动命令
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]