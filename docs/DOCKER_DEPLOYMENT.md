# ArtFlow 容器化部署指南

本文档介绍如何使用Docker和Docker Compose部署ArtFlow实时AI图像生成应用。

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细部署步骤](#详细部署步骤)
- [配置选项](#配置选项)
- [生产环境配置](#生产环境配置)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 系统要求

### 最低要求
- **CPU**: 4核心以上
- **内存**: 8GB RAM以上
- **存储**: 50GB可用空间
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows 10+

### 推荐配置（GPU支持）
- **CPU**: 8核心以上
- **内存**: 32GB RAM以上
- **GPU**: NVIDIA GPU with 12GB+ VRAM (CUDA 11.8+ 或 12.1+)
- **存储**: 100GB可用空间 (SSD推荐)

### 软件依赖
- Docker Engine 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (GPU支持)

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd realtime_painting
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp .env.docker .env

# 根据需要修改环境变量
vim .env
```

### 3. 启动服务
```bash
# 生产环境（仅后端）
docker-compose up -d

# 开发环境（包含前端开发服务）
docker-compose --profile dev up -d

# 完整环境（包含数据库、缓存、监控）
docker-compose --profile db --profile cache --profile monitor up -d
```

### 4. 验证部署
- 后端API: http://localhost:8000
- 健康检查: http://localhost:8000/api/health
- API文档: http://localhost:8000/docs

## 详细部署步骤

### 1. 准备工作

#### 安装Docker和Docker Compose
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### NVIDIA GPU支持（可选）
```bash
# 安装NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### 2. 环境配置

#### 基本配置
```bash
# 复制环境变量文件
cp .env.docker .env

# 主要配置项
vim .env
```

#### 关键环境变量说明
```bash
# 基本配置
STREAMDIFFUSION_HOST=0.0.0.0          # 服务监听地址
STREAMDIFFUSION_PORT=8000             # 服务端口
STREAMDIFFUSION_LOG_LEVEL=INFO        # 日志级别

# GPU配置
STREAMDIFFUSION_GPU_ENABLED=true      # 是否启用GPU
STREAMDIFFUSION_DEVICE=cuda           # 计算设备类型
STREAMDIFFUSION_DTYPE=float16         # 数据类型

# 性能配置
STREAMDIFFUSION_MAX_BATCH_SIZE=4      # 最大批处理大小
STREAMDIFFUSION_QUEUE_SIZE=10         # 队列大小
STREAMDIFFUSION_TIMEOUT=60            # 超时时间
```

### 3. 构建和启动

#### 构建镜像
```bash
# 构建所有服务
docker-compose build

# 构建特定服务
docker-compose build artflow-backend
```

#### 启动服务
```bash
# 启动基础服务
docker-compose up -d artflow-backend

# 启动开发环境
docker-compose --profile dev up -d

# 启动完整生产环境
docker-compose --profile db --profile cache --profile monitor up -d
```

### 4. 验证部署

#### 检查服务状态
```bash
# 查看所有服务状态
docker-compose ps

# 查看服务日志
docker-compose logs artflow-backend

# 实时查看日志
docker-compose logs -f artflow-backend
```

#### 健康检查
```bash
# API健康检查
curl http://localhost:8000/api/health

# 查看GPU使用情况
docker exec -it artflow-backend nvidia-smi
```

## 配置选项

### Docker Compose Profiles

#### 可用的Profile
- `dev`: 包含前端开发服务
- `prod`: 包含Nginx反向代理
- `db`: 包含PostgreSQL数据库
- `cache`: 包含Redis缓存
- `monitor`: 包含Prometheus监控

#### 使用示例
```bash
# 开发环境
docker-compose --profile dev up -d

# 生产环境
docker-compose --profile prod up -d

# 完整功能环境
docker-compose --profile dev --profile db --profile cache --profile monitor up -d
```

### 存储卷配置

#### 数据持久化
- `artflow_models`: 模型文件存储
- `artflow_uploads`: 上传文件存储
- `artflow_logs`: 日志文件存储
- `artflow_temp`: 临时文件存储

#### 备份重要数据
```bash
# 备份模型和上传文件
docker run --rm -v artflow_models:/data -v $(pwd):/backup alpine tar czf /backup/models-backup.tar.gz -C /data .
docker run --rm -v artflow_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

## 生产环境配置

### 1. 安全配置

#### HTTPS配置
```bash
# 生成SSL证书（自签名）
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem

# 或使用Let's Encrypt
certbot certonly --standalone -d your-domain.com
```

#### 更新Nginx配置
```bash
# 启用HTTPS配置
vim nginx/sites-available/artflow.conf

# 取消注释HTTPS部分并更新域名
```

### 2. 性能优化

#### 资源限制
```yaml
# 在docker-compose.yml中添加资源限制
services:
  artflow-backend:
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '8'
        reservations:
          memory: 8G
          cpus: '4'
```

#### 调优参数
```bash
# 更新环境变量
STREAMDIFFUSION_MAX_BATCH_SIZE=8
STREAMDIFFUSION_QUEUE_SIZE=20
STREAMDIFFUSION_WORKERS=4
```

### 3. 监控配置

#### Prometheus配置
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'artflow'
    static_configs:
      - targets: ['artflow-backend:8000']
```

#### 启动监控
```bash
docker-compose --profile monitor up -d
```

## 监控和维护

### 1. 日志管理

#### 日志轮转
```bash
# 配置日志轮转
sudo vim /etc/logrotate.d/artflow
```

```
/var/lib/docker/containers/*/*-json.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

#### 查看日志
```bash
# 应用日志
docker-compose logs -f artflow-backend

# 系统资源使用
docker stats

# GPU使用情况
docker exec artflow-backend nvidia-smi
```

### 2. 数据备份

#### 自动备份脚本
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/artflow"

mkdir -p $BACKUP_DIR

# 备份数据卷
docker run --rm -v artflow_models:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/models_$DATE.tar.gz -C /data .
docker run --rm -v artflow_uploads:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/uploads_$DATE.tar.gz -C /data .
docker run --rm -v artflow_logs:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/logs_$DATE.tar.gz -C /data .

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

#### 设置定时任务
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /path/to/backup.sh
```

### 3. 更新部署

#### 滚动更新
```bash
# 拉取最新代码
git pull origin main

# 重新构建和部署
docker-compose build artflow-backend
docker-compose up -d artflow-backend
```

#### 零停机更新
```bash
# 使用blue-green部署
docker-compose -f docker-compose.yml -f docker-compose.blue.yml up -d
```

## 故障排除

### 常见问题

#### 1. GPU相关
```bash
# 检查GPU支持
nvidia-docker run --rm nvidia/cuda:11.8-base nvidia-smi

# 检查容器GPU访问
docker exec artflow-backend python -c "import torch; print(torch.cuda.is_available())"
```

#### 2. 内存问题
```bash
# 检查内存使用
docker stats

# 清理未使用的Docker资源
docker system prune -a
```

#### 3. 网络问题
```bash
# 检查网络连接
docker network ls
docker network inspect realtime_painting_artflow-network

# 重启网络
docker-compose down
docker-compose up -d
```

#### 4. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :8000
lsof -i :8000

# 修改端口
vim .env
# 更新STREAMDIFFUSION_PORT=8001
```

### 性能调优

#### GPU内存优化
```bash
# 监控GPU内存
watch -n 1 nvidia-smi

# 在容器中清理GPU内存
docker exec artflow-backend python -c "import torch; torch.cuda.empty_cache()"
```

#### CPU和内存优化
```bash
# 调整worker数量
STREAMDIFFUSION_WORKERS=4

# 优化批处理大小
STREAMDIFFUSION_MAX_BATCH_SIZE=4
```

### 日志分析

#### 常见错误和解决方案
```bash
# CUDA内存不足
# 解决：减少批处理大小或启用xformers
STREAMDIFFUSION_MAX_BATCH_SIZE=2

# 模型加载失败
# 解决：检查模型文件路径和权限
ls -la /app/models/

# WebSocket连接失败
# 解决：检查防火墙和网络配置
curl -I http://localhost:8000/api/health
```

## 高级配置

### 集群部署

#### Docker Swarm
```bash
# 初始化Swarm
docker swarm init

# 部署服务栈
docker stack deploy -c docker-compose.yml artflow
```

#### Kubernetes
```bash
# 创建k8s配置
kubectl apply -f k8s/
```

### 自定义扩展

#### 添加新服务
```yaml
# 在docker-compose.yml中添加新服务
custom-service:
  image: your-image
  networks:
    - artflow-network
  depends_on:
    - artflow-backend
```

## 支持和反馈

如果遇到部署问题，请：

1. 查看本文档的故障排除部分
2. 检查GitHub Issues
3. 提交新的Issue并提供详细的错误日志

---

*最后更新: 2025年11月*