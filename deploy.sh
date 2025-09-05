#!/bin/bash

# 股票分析系统启动脚本
# 用于本地开发和生产部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  A股散户分析系统 Docker 部署${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查Docker和Docker Compose
check_requirements() {
    print_message "检查环境依赖..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_message "Docker 环境检查通过"
}

# 检查环境配置
check_env() {
    print_message "检查环境配置..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env 文件不存在，正在从 .env.example 创建..."
            cp .env.example .env
            print_warning "请编辑 .env 文件，配置必要的参数（如 TUSHARE_TOKEN）"
            read -p "按 Enter 键继续..." -r
        else
            print_error ".env 文件不存在，请创建配置文件"
            exit 1
        fi
    fi
    
    # 检查关键配置
    if ! grep -q "TUSHARE_TOKEN=.*[^[:space:]]" .env; then
        print_warning "请在 .env 文件中配置 TUSHARE_TOKEN"
    fi
    
    print_message "环境配置检查完成"
}

# 构建镜像
build_image() {
    print_message "构建 Docker 镜像..."
    docker-compose build --no-cache
    print_message "镜像构建完成"
}

# 启动服务
start_services() {
    print_message "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    print_message "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_message "服务启动成功！"
        echo
        print_message "访问地址："
        echo "  本地访问: http://localhost"
        echo "  直接访问: http://localhost:8080"
        echo
        print_message "查看日志: docker-compose logs -f"
        print_message "停止服务: docker-compose down"
    else
        print_error "服务启动失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# 停止服务
stop_services() {
    print_message "停止服务..."
    docker-compose down
    print_message "服务已停止"
}

# 查看日志
show_logs() {
    docker-compose logs -f "${2:-}"
}

# 重启服务
restart_services() {
    print_message "重启服务..."
    docker-compose restart
    print_message "服务已重启"
}

# 清理资源
cleanup() {
    print_message "清理Docker资源..."
    docker-compose down -v
    docker system prune -f
    print_message "清理完成"
}

# 备份数据
backup_data() {
    print_message "备份数据..."
    BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份数据卷
    docker run --rm -v stock_analysis_stock_data:/data -v "$(pwd)/$BACKUP_DIR":/backup ubuntu tar czf /backup/data.tar.gz -C /data .
    
    print_message "数据备份完成: $BACKUP_DIR"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  start     启动服务（默认）"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  build     重新构建镜像"
    echo "  logs      查看日志"
    echo "  status    查看服务状态"
    echo "  backup    备份数据"
    echo "  cleanup   清理Docker资源"
    echo "  help      显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 start          # 启动所有服务"
    echo "  $0 logs           # 查看所有日志"
    echo "  $0 logs stock-analysis # 查看特定服务日志"
    echo "  $0 backup         # 备份数据"
}

# 显示服务状态
show_status() {
    print_message "服务状态:"
    docker-compose ps
}

# 主函数
main() {
    print_header
    
    case "${1:-start}" in
        "start")
            check_requirements
            check_env
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "build")
            check_requirements
            build_image
            ;;
        "logs")
            show_logs "$@"
            ;;
        "status")
            show_status
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"