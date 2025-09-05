# 快速配置指南

## 重要：切换到Tushare数据源

系统已切换为使用Tushare作为主数据源，您需要完成以下配置：

### 1. 获取Tushare Token

1. 访问 [Tushare官网](https://tushare.pro)
2. 注册账号并登录
3. 在个人中心获取您的Token
4. Token格式类似：`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. 配置环境变量

编辑 `.env` 文件，设置您的Token：

```bash
# 将 your_tushare_token_here 替换为您的实际token
TUSHARE_TOKEN=your_actual_token_here
```

### 3. 测试配置

运行测试命令确认配置正确：

```bash
python main.py test
```

如果看到以下输出，说明配置成功：
```
✅ 可用数据源: tushare
✅ 成功获取股票数据，共 XXXX 只股票
```

### 4. 开始使用

配置完成后，您可以：

```bash
# 分析股票
python main.py analyze 000001

# 启动Web界面
python main.py web
```

## Tushare相比AKShare的优势

- **数据质量更高**：经过专业清洗和校验
- **数据更稳定**：API稳定性更好，不易出现连接问题
- **功能更丰富**：支持财务数据、资金流向等高级功能
- **更新更及时**：数据更新频率更高

## 注意事项

1. **免费额度**：Tushare新用户有一定的免费调用额度
2. **积分制度**：长期使用可能需要积分，可通过社区贡献获得
3. **备用方案**：如果Tushare不可用，系统会自动切换到AKShare

## 遇到问题？

如果遇到配置问题：

1. 检查Token是否正确复制（不要有多余空格）
2. 确认网络连接正常
3. 查看日志文件：`logs/stock_analysis_YYYYMMDD.log`
4. 尝试重新获取Token

---

配置完成后，您将享受到更专业、更稳定的股票分析服务！📈