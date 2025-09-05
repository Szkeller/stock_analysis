# 🔒 安全配置说明

## ⚠️ 重要安全提醒

### 🔑 敏感信息保护

本项目包含敏感配置信息，请务必注意以下安全措施：

#### ✅ 已实施的安全措施

1. **环境变量隔离**
   - 所有敏感信息通过 `.env` 文件配置
   - `.env` 文件已添加到 `.gitignore`，不会被推送到Git

2. **Token保护**
   - Tushare Token 等API密钥存储在环境变量中
   - 提供 `.env.example` 作为配置模板

3. **Docker安全**
   - 生产环境密钥通过环境变量注入
   - 支持 Docker secrets 管理

#### 🚨 安全配置检查清单

- [ ] **检查 `.env` 文件**: 确保包含真实token的 `.env` 文件未被推送到Git
- [ ] **更新 Token**: 如果token已泄露，立即到 Tushare 官网重新生成
- [ ] **验证 .gitignore**: 确认 `.env` 在忽略列表中
- [ ] **清理历史**: 如果历史记录中包含敏感信息，需要清理Git历史

#### 🔧 正确的配置流程

1. **复制模板文件**
   ```bash
   cp .env.example .env
   ```

2. **编辑配置文件**
   ```bash
   # 编辑 .env 文件，填入你的真实token
   TUSHARE_TOKEN=your_real_token_here
   ```

3. **验证文件不被追踪**
   ```bash
   git status  # .env 应该不在列表中
   ```

#### 🌍 环境配置

- **开发环境**: 使用本地 `.env` 文件
- **Docker环境**: 通过环境变量或Docker secrets
- **云部署**: 使用云平台的密钥管理服务

#### 📞 安全问题处理

如果发现安全问题：

1. **立即撤销泄露的API密钥**
2. **重新生成新的密钥**
3. **更新所有相关配置**
4. **清理Git历史记录**

## 🔗 相关链接

- [Tushare官网](https://tushare.pro) - 获取和管理API Token
- [Docker Secrets文档](https://docs.docker.com/engine/swarm/secrets/)
- [GitHub Security Guide](https://docs.github.com/en/code-security)

---

**⚠️ 请务必保护好你的API密钥，不要将其提交到版本控制系统中！**