#!/bin/bash

# Docker部署测试脚本

set -e

echo "🧪 开始测试Docker部署..."

# 检查必需文件
echo "📁 检查文件完整性..."
required_files=(
    "Dockerfile"
    "docker-compose.yml"
    "docker-compose.dev.yml"
    ".env.example"
    "nginx/nginx.conf"
    "nginx/default.conf"
    "deploy.sh"
    "aliyun-deploy.sh"
)

for file in "${required_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file 缺失"
        exit 1
    fi
done

# 检查环境配置
echo "⚙️ 检查环境配置..."
if [[ ! -f ".env" ]]; then
    echo "📝 创建 .env 文件..."
    cp .env.example .env
    # 设置测试用的默认值
    sed -i.bak 's/TUSHARE_TOKEN=.*/TUSHARE_TOKEN=test_token/' .env
    sed -i.bak 's/SECRET_KEY=.*/SECRET_KEY=test_secret_key_for_docker_test/' .env
    echo "⚠️ 请设置正确的 TUSHARE_TOKEN"
fi

# 验证Docker Compose配置
echo "🔍 验证Docker Compose配置..."
docker-compose config > /dev/null
echo "✅ docker-compose.yml 配置有效"

docker-compose -f docker-compose.dev.yml config > /dev/null
echo "✅ docker-compose.dev.yml 配置有效"

# 测试构建
echo "🏗️ 测试Docker镜像构建..."
if docker-compose build --no-cache; then
    echo "✅ Docker镜像构建成功"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi

# 启动测试
echo "🚀 启动容器进行测试..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 20

# 检查容器状态
echo "📊 检查容器状态..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ 容器启动成功"
    docker-compose ps
else
    echo "❌ 容器启动失败"
    docker-compose logs
    exit 1
fi

# 测试健康检查
echo "🏥 测试应用健康状态..."
max_retries=10
retry_count=0

while [ $retry_count -lt $max_retries ]; do
    if curl -f http://localhost:8080 > /dev/null 2>&1; then
        echo "✅ 应用健康检查通过"
        break
    else
        echo "⏳ 等待应用启动... ($((retry_count + 1))/$max_retries)"
        sleep 3
        retry_count=$((retry_count + 1))
    fi
done

if [ $retry_count -eq $max_retries ]; then
    echo "❌ 应用健康检查失败"
    docker-compose logs stock-analysis
    exit 1
fi

# 测试API端点
echo "🔌 测试API端点..."
if curl -f http://localhost:8080/api/search_stock?q=000001 > /dev/null 2>&1; then
    echo "✅ API端点测试通过"
else
    echo "⚠️ API端点测试失败（可能需要正确的Token）"
fi

# 停止测试容器
echo "🛑 停止测试容器..."
docker-compose down

echo "🎉 Docker部署测试完成！"
echo ""
echo "📝 测试总结："
echo "✅ 所有必需文件存在"
echo "✅ Docker Compose配置有效"
echo "✅ Docker镜像构建成功"
echo "✅ 容器启动成功"
echo "✅ 应用健康检查通过"
echo ""
echo "🚀 现在可以使用以下命令启动生产环境："
echo "  ./deploy.sh start"
echo ""
echo "🌐 或者部署到阿里云："
echo "  ./aliyun-deploy.sh"