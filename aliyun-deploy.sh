#!/bin/bash

# 阿里云一键部署脚本
# 适用于阿里云ECS快速部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo -e "${BLUE}    阿里云一键部署脚本${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查操作系统
check_os() {
    if [[ -f /etc/redhat-release ]]; then
        OS="centos"
        print_message "检测到 CentOS/RHEL 系统"
    elif [[ -f /etc/debian_version ]]; then
        OS="ubuntu"
        print_message "检测到 Ubuntu/Debian 系统"
    else
        print_error "不支持的操作系统"
        exit 1
    fi
}

# 安装Docker
install_docker() {
    print_message "安装 Docker..."
    
    if command -v docker &> /dev/null; then
        print_message "Docker 已安装，跳过"
        return
    fi
    
    if [[ "$OS" == "ubuntu" ]]; then
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    elif [[ "$OS" == "centos" ]]; then
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io
    fi
    
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    
    print_message "Docker 安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    print_message "安装 Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        print_message "Docker Compose 已安装，跳过"
        return
    fi
    
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_message "Docker Compose 安装完成"
}

# 配置防火墙
configure_firewall() {
    print_message "配置防火墙..."
    
    if [[ "$OS" == "ubuntu" ]]; then
        sudo ufw allow 22
        sudo ufw allow 80
        sudo ufw allow 443
        sudo ufw allow 8080
        sudo ufw --force enable
    elif [[ "$OS" == "centos" ]]; then
        sudo firewall-cmd --permanent --add-port=22/tcp
        sudo firewall-cmd --permanent --add-port=80/tcp
        sudo firewall-cmd --permanent --add-port=443/tcp
        sudo firewall-cmd --permanent --add-port=8080/tcp
        sudo firewall-cmd --reload
    fi
    
    print_message "防火墙配置完成"
}

# 优化系统
optimize_system() {
    print_message "优化系统配置..."
    
    # 增加文件描述符限制
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # 优化内核参数
    echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
    echo "net.ipv4.tcp_max_syn_backlog = 65535" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    
    print_message "系统优化完成"
}

# 创建目录结构
create_directories() {
    print_message "创建项目目录..."
    
    sudo mkdir -p /opt/stock_analysis
    sudo chown $USER:$USER /opt/stock_analysis
    cd /opt/stock_analysis
    
    print_message "项目目录创建完成"
}

# 下载项目代码（示例）
download_project() {
    print_message "请手动上传项目代码到 /opt/stock_analysis 目录"
    print_message "或使用以下命令之一："
    echo "  git clone <your-repo-url> ."
    echo "  scp -r local_project/* user@server:/opt/stock_analysis/"
    echo "  wget <project-archive-url> && tar -xzf archive.tar.gz"
    
    read -p "代码已上传完成？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "请先上传代码，然后重新运行脚本"
        exit 1
    fi
}

# 配置环境
configure_environment() {
    print_message "配置环境变量..."
    
    if [[ ! -f .env.example ]]; then
        print_error ".env.example 文件不存在"
        exit 1
    fi
    
    if [[ ! -f .env ]]; then
        cp .env.example .env
        print_warning "已创建 .env 文件，请编辑配置"
        
        read -p "请输入 Tushare Token: " tushare_token
        sed -i "s/TUSHARE_TOKEN=.*/TUSHARE_TOKEN=$tushare_token/" .env
        
        # 生成随机密钥
        secret_key=$(openssl rand -hex 32)
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" .env
        
        # 设置生产环境配置
        sed -i "s/WEB_DEBUG=.*/WEB_DEBUG=false/" .env
        sed -i "s/WEB_HOST=.*/WEB_HOST=0.0.0.0/" .env
    fi
    
    print_message "环境配置完成"
}

# 部署应用
deploy_application() {
    print_message "部署应用..."
    
    # 构建镜像
    docker-compose build --no-cache
    
    # 启动服务
    docker-compose up -d
    
    # 等待服务启动
    sleep 15
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_message "应用部署成功！"
        
        # 获取公网IP
        public_ip=$(curl -s http://ifconfig.me)
        
        echo
        print_message "访问地址："
        echo "  http://$public_ip"
        echo "  http://$public_ip:8080"
        echo
        print_message "管理命令："
        echo "  查看状态: docker-compose ps"
        echo "  查看日志: docker-compose logs -f"
        echo "  重启服务: docker-compose restart"
        echo "  停止服务: docker-compose down"
        
    else
        print_error "应用部署失败"
        docker-compose logs
        exit 1
    fi
}

# 设置自动启动
setup_autostart() {
    print_message "设置开机自启..."
    
    cat > /etc/systemd/system/stock-analysis.service << EOF
[Unit]
Description=Stock Analysis Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/docker-compose -f /opt/stock_analysis/docker-compose.yml up -d
ExecStop=/usr/local/bin/docker-compose -f /opt/stock_analysis/docker-compose.yml down
WorkingDirectory=/opt/stock_analysis

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable stock-analysis.service
    
    print_message "自启动设置完成"
}

# 主函数
main() {
    print_header
    
    # 检查权限
    if [[ $EUID -eq 0 ]]; then
        print_warning "建议使用普通用户运行此脚本（需要sudo权限）"
    fi
    
    check_os
    install_docker
    install_docker_compose
    configure_firewall
    optimize_system
    create_directories
    download_project
    configure_environment
    deploy_application
    setup_autostart
    
    print_message "部署完成！"
    echo
    print_warning "重要提醒："
    echo "1. 请确保阿里云安全组已开放 80、443、8080 端口"
    echo "2. 如需HTTPS，请配置SSL证书"
    echo "3. 定期备份数据和更新系统"
    echo "4. 监控系统资源使用情况"
}

# 执行主函数
main "$@"