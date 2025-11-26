#!/bin/bash

# ArtFlow Docker 部署脚本
# 使用方法: ./deploy.sh [选项]
# 选项:
#   -p, --profile PROFILE    使用的配置文件 (dev/prod)
#   -e, --env FILE          环境变量文件
#   -b, --build             重新构建镜像
#   -d, --down              停止并删除服务
#   -l, --logs              查看日志
#   -s, --status            查看服务状态
#   -h, --help              显示帮助信息

set -e

# 默认配置
PROFILE="prod"
ENV_FILE=".env"
BUILD=false
DOWN=false
LOGS=false
STATUS=false
SERVICES=""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 显示帮助信息
show_help() {
    cat << EOF
ArtFlow Docker 部署脚本

使用方法:
    $0 [选项]

选项:
    -p, --profile PROFILE    使用的配置文件 (dev/prod)
    -e, --env FILE          环境变量文件 (默认: .env)
    -b, --build             重新构建镜像
    -d, --down              停止并删除服务
    -l, --logs              查看日志
    -s, --status            查看服务状态
    --monitor               启动监控服务
    --db                    启动数据库服务
    --cache                 启动缓存服务
    -h, --help              显示帮助信息

示例:
    $0                                              # 启动生产环境
    $0 -p dev -b                                    # 开发环境并重新构建
    $0 --monitor --db --cache                       # 启动完整服务栈
    $0 -d                                           # 停止所有服务
    $0 -l                                           # 查看日志

EOF
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或不在PATH中"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi

    # 使用 docker compose 或 docker-compose
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi

    log_success "依赖检查通过"
}

# 检查环境文件
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "环境文件 $ENV_FILE 不存在，使用默认配置"
        if [ -f ".env.docker" ]; then
            cp .env.docker "$ENV_FILE"
            log_success "已从 .env.docker 复制环境配置"
        else
            log_error "找不到 .env.docker 文件"
            exit 1
        fi
    fi
}

# 检查GPU支持
check_gpu_support() {
    if command -v nvidia-smi &> /dev/null; then
        log_info "检测到NVIDIA GPU"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    else
        log_warning "未检测到NVIDIA GPU，将使用CPU模式"
        # 更新环境变量以禁用GPU
        sed -i 's/STREAMDIFFUSION_GPU_ENABLED=true/STREAMDIFFUSION_GPU_ENABLED=false/' "$ENV_FILE"
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    $COMPOSE_CMD build
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    local compose_args="-f docker-compose.yml"

    # 添加profile
    if [ "$PROFILE" = "dev" ]; then
        compose_args="$compose_args --profile dev"
    elif [ "$PROFILE" = "prod" ]; then
        compose_args="$compose_args --profile prod"
    fi

    # 添加其他services
    if [ -n "$SERVICES" ]; then
        compose_args="$compose_args $SERVICES"
    fi

    log_info "启动服务 (Profile: $PROFILE)..."
    $COMPOSE_CMD $compose_args up -d

    log_success "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止并删除服务..."
    $COMPOSE_CMD down -v --remove-orphans
    log_success "服务已停止"
}

# 查看状态
show_status() {
    log_info "服务状态:"
    $COMPOSE_CMD ps

    echo
    log_info "容器资源使用:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 查看日志
show_logs() {
    local service=""
    if [ -n "$1" ]; then
        service="$1"
    fi

    log_info "查看日志..."
    if [ -n "$service" ]; then
        $COMPOSE_CMD logs -f "$service"
    else
        $COMPOSE_CMD logs -f
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 等待服务启动
    sleep 10

    # 检查API健康状态
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        log_success "API健康检查通过"
    else
        log_warning "API健康检查失败"
    fi

    # 检查服务状态
    show_status
}

# 主函数
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--profile)
                PROFILE="$2"
                shift 2
                ;;
            -e|--env)
                ENV_FILE="$2"
                shift 2
                ;;
            -b|--build)
                BUILD=true
                shift
                ;;
            -d|--down)
                DOWN=true
                shift
                ;;
            -l|--logs)
                LOGS=true
                shift
                ;;
            -s|--status)
                STATUS=true
                shift
                ;;
            --monitor)
                SERVICES="$SERVICES --profile monitor"
                shift
                ;;
            --db)
                SERVICES="$SERVICES --profile db"
                shift
                ;;
            --cache)
                SERVICES="$SERVICES --profile cache"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 执行操作
    if [ "$DOWN" = true ]; then
        check_dependencies
        stop_services
        exit 0
    fi

    if [ "$LOGS" = true ]; then
        check_dependencies
        show_logs "$2"
        exit 0
    fi

    if [ "$STATUS" = true ]; then
        check_dependencies
        show_status
        exit 0
    fi

    # 正常部署流程
    log_info "开始部署 ArtFlow..."

    check_dependencies
    check_env_file
    check_gpu_support

    if [ "$BUILD" = true ]; then
        build_images
    fi

    start_services

    # 等待服务启动并进行健康检查
    log_info "等待服务启动..."
    sleep 15
    health_check

    log_success "部署完成!"
    echo
    echo "访问地址:"
    echo "  - API服务: http://localhost:8000"
    echo "  - API文档: http://localhost:8000/docs"
    echo "  - 健康检查: http://localhost:8000/api/health"

    if [ "$PROFILE" = "dev" ]; then
        echo "  - 前端开发: http://localhost:5173"
    fi

    if echo "$SERVICES" | grep -q "monitor"; then
        echo "  - 监控面板: http://localhost:9090"
    fi

    echo
    echo "管理命令:"
    echo "  - 查看状态: $0 -s"
    echo "  - 查看日志: $0 -l"
    echo "  - 停止服务: $0 -d"
}

# 捕获退出信号
trap 'log_warning "部署被中断"; exit 1' INT TERM

# 运行主函数
main "$@"