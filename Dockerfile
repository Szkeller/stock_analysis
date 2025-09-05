# 使用官方Python 3.11镜像作为基础镜像
FROM python:3.11-slim-bullseye

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    TZ=Asia/Shanghai

# 安装系统依赖和TA-Lib
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    unzip \
    libatlas-base-dev \
    libopenblas-dev \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装TA-Lib库
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# 更新pip和安装wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/charts /app/output

# 复制项目文件
COPY . .

# 创建非root用户
RUN groupadd -r stockuser && useradd -r -g stockuser stockuser \
    && chown -R stockuser:stockuser /app

# 切换到非root用户
USER stockuser

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# 启动命令
CMD ["python", "main.py", "web"]