# 📊 A股散户分析系统

> 🇨🇳 专为中国A股散户设计的免费股票分析工具，提供实用的技术分析和投资建议。

[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.11+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![阿里云](https://img.shields.io/badge/部署-阿里云-orange)](https://www.aliyun.com/)

## 🎆 项目亮点

- 🔒 **免费数据源** - 支持Tushare、AKShare、东方财富等多个免费数据源
- 📊 **专业技术分析** - MA、MACD、RSI、KDJ、布林带等技术指标
- 🛡️ **智能风险评估** - 波动率分析、成交量异动检测、价格异常提醒
- 🚀 **海龟交易策略** - 集成经典量化交易策略
- 🌐 **Web界面** - 简洁直观的操作界面，支持手机和电脑访问
- 🐳 **Docker部署** - 一键部署到阿里云，支持高可用集群

## 🖥️ 系统架构

```
前端 (Web UI)
│
├── Flask Web 框架
│   ├── 股票搜索与选择
│   ├── 技术分析图表
│   └── 实时数据展示
│
├── 数据层 (Data Layer)
│   ├── 多数据源支持
│   │   ├── Tushare Pro
│   │   ├── AKShare
│   │   ├── 东方财富
│   │   └── 新浪财经
│   └── SQLite 数据库
│
├── 分析引擎 (Analysis Engine)
│   ├── 技术指标计算
│   ├── 图表生成
│   └── 信号检测
│
├── 策略模块 (Strategy Module)
│   ├── 散户策略
│   └── 海龟交易策略
│
└── 风险管理 (Risk Management)
    ├── 波动率分析
    ├── 成交量监控
    └── 止损止盈建议
```

## 🚀 快速开始

### 方法一：Docker 部署（推荐）

1. **克隆项目**
```bash
git clone https://github.com/your-username/stock_analysis.git
cd stock_analysis
```

2. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，设置 TUSHARE_TOKEN
```

3. **一键启动**
```bash
./deploy.sh start
```

4. **访问应用**
打开浏览器访问：http://localhost:8080

### 方法二：本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. **运行程序**
```bash
python main.py web
```

## 🔧 功能特性

### 📊 技术分析
- **趋势指标**: MA5/10/20/60日均线
- **动量指标**: MACD金叉死叉信号
- **摆动指标**: RSI超买超卖区间
- **随机指标**: KDJ金叉死叉
- **波带指标**: 布林带上下轨支撑位

### 🛡️ 风险评估
- **波动率分析**: 计算历史波动率，评估投资风险
- **成交量异动**: 检测成交量异常放大
- **价格异常**: 监控价格大幅波动
- **风险等级**: 自动评定风险等级（低/中/高）

### 💹 投资策略
- **散户策略**: 专为散户设计的简单易用策略
- **海龟交易法则**: 经典量化交易策略
- **止损止盈**: 自动计算合理的止损止盈位
- **仓位管理**: 提供仓位分配建议

## 🐳 Docker 部署

### 本地测试
```bash
# 测试Docker环境
./test-docker.sh
```

### 阿里云部署
```bash
# 一键部署到阿里云
./aliyun-deploy.sh
```

### 手动部署
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

## 📚 API 文档

### 搜索股票
```http
GET /api/search_stock?q=000001
```

### 分析股票
```http
GET /api/analyze/000001?days=120
```

### 获取交易信号
```http
GET /api/trading_signals/000001
```

### 风险评估
```http
GET /api/risk_assessment/000001
```

## 🔧 配置说明

### 环境变量
复制 `.env.example` 为 `.env` 并修改以下配置：

```bash
# 必需配置
TUSHARE_TOKEN=your_tushare_token_here  # 从 https://tushare.pro 获取

# 可选配置
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_DEBUG=false
SECRET_KEY=your_secret_key
```

### 数据源配置
在 `config.py` 中可以配置不同数据源的启用状态和优先级。

## 🛠️ 开发指南

### 目录结构
```
src/
├── analysis/          # 分析引擎
├── data_source/       # 数据源管理
├── database/          # 数据库操作
├── risk/              # 风险评估
├── strategy/          # 交易策略
└── web/               # Web界面
```

### 贡献指南
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

## 📖 文档

- [Docker部署README](Docker部署README.md)
- [阿里云部署指南](阿里云Docker部署指南.md)
- [海龟交易法则集成说明](海龟交易法则集成说明.md)
- [网站主流程测试报告](网站主流程测试报告.md)

## ⚠️ 免责声明

本项目仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎！

## 📞 支持

- 🐛 问题反馈：[GitHub Issues](https://github.com/your-username/stock_analysis/issues)
- 💬 讨论交流：[GitHub Discussions](https://github.com/your-username/stock_analysis/discussions)
- 📧 邮件联系：your-email@example.com

## 📖 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐ Star！**

由 ❤️ 制作，专为A股散户服务

</div>