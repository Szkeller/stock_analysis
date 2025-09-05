"""
腾讯股票数据源
提供实时行情数据
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from .base import BaseDataSource


class QQStockDataSource(BaseDataSource):
    """腾讯股票数据源"""
    
    def __init__(self):
        super().__init__("qqstock")
        self.description = "腾讯股票 - 实时行情数据"
        self.base_url = "http://qt.gtimg.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'http://gu.qq.com/'
        })
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """测试连接"""
        try:
            # 测试获取平安银行的实时数据
            url = f"{self.base_url}/q=sz000001"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200 and 'v_sz000001' in response.text:
                self.logger.info("腾讯股票数据源连接成功")
                self.is_connected = True
                return True
            
            self.logger.warning("腾讯股票数据源连接失败")
            self.is_connected = False
            return False
            
        except Exception as e:
            self.logger.error(f"腾讯股票数据源连接测试失败: {e}")
            self.is_connected = False
            return False
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        try:
            # 腾讯没有直接的股票列表接口，返回常见股票
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
            self.logger.info(f"腾讯数据源提供{len(df)}只常见股票")
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_real_time_price(self, symbol: str) -> Dict:
        """获取实时价格"""
        try:
            qq_symbol = self._convert_symbol(symbol)
            url = f"{self.base_url}/q={qq_symbol}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            # 解析腾讯返回的数据
            content = response.text
            
            # 腾讯数据格式: v_sz000001="51~平安银行~000001~13.46~13.38~13.50~..."
            start_pos = content.find('"') + 1
            end_pos = content.rfind('"')
            
            if start_pos <= 0 or end_pos <= start_pos:
                return {}
            
            data_str = content[start_pos:end_pos]
            data_parts = data_str.split('~')
            
            if len(data_parts) < 50:  # 腾讯数据字段很多
                return {}
            
            # 腾讯数据格式解析
            try:
                return {
                    'symbol': symbol,
                    'name': data_parts[1],
                    'price': float(data_parts[3]) if data_parts[3] else 0,
                    'prev_close': float(data_parts[4]) if data_parts[4] else 0,
                    'open': float(data_parts[5]) if data_parts[5] else 0,
                    'high': float(data_parts[33]) if len(data_parts) > 33 and data_parts[33] else 0,
                    'low': float(data_parts[34]) if len(data_parts) > 34 and data_parts[34] else 0,
                    'volume': int(float(data_parts[6])) if data_parts[6] else 0,
                    'turnover': float(data_parts[37]) if len(data_parts) > 37 and data_parts[37] else 0,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            except (ValueError, IndexError) as e:
                self.logger.error(f"解析腾讯数据失败: {e}")
                return {}
            
        except Exception as e:
            self.logger.error(f"获取{symbol}实时数据失败: {e}")
            return {}
    
    def get_daily_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        try:
            qq_symbol = self._convert_symbol(symbol)
            
            # 腾讯K线数据接口
            url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {
                'param': f"{qq_symbol},day,{start_date},{end_date},320,qfq",
                '_var': 'kline_dayqfq',
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                return pd.DataFrame()
            
            # 解析返回数据
            content = response.text
            start_pos = content.find('{')
            if start_pos < 0:
                return pd.DataFrame()
                
            json_str = content[start_pos:]
            data = json.loads(json_str)
            
            if 'data' not in data or not data['data']:
                return pd.DataFrame()
            
            stock_data = data['data'][qq_symbol]
            if 'day' not in stock_data:
                return pd.DataFrame()
            
            # 解析K线数据
            klines = stock_data['day']
            rows = []
            
            for kline in klines:
                if len(kline) >= 6:
                    rows.append({
                        'date': kline[0],
                        'open': float(kline[1]),
                        'close': float(kline[2]),
                        'high': float(kline[3]),
                        'low': float(kline[4]),
                        'volume': int(float(kline[5])),
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
        """转换股票代码为腾讯格式"""
        if symbol.startswith('6'):
            return f"sh{symbol}"  # 上海
        else:
            return f"sz{symbol}"  # 深圳
    
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