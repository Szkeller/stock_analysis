"""
数据库模型定义
使用SQLAlchemy ORM定义数据表结构
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), unique=True, nullable=False, comment='股票代码')
    name = Column(String(100), nullable=False, comment='股票名称')
    market = Column(String(10), comment='市场（SH/SZ）')
    industry = Column(String(100), comment='所属行业')
    area = Column(String(50), comment='所属地区')
    list_date = Column(String(10), comment='上市日期')
    delist_date = Column(String(10), comment='退市日期')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    __table_args__ = (
        Index('idx_symbol', 'symbol'),
        Index('idx_name', 'name'),
        Index('idx_industry', 'industry'),
    )


class DailyPrice(Base):
    """日线价格数据表"""
    __tablename__ = 'daily_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, comment='股票代码')
    date = Column(String(10), nullable=False, comment='交易日期')
    open = Column(Float, comment='开盘价')
    close = Column(Float, comment='收盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    volume = Column(Float, comment='成交量')
    amount = Column(Float, comment='成交额')
    pct_change = Column(Float, comment='涨跌幅')
    change = Column(Float, comment='涨跌额')
    turnover_rate = Column(Float, comment='换手率')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date', unique=True),
        Index('idx_date', 'date'),
    )


class RealtimePrice(Base):
    """实时价格数据表"""
    __tablename__ = 'realtime_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, comment='股票代码')
    price = Column(Float, comment='当前价格')
    open = Column(Float, comment='今日开盘价')
    pre_close = Column(Float, comment='昨日收盘价')
    high = Column(Float, comment='今日最高价')
    low = Column(Float, comment='今日最低价')
    volume = Column(Float, comment='成交量')
    amount = Column(Float, comment='成交额')
    pct_change = Column(Float, comment='涨跌幅')
    change = Column(Float, comment='涨跌额')
    turnover_rate = Column(Float, comment='换手率')
    pe_ttm = Column(Float, comment='市盈率TTM')
    pb = Column(Float, comment='市净率')
    timestamp = Column(DateTime, default=datetime.now, comment='数据时间')
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )


class TechnicalIndicator(Base):
    """技术指标数据表"""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, comment='股票代码')
    date = Column(String(10), nullable=False, comment='计算日期')
    
    # 移动平均线
    ma5 = Column(Float, comment='5日均线')
    ma10 = Column(Float, comment='10日均线')
    ma20 = Column(Float, comment='20日均线')
    ma60 = Column(Float, comment='60日均线')
    
    # MACD指标
    macd = Column(Float, comment='MACD值')
    macd_signal = Column(Float, comment='MACD信号线')
    macd_histogram = Column(Float, comment='MACD柱状图')
    
    # RSI指标
    rsi = Column(Float, comment='RSI值')
    
    # KDJ指标
    kdj_k = Column(Float, comment='KDJ-K值')
    kdj_d = Column(Float, comment='KDJ-D值')
    kdj_j = Column(Float, comment='KDJ-J值')
    
    # 布林带
    boll_upper = Column(Float, comment='布林带上轨')
    boll_middle = Column(Float, comment='布林带中轨')
    boll_lower = Column(Float, comment='布林带下轨')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_symbol_date_ti', 'symbol', 'date', unique=True),
        Index('idx_date_ti', 'date'),
    )


class Watchlist(Base):
    """自选股表"""
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, comment='股票代码')
    name = Column(String(100), comment='股票名称')
    added_date = Column(DateTime, default=datetime.now, comment='添加日期')
    notes = Column(Text, comment='备注')
    priority = Column(Integer, default=1, comment='关注优先级（1-5）')
    is_active = Column(Boolean, default=True, comment='是否活跃')
    
    __table_args__ = (
        Index('idx_symbol_watchlist', 'symbol', unique=True),
        Index('idx_added_date', 'added_date'),
    )


class Alert(Base):
    """预警记录表"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, comment='股票代码')
    alert_type = Column(String(50), nullable=False, comment='预警类型')
    title = Column(String(200), comment='预警标题')
    message = Column(Text, comment='预警内容')
    severity = Column(String(20), default='INFO', comment='严重程度（INFO/WARNING/CRITICAL）')
    is_read = Column(Boolean, default=False, comment='是否已读')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_symbol_alert', 'symbol'),
        Index('idx_created_at_alert', 'created_at'),
        Index('idx_alert_type', 'alert_type'),
    )


class Strategy(Base):
    """策略记录表"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, comment='股票代码')
    strategy_type = Column(String(50), nullable=False, comment='策略类型')
    action = Column(String(10), comment='操作建议（BUY/SELL/HOLD）')
    confidence = Column(Float, comment='置信度（0-1）')
    reason = Column(Text, comment='操作理由')
    price = Column(Float, comment='建议价格')
    stop_loss = Column(Float, comment='止损价格')
    take_profit = Column(Float, comment='止盈价格')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    __table_args__ = (
        Index('idx_symbol_strategy', 'symbol'),
        Index('idx_created_at_strategy', 'created_at'),
        Index('idx_strategy_type', 'strategy_type'),
    )


class UserConfig(Base):
    """用户配置表"""
    __tablename__ = 'user_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, comment='配置键')
    value = Column(Text, comment='配置值')
    description = Column(Text, comment='配置描述')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    __table_args__ = (
        Index('idx_key', 'key'),
    )


def create_database(database_url: str = None):
    """创建数据库和表"""
    if database_url is None:
        # 确保data目录存在
        data_dir = "/Volumes/WDSSD/stock_analysis/data"
        os.makedirs(data_dir, exist_ok=True)
        database_url = f"sqlite:///{data_dir}/stock_analysis.db"
    
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(database_url: str = None):
    """获取数据库会话"""
    engine = create_database(database_url)
    Session = sessionmaker(bind=engine)
    return Session()