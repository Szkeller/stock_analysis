"""
新浪财经数据源
实时股票行情数据获取
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import re
from .base import BaseDataSource


class SinaDataSource(BaseDataSource):
    """新浪财经数据源"""
    
    def __init__(self):
        super().__init__("sina")
        self.description = "新浪财经 - 实时股票行情数据"
        self.base_url = "http://hq.sinajs.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'http://finance.sina.com.cn/'
        })
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """测试连接"""
        try:
            # 测试获取平安银行的实时数据
            url = f"{self.base_url}/list=sz000001"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200 and 'var hq_str_sz000001' in response.text:
                self.logger.info("新浪财经数据源连接成功")
                self.is_connected = True
                return True
            
            self.logger.warning("新浪财经数据源连接失败")
            self.is_connected = False
            return False
            
        except Exception as e:
            self.logger.error(f"新浪财经数据源连接测试失败: {e}")
            self.is_connected = False
            return False
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        try:
            # 新浪没有直接的股票列表接口，这里返回一些常见股票
            common_stocks = [
                ('000001', '平安银行', 'SZ'),
                ('000002', '万科A', 'SZ'),
                ('000858', '五粮液', 'SZ'),
                ('002415', '海康威视', 'SZ'),
                ('600000', '浦发银行', 'SH'),
                ('600036', '招商银行', 'SH'),
                ('600519', '贵州茅台', 'SH'),
                ('600887', '伊利股份', 'SH'),
                ('000858', '五粮液', 'SZ'),
                ('002594', '比亚迪', 'SZ'),
            ]
            
            stocks = []
            for symbol, name, market in common_stocks:
                stocks.append({
                    'symbol': symbol,
                    'name': name,
                    'market': market
                })
            
            df = pd.DataFrame(stocks)
            self.logger.info(f"新浪数据源提供{len(df)}只常见股票")
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_real_time_price(self, symbol: str) -> Dict:
        """获取实时价格"""
        try:
            sina_symbol = self._convert_symbol(symbol)
            url = f"{self.base_url}/list={sina_symbol}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            # 解析新浪返回的数据
            content = response.text
            pattern = rf'var hq_str_{sina_symbol}="([^"]*)"'
            match = re.search(pattern, content)
            
            if not match:
                return {}
            
            data_str = match.group(1)
            data_parts = data_str.split(',')
            
            if len(data_parts) < 32:
                return {}
            
            # 新浪数据格式解析
            return {
                'symbol': symbol,
                'name': data_parts[0],
                'open': float(data_parts[1]) if data_parts[1] else 0,
                'prev_close': float(data_parts[2]) if data_parts[2] else 0,
                'price': float(data_parts[3]) if data_parts[3] else 0,
                'high': float(data_parts[4]) if data_parts[4] else 0,
                'low': float(data_parts[5]) if data_parts[5] else 0,
                'bid_price': float(data_parts[6]) if data_parts[6] else 0,
                'ask_price': float(data_parts[7]) if data_parts[7] else 0,
                'volume': int(float(data_parts[8])) if data_parts[8] else 0,
                'turnover': float(data_parts[9]) if data_parts[9] else 0,
                'timestamp': f"{data_parts[30]} {data_parts[31]}" if len(data_parts) > 31 else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"获取{symbol}实时数据失败: {e}")
            return {}
    
    def get_daily_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据 (新浪不直接提供历史数据接口，返回空DataFrame)"""
        self.logger.warning("新浪财经数据源不支持历史数据获取")
        return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        try:
            real_time = self.get_real_time_price(symbol)
            
            if not real_time:
                return {}
            
            # 计算涨跌幅
            price = real_time.get('price', 0)
            prev_close = real_time.get('prev_close', 0)
            
            if prev_close > 0:
                change = price - prev_close
                pct_change = (change / prev_close) * 100
            else:
                change = 0
                pct_change = 0
            
            return {
                'symbol': symbol,
                'name': real_time.get('name', ''),
                'market': 'SH' if symbol.startswith('6') else 'SZ',
                'price': price,
                'change': change,
                'pct_change': pct_change,
                'volume': real_time.get('volume', 0),
                'turnover': real_time.get('turnover', 0),
                'is_active': True
            }
            
        except Exception as e:
            self.logger.error(f"获取{symbol}基本信息失败: {e}")
            return {}
    
    def get_market_status(self) -> Dict:
        """获取市场状态"""
        try:
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            
            # 简单的市场时间判断
            is_trading = False
            if now.weekday() < 5:  # 周一到周五
                if ('09:30' <= current_time <= '11:30') or ('13:00' <= current_time <= '15:00'):
                    is_trading = True
            
            return {
                'is_trading': is_trading,
                'market_time': current_time,
                'status': '交易中' if is_trading else '休市',
                'data_source': self.name
            }
            
        except Exception as e:
            self.logger.error(f"获取市场状态失败: {e}")
            return {
                'is_trading': False,
                'market_time': '',
                'status': '未知',
                'data_source': self.name
            }
    
    def _convert_symbol(self, symbol: str) -> str:
        """转换股票代码为新浪格式"""
        if symbol.startswith('6'):
            return f"sh{symbol}"  # 上海
        else:
            return f"sz{symbol}"  # 深圳
    
    def get_price_data(self, symbol: str, start_date: str = None, 
                      end_date: str = None, period: str = "daily") -> pd.DataFrame:
        """获取价格数据（新浪不支持历史数据）"""
        return self.get_daily_prices(symbol, start_date or '', end_date or '')
    
    def get_realtime_data(self, symbols: List[str]) -> pd.DataFrame:
        """获取实时数据"""
        data_list = []
        for symbol in symbols:
            real_time = self.get_real_time_price(symbol)
            if real_time:
                data_list.append(real_time)
        
        return pd.DataFrame(data_list)