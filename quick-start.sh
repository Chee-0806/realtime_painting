#!/bin/bash

# ArtFlow 快速启动脚本
# 适用于快速开发和测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker 未运行，请启动 Docker 服务"
        exit 1
    fi

    log_success "Docker 检查通过"
}

# 检查Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi

    # 设置compose命令
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi

    log_success "Docker Compose 检查通过"
}

# 检查环境文件
setup_environment() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.docker" ]; then
            cp .env.docker .env
            log_success "已创建环境配置文件 .env"
        else
            log_warning "未找到环境配置文件，使用默认配置"
        fi
    else
        log_info "环境配置文件已存在"
    fi
}

# 检查GPU支持
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        log_info "检测到 NVIDIA GPU"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1
        log_success "GPU 支持已启用"
    else
        log_warning "未检测到 GPU，将使用 CPU 模式"
        log_warning "性能可能会较慢"
    fi
}

# 快速启动
quick_start() {
    log_info "开始快速启动 ArtFlow..."

    # 拉取基础镜像
    log_info "拉取基础镜像..."
    $COMPOSE_CMD pull

    # 构建并启动服务
    log_info "构建并启动服务..."
    $COMPOSE_CMD up -d --build

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 20

    # 健康检查
    log_info "执行健康检查..."
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        log_success "服务启动成功！"
    else
        log_warning "服务可能还在启动中，请稍后检查"
    fi

    # 显示访问信息
    echo
    log_success "🎉 ArtFlow 启动完成！"
    echo
    echo "访问地址:"
    echo "  🌐 API 服务: http://localhost:8000"
    echo "  📚 API 文档: http://localhost:8000/docs"
    echo "  🔍 健康检查: http://localhost:8000/api/health"
    echo
    echo "常用命令:"
    echo "  📊 查看状态: $COMPOSE_CMD ps"
    echo "  📋 查看日志: $COMPOSE_CMD logs -f"
    echo "  🛑 停止服务: $COMPOSE_CMD down"
    echo "  🔧 重新构建: $COMPOSE_CMD up -d --build"
    echo
    echo "如需完整功能，请使用: ./deploy.sh --monitor --db --cache"
}

# 主函数
main() {
    echo "🚀 ArtFlow 快速启动脚本"
    echo "==============================="
    echo

    check_docker
    check_docker_compose
    setup_environment
    check_gpu
    quick_start
}

# 运行主函数
main "$@"