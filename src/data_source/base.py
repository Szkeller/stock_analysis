"""
数据获取基础类
定义数据获取的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import pandas as pd
from datetime import datetime, timedelta


class BaseDataSource(ABC):
    """数据源基础类"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """连接数据源"""
        pass
    
    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        pass
    
    @abstractmethod
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        pass
    
    @abstractmethod
    def get_price_data(self, symbol: str, start_date: str = None, 
                      end_date: str = None, period: str = "daily") -> pd.DataFrame:
        """获取价格数据"""
        pass
    
    @abstractmethod
    def get_realtime_data(self, symbols: List[str]) -> pd.DataFrame:
        """获取实时数据"""
        pass
    
    def get_market_status(self) -> Dict:
        """获取市场状态"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # A股交易时间
        morning_start = "09:30"
        morning_end = "11:30"
        afternoon_start = "13:00"
        afternoon_end = "15:00"
        
        is_trading_day = now.weekday() < 5  # 周一到周五
        
        if not is_trading_day:
            status = "休市"
        elif morning_start <= current_time <= morning_end:
            status = "开市"
        elif afternoon_start <= current_time <= afternoon_end:
            status = "开市"
        elif current_time < morning_start:
            status = "未开市"
        elif morning_end < current_time < afternoon_start:
            status = "午休"
        else:
            status = "收市"
        
        return {
            "status": status,
            "is_trading": status == "开市",
            "current_time": current_time,
            "next_open": self._get_next_open_time()
        }
    
    def _get_next_open_time(self) -> str:
        """获取下次开市时间"""
        now = datetime.now()
        
        # 如果是工作日且在开市前
        if now.weekday() < 5 and now.hour < 9:
            return f"{now.strftime('%Y-%m-%d')} 09:30"
        
        # 如果是工作日且在午休时间
        if now.weekday() < 5 and 11 <= now.hour < 13:
            return f"{now.strftime('%Y-%m-%d')} 13:00"
        
        # 其他情况，计算下个工作日
        days_ahead = 1
        if now.weekday() >= 4:  # 周五或周末
            days_ahead = 7 - now.weekday()
        
        next_day = now + timedelta(days=days_ahead)
        return f"{next_day.strftime('%Y-%m-%d')} 09:30"


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.sources: Dict[str, BaseDataSource] = {}
        self.primary_source: Optional[str] = None
    
    def add_source(self, source: BaseDataSource):
        """添加数据源"""
        self.sources[source.name] = source
        if self.primary_source is None:
            self.primary_source = source.name
    
    def set_primary_source(self, source_name: str):
        """设置主数据源"""
        if source_name in self.sources:
            self.primary_source = source_name
        else:
            raise ValueError(f"数据源 {source_name} 不存在")
    
    def get_source(self, source_name: str = None) -> BaseDataSource:
        """获取数据源"""
        if source_name is None:
            source_name = self.primary_source
        
        if source_name not in self.sources:
            raise ValueError(f"数据源 {source_name} 不存在")
        
        return self.sources[source_name]
    
    def get_source_by_name(self, source_name: str) -> BaseDataSource:
        """根据名称获取数据源"""
        if source_name not in self.sources:
            return None
        return self.sources[source_name]
    
    def connect_all(self) -> Dict[str, bool]:
        """连接所有数据源"""
        results = {}
        for name, source in self.sources.items():
            try:
                results[name] = source.connect()
            except Exception as e:
                print(f"连接数据源 {name} 失败: {e}")
                results[name] = False
        return results
    
    def get_available_sources(self) -> List[str]:
        """获取可用的数据源"""
        return [name for name, source in self.sources.items() if source.is_connected]
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        source = self.get_source()
        return source.get_stock_info(symbol)
    
    def get_real_time_price(self, symbol: str) -> Dict:
        """获取实时价格"""
        source = self.get_source()
        return source.get_real_time_price(symbol)
    
    def get_daily_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        source = self.get_source()
        return source.get_daily_prices(symbol, start_date, end_date)
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        source = self.get_source()
        return source.get_stock_list()
    
    def get_market_status(self) -> Dict:
        """获取市场状态"""
        source = self.get_source()
        return source.get_market_status()