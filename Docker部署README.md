# A股散户分析系统 - Docker 部署

本项目已完全Docker化，支持本地开发和生产环境部署，特别针对阿里云ECS进行了优化。

## 🚀 快速开始

### 本地开发环境

1. **准备环境**
   ```bash
   # 克隆项目
   git clone <your-repo-url>
   cd stock_analysis
   
   # 复制环境配置
   cp .env.example .env
   ```

2. **配置环境变量**
   编辑 `.env` 文件，至少配置以下必需项：
   ```bash
   TUSHARE_TOKEN=your_tushare_token_here
   ```

3. **启动开发环境**
   ```bash
   # 使用开发配置启动
   docker-compose -f docker-compose.dev.yml up -d
   
   # 或使用快速启动脚本
   ./deploy.sh start
   ```

4. **访问应用**
   打开浏览器访问：http://localhost:8080

### 生产环境部署

1. **完整部署（包含Nginx）**
   ```bash
   ./deploy.sh start
   ```

2. **只启动应用服务**
   ```bash
   docker-compose up -d stock-analysis
   ```

## 📁 文件说明

### Docker相关文件
- `Dockerfile` - 应用容器构建文件
- `docker-compose.yml` - 生产环境编排文件
- `docker-compose.dev.yml` - 开发环境编排文件
- `.dockerignore` - Docker构建忽略文件

### 配置文件
- `.env.example` - 环境变量模板
- `nginx/nginx.conf` - Nginx主配置
- `nginx/default.conf` - 站点配置

### 部署脚本
- `deploy.sh` - 通用部署管理脚本
- `aliyun-deploy.sh` - 阿里云一键部署脚本

### 文档
- `阿里云Docker部署指南.md` - 详细部署文档

## 🛠️ 管理命令

### 使用部署脚本（推荐）
```bash
./deploy.sh start      # 启动所有服务
./deploy.sh stop       # 停止所有服务
./deploy.sh restart    # 重启服务
./deploy.sh logs       # 查看日志
./deploy.sh status     # 查看状态
./deploy.sh backup     # 备份数据
./deploy.sh cleanup    # 清理资源
```

### 使用Docker Compose
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启特定服务
docker-compose restart stock-analysis
```

## 🌐 阿里云部署

### 方法一：一键部署脚本
1. 登录阿里云ECS服务器
2. 上传项目代码到 `/opt/stock_analysis`
3. 运行一键部署脚本：
   ```bash
   chmod +x aliyun-deploy.sh
   ./aliyun-deploy.sh
   ```

### 方法二：手动部署
详细步骤请参考 `阿里云Docker部署指南.md`

### 阿里云ECS推荐配置
- **CPU**: 2核或以上
- **内存**: 4GB或以上
- **存储**: 40GB SSD
- **网络**: 5Mbps带宽
- **操作系统**: Ubuntu 20.04 LTS 或 CentOS 8

### 安全组配置
确保在阿里云控制台的安全组中开放以下端口：
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8080 (应用端口)

## 📊 监控和运维

### 健康检查
系统内置健康检查，可通过以下方式查看：
```bash
# Docker健康检查
docker ps

# 应用健康检查
curl http://localhost:8080/health

# Nginx状态
curl http://localhost/health
```

### 日志管理
```bash
# 应用日志
docker-compose logs -f stock-analysis

# Nginx访问日志
docker exec stock-analysis-nginx tail -f /var/log/nginx/access.log

# 系统日志
journalctl -u docker -f
```

### 数据备份
```bash
# 自动备份
./deploy.sh backup

# 手动备份
docker run --rm -v stock_analysis_stock_data:/data -v $(pwd)/backup:/backup ubuntu tar czf /backup/data_$(date +%Y%m%d).tar.gz -C /data .
```

## 🔧 自定义配置

### 修改端口
1. 编辑 `docker-compose.yml`：
   ```yaml
   ports:
     - "您的端口:8080"
   ```

2. 编辑 `.env` 文件：
   ```bash
   WEB_PORT=您的端口
   ```

### 启用HTTPS
1. 获取SSL证书（推荐Let's Encrypt）
2. 将证书文件放到 `ssl/` 目录
3. 编辑 `nginx/default.conf`，启用SSL配置

### 数据库配置
默认使用SQLite，如需使用MySQL：
1. 编辑 `.env` 文件
2. 在 `docker-compose.yml` 中添加MySQL服务

## 🚨 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tulpn | grep :8080
   
   # 修改端口或停止占用进程
   ```

2. **数据源连接失败**
   ```bash
   # 检查Token配置
   docker exec stock-analysis-app env | grep TUSHARE
   
   # 测试网络连接
   docker exec stock-analysis-app ping tushare.pro
   ```

3. **容器启动失败**
   ```bash
   # 查看详细错误
   docker-compose logs stock-analysis
   
   # 检查配置文件
   docker-compose config
   ```

4. **磁盘空间不足**
   ```bash
   # 清理Docker资源
   docker system prune -f
   
   # 清理旧的镜像
   docker image prune -f
   ```

### 性能优化

1. **增加内存限制**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

2. **启用缓存**
   取消 `docker-compose.yml` 中Redis服务的注释

3. **优化Nginx**
   根据实际需求调整 `nginx/nginx.conf` 中的worker进程数

## 📞 支持

- 📖 完整文档：`阿里云Docker部署指南.md`
- 🐛 问题反馈：GitHub Issues
- 📧 技术支持：联系开发团队

---

## 📄 许可证

本项目采用 MIT 许可证。详情请参见 LICENSE 文件。