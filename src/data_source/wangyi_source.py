"""
网易财经数据源
提供股票行情数据
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from .base import BaseDataSource


class WangYiDataSource(BaseDataSource):
    """网易财经数据源"""
    
    def __init__(self):
        super().__init__("wangyi")
        self.description = "网易财经 - 股票行情数据"
        self.base_url = "http://api.money.126.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'http://money.163.com/'
        })
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """测试连接"""
        try:
            # 测试获取平安银行的实时数据
            url = f"{self.base_url}/data/feed/0000001,money.api"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                self.logger.info("网易财经数据源连接成功")
                self.is_connected = True
                return True
            
            self.logger.warning("网易财经数据源连接失败")
            self.is_connected = False
            return False
            
        except Exception as e:
            self.logger.error(f"网易财经数据源连接测试失败: {e}")
            self.is_connected = False
            return False
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        try:
            # 网易没有公开的股票列表接口，返回常见股票
            common_stocks = [
                ('000001', '平安银行', 'SZ'),
                ('000002', '万科A', 'SZ'),
                ('000858', '五粮液', 'SZ'),
                ('002415', '海康威视', 'SZ'),
                ('002594', '比亚迪', 'SZ'),
                ('600000', '浦发银行', 'SH'),
                ('600036', '招商银行', 'SH'),
                ('600519', '贵州茅台', 'SH'),
                ('600887', '伊利股份', 'SH'),
                ('601318', '中国平安', 'SH'),
            ]
            
            stocks = []
            for symbol, name, market in common_stocks:
                stocks.append({
                    'symbol': symbol,
                    'name': name,
                    'market': market
                })
            
            df = pd.DataFrame(stocks)
            self.logger.info(f"网易数据源提供{len(df)}只常见股票")
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_real_time_price(self, symbol: str) -> Dict:
        """获取实时价格"""
        try:
            wy_symbol = self._convert_symbol(symbol)
            url = f"{self.base_url}/data/feed/{wy_symbol},money.api"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            # 网易返回的是JSONP格式，需要处理
            content = response.text
            
            # 去掉JSONP的包装
            start_pos = content.find('{')
            end_pos = content.rfind('}') + 1
            
            if start_pos < 0 or end_pos <= start_pos:
                return {}
            
            json_str = content[start_pos:end_pos]
            data = json.loads(json_str)
            
            stock_key = list(data.keys())[0] if data else None
            if not stock_key or stock_key not in data:
                return {}
            
            stock_data = data[stock_key]
            
            return {
                'symbol': symbol,
                'name': stock_data.get('name', ''),
                'price': float(stock_data.get('price', 0)),
                'change': float(stock_data.get('updown', 0)),
                'pct_change': float(stock_data.get('percent', 0)),
                'open': float(stock_data.get('open', 0)),
                'high': float(stock_data.get('high', 0)),
                'low': float(stock_data.get('low', 0)),
                'volume': int(float(stock_data.get('volume', 0))),
                'turnover': float(stock_data.get('turnover', 0)),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"获取{symbol}实时数据失败: {e}")
            return {}
    
    def get_daily_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        try:
            wy_symbol = self._convert_symbol(symbol)
            
            # 网易K线数据接口
            url = f"{self.base_url}/data/feed/{wy_symbol}/day/times/{start_date}/{end_date}.json"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                return pd.DataFrame()
            
            data = response.json()
            
            if 'data' not in data:
                return pd.DataFrame()
            
            # 解析K线数据
            klines = data['data']
            rows = []
            
            for date_str, kline in klines.items():
                if isinstance(kline, list) and len(kline) >= 4:
                    rows.append({
                        'date': date_str,
                        'close': float(kline[0]),
                        'high': float(kline[1]),
                        'low': float(kline[2]),
                        'open': float(kline[3]),
                        'volume': int(float(kline[4])) if len(kline) > 4 else 0,
                        'turnover': float(kline[5]) if len(kline) > 5 else 0,
                        'symbol': symbol
                    })
            
            df = pd.DataFrame(rows)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                # 计算涨跌幅
                df['pct_change'] = df['close'].pct_change() * 100
                self.logger.info(f"获取到{symbol} {len(df)}条历史数据")
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取{symbol}历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        try:
            real_time = self.get_real_time_price(symbol)
            
            if not real_time:
                return {}
            
            return {
                'symbol': symbol,
                'name': real_time.get('name', ''),
                'market': 'SH' if symbol.startswith('6') else 'SZ',
                'price': real_time.get('price', 0),
                'change': real_time.get('change', 0),
                'pct_change': real_time.get('pct_change', 0),
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
        """转换股票代码为网易格式"""
        if symbol.startswith('6'):
            return f"1{symbol}"  # 上海股票
        else:
            return f"0{symbol}"  # 深圳股票
    
    def get_price_data(self, symbol: str, start_date: str = None, 
                      end_date: str = None, period: str = "daily") -> pd.DataFrame:
        """获取价格数据"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        
        return self.get_daily_prices(symbol, start_date, end_date)
    
    def get_realtime_data(self, symbols: List[str]) -> pd.DataFrame:
        """获取实时数据"""
        data_list = []
        for symbol in symbols:
            real_time = self.get_real_time_price(symbol)
            if real_time:
                data_list.append(real_time)
        
        return pd.DataFrame(data_list)