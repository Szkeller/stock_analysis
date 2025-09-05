"""
中国A股散户分析系统
专为中国A股散户设计的股票分析工具
"""

# 项目信息
PROJECT_NAME = "A股散户分析系统"
VERSION = "1.0.0"
DESCRIPTION = "专为中国A股散户设计的简单实用的股票分析工具"

# 数据源配置
DATA_SOURCES = {
    "akshare": {
        "enabled": False,  # 已禁用
        "priority": 3,  # 优先级：数字越小优先级越高
        "description": "AKShare - 开源金融数据接口",
        "features": ["历史数据", "实时数据", "股票列表"]
    },
    "tushare": {
        "enabled": False,  # 已禁用
        "priority": 2,
        "token": "",      # 在.env文件中配置
        "description": "Tushare - 专业金融数据接口",
        "features": ["历史数据", "基本面数据", "财务数据"]
    },
    "eastmoney": {
        "enabled": True,
        "priority": 1,  # 最高优先级
        "description": "东方财富 - 免费可靠的股票数据",
        "features": ["历史数据", "实时数据", "股票列表"]
    },
    "sina": {
        "enabled": True,
        "priority": 4,
        "description": "新浪财经 - 实时行情数据",
        "features": ["实时数据"]
    },
    "qqstock": {
        "enabled": True,
        "priority": 5,
        "description": "腾讯股票 - 实时行情数据",
        "features": ["历史数据", "实时数据"]
    },
    "wangyi": {
        "enabled": False,  # 已禁用
        "priority": 6,
        "description": "网易财经 - 股票行情数据",
        "features": ["历史数据", "实时数据"]
    }
}

# 数据库配置
DATABASE = {
    "type": "sqlite",
    "path": "data/stock_analysis.db"
}

# 技术指标配置
TECHNICAL_INDICATORS = {
    "MA": [5, 10, 20, 60],  # 移动平均线周期
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "RSI": {"period": 14},
    "KDJ": {"k_period": 9, "d_period": 3, "j_period": 3},
    "BOLL": {"period": 20, "std": 2}  # 布林带
}

# 风险评估配置
RISK_ASSESSMENT = {
    "volatility_threshold": 0.05,  # 波动率阈值
    "volume_ratio_threshold": 2.0,  # 成交量比率阈值
    "price_change_threshold": 0.1   # 价格变化阈值
}

# 监控配置
MONITORING = {
    "update_interval": 300,  # 更新间隔（秒）
    "market_hours": {
        "start": "09:30",
        "end": "15:00",
        "lunch_start": "11:30",
        "lunch_end": "13:00"
    }
}

# Web界面配置
WEB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": True
}

# 散户策略配置
RETAIL_STRATEGY = {
    "stop_loss": 0.08,      # 止损比例 8%
    "take_profit": 0.15,    # 止盈比例 15%
    "min_hold_days": 3,     # 最短持有天数
    "max_position": 0.2,    # 单只股票最大仓位 20%
    "enable_turtle": True,  # 启用海龜交易法则
    "turtle_weight": 0.6    # 海龜策略权重
}

# 海龜交易法则配置
TURTLE_STRATEGY = {
    # 系统1参数（短期）
    "system1_entry_period": 20,    # 20天突破入场
    "system1_exit_period": 10,     # 10天突破出场
    
    # 系统2参数（长期）
    "system2_entry_period": 55,    # 55天突破入场
    "system2_exit_period": 20,     # 20天突破出场
    
    # 风险管理参数
    "atr_period": 20,              # ATR计算周期
    "stop_loss_atr_multiple": 2.0, # 止损为2倍ATR
    "position_risk_pct": 0.02,     # 每笔交易风险2%
    "max_positions": 4,            # 最大同时持仓数
    
    # 资金管理
    "total_capital": 100000,       # 总资金
    "unit_limit_single": 0.05,     # 单个市场最大仓位5%
    "unit_limit_sector": 0.12,     # 同行业最大仓位12%
    "unit_limit_direction": 0.20,  # 同方向最大仓位20%
}