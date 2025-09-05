# A股散户分析系统 - 阿里云Docker部署指南

## 概述

本指南详细介绍如何将A股散户分析系统通过Docker部署到阿里云ECS服务器上。

## 前置要求

### 1. 阿里云资源
- ECS云服务器（推荐配置：2核4GB内存，40GB SSD）
- 公网IP或域名
- 安全组配置（开放80、443、8080端口）

### 2. 本地环境
- Docker和Docker Compose
- Git（用于代码管理）

## 部署步骤

### 第一步：准备阿里云ECS

1. **创建ECS实例**
   ```bash
   # 推荐配置
   - 操作系统：Ubuntu 20.04 LTS 或 CentOS 8
   - 实例规格：ecs.t6-c2m4.large (2核4GB) 或更高
   - 存储：40GB SSD云盘
   - 网络：VPC，分配公网IP
   ```

2. **配置安全组规则**
   ```bash
   # 入方向规则
   HTTP     80/80     0.0.0.0/0
   HTTPS    443/443   0.0.0.0/0
   应用端口  8080/8080 0.0.0.0/0  
   SSH      22/22     你的IP/32
   ```

3. **连接到ECS服务器**
   ```bash
   ssh root@your_server_ip
   ```

### 第二步：安装Docker环境

1. **更新系统**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt upgrade -y
   
   # CentOS/RHEL
   sudo yum update -y
   ```

2. **安装Docker**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # CentOS/RHEL
   sudo yum install -y docker
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

3. **安装Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

### 第三步：上传项目代码

1. **使用Git克隆（推荐）**
   ```bash
   # 如果你的代码在Git仓库中
   git clone https://your-git-repo/stock_analysis.git
   cd stock_analysis
   ```

2. **使用SCP上传**
   ```bash
   # 在本地机器上执行
   scp -r /path/to/stock_analysis root@your_server_ip:/opt/
   ```

3. **使用压缩包上传**
   ```bash
   # 本地打包
   tar -czf stock_analysis.tar.gz stock_analysis/
   
   # 上传到服务器
   scp stock_analysis.tar.gz root@your_server_ip:/opt/
   
   # 服务器解压
   cd /opt
   tar -xzf stock_analysis.tar.gz
   ```

### 第四步：配置环境

1. **创建环境配置文件**
   ```bash
   cd /opt/stock_analysis
   cp .env.example .env
   ```

2. **编辑环境配置**
   ```bash
   vim .env
   
   # 重要配置项
   TUSHARE_TOKEN=your_tushare_token_here
   WEB_HOST=0.0.0.0
   WEB_PORT=8080
   WEB_DEBUG=false
   SECRET_KEY=your_production_secret_key
   ```

3. **配置域名（可选）**
   ```bash
   # 如果有域名，修改nginx配置
   vim nginx/default.conf
   # 将 server_name localhost; 改为你的域名
   ```

### 第五步：启动服务

1. **使用部署脚本启动**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh start
   ```

2. **或手动启动**
   ```bash
   # 构建镜像
   docker-compose build
   
   # 启动服务
   docker-compose up -d
   
   # 查看状态
   docker-compose ps
   ```

3. **验证部署**
   ```bash
   # 检查服务状态
   curl http://localhost:8080
   
   # 查看日志
   docker-compose logs -f
   ```

### 第六步：配置SSL证书（可选）

1. **使用Let's Encrypt免费证书**
   ```bash
   # 安装certbot
   sudo apt install certbot python3-certbot-nginx
   
   # 获取证书
   sudo certbot --nginx -d your-domain.com
   ```

2. **手动配置SSL证书**
   ```bash
   # 创建SSL目录
   mkdir -p ssl
   
   # 上传证书文件
   # ssl/cert.pem (证书文件)
   # ssl/key.pem (私钥文件)
   
   # 修改nginx配置启用HTTPS
   vim nginx/default.conf
   # 取消SSL相关配置的注释
   ```

## 运维管理

### 日常操作命令

```bash
# 查看服务状态
./deploy.sh status
docker-compose ps

# 查看日志
./deploy.sh logs
docker-compose logs -f stock-analysis

# 重启服务
./deploy.sh restart
docker-compose restart

# 停止服务
./deploy.sh stop
docker-compose down

# 更新代码和重新部署
git pull
docker-compose build --no-cache
docker-compose up -d
```

### 数据备份

```bash
# 使用部署脚本备份
./deploy.sh backup

# 手动备份数据库
docker exec stock-analysis-app cp /app/data/stock_analysis.db /tmp/
docker cp stock-analysis-app:/tmp/stock_analysis.db ./backup/

# 备份图表文件
docker exec stock-analysis-app tar -czf /tmp/charts.tar.gz /app/charts/
docker cp stock-analysis-app:/tmp/charts.tar.gz ./backup/
```

### 监控和日志

```bash
# 系统资源监控
htop
df -h
free -h

# Docker资源使用
docker stats

# 应用日志
tail -f logs/stock_analysis_$(date +%Y%m%d).log

# Nginx访问日志
docker exec stock-analysis-nginx tail -f /var/log/nginx/access.log
```

## 性能优化

### 1. 系统优化
```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

### 2. Docker优化
```bash
# 限制容器资源使用
# 在docker-compose.yml中添加：
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### 3. 应用优化
- 启用Redis缓存
- 配置数据库连接池
- 优化图表生成
- 使用CDN加速静态资源

## 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8080
   
   # 检查Docker日志
   docker-compose logs stock-analysis
   ```

2. **数据获取失败**
   ```bash
   # 检查网络连接
   docker exec stock-analysis-app ping tushare.pro
   
   # 检查Token配置
   docker exec stock-analysis-app env | grep TUSHARE
   ```

3. **图表生成失败**
   ```bash
   # 检查存储空间
   df -h
   
   # 检查权限
   docker exec stock-analysis-app ls -la /app/charts/
   ```

### 日志分析

```bash
# 应用错误日志
grep ERROR logs/stock_analysis_*.log

# Nginx错误日志
docker exec stock-analysis-nginx tail -f /var/log/nginx/error.log

# 系统日志
journalctl -u docker -f
```

## 扩展部署

### 高可用部署

1. **负载均衡器**
   - 使用阿里云SLB
   - 配置多个ECS实例
   - 健康检查设置

2. **数据库集群**
   - 使用阿里云RDS MySQL
   - 配置主从复制
   - 读写分离

3. **缓存集群**
   - 使用阿里云Redis
   - 配置集群模式
   - 数据持久化

### 监控告警

1. **阿里云监控**
   - ECS监控指标
   - 自定义监控
   - 告警规则配置

2. **应用监控**
   - 集成Prometheus
   - Grafana仪表板
   - 钉钉/微信告警

## 成本优化

### 1. 资源优化
- 选择合适的ECS规格
- 使用抢占式实例
- 配置弹性伸缩

### 2. 存储优化
- 使用对象存储OSS
- 配置生命周期管理
- 数据压缩和清理

### 3. 网络优化
- CDN加速
- 选择合适的带宽
- 内网通信

## 安全建议

### 1. 网络安全
- 配置WAF
- 使用VPC网络
- 安全组最小权限

### 2. 应用安全
- 定期更新依赖
- 配置HTTPS
- API访问控制

### 3. 数据安全
- 定期备份
- 加密传输
- 访问审计

## 联系支持

如果在部署过程中遇到问题，可以：

1. 查看项目文档
2. 检查GitHub Issues
3. 联系技术支持

---

**注意事项：**
- 生产环境请使用HTTPS
- 定期备份重要数据
- 监控系统资源使用情况
- 及时更新系统和应用