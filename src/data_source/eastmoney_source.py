"""
东方财富数据源
免费可靠的股票数据获取
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from .base import BaseDataSource


class EastMoneyDataSource(BaseDataSource):
    """东方财富数据源"""
    
    def __init__(self):
        super().__init__("eastmoney")
        self.description = "东方财富 - 免费股票数据接口"
        self.base_url = "http://push2.eastmoney.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """测试连接"""
        try:
            # 测试获取一只股票的基本信息
            url = f"{self.base_url}/api/qt/stock/get"
            params = {
                'secid': '0.000001',
                'fields': 'f58,f57,f43,f169,f170'
            }
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('rc') == 0:  # 东方财富的成功返回码
                    self.logger.info("东方财富数据源连接成功")
                    self.is_connected = True
                    return True
            
            self.logger.warning("东方财富数据源连接失败")
            self.is_connected = False
            return False
            
        except Exception as e:
            self.logger.error(f"东方财富数据源连接测试失败: {e}")
            self.is_connected = False
            return False
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        try:
            # 获取A股列表
            url = f"{self.base_url}/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': '5000',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # A股
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"获取股票列表失败，状态码: {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            if data.get('rc') != 0 or not data.get('data', {}).get('diff'):
                self.logger.error("东方财富返回数据格式错误")
                return pd.DataFrame()
            
            stocks = []
            for item in data['data']['diff']:
                symbol = item.get('f12', '')
                name = item.get('f14', '')
                
                if symbol and name:
                    stocks.append({
                        'symbol': symbol,
                        'name': name,
                        'market': 'SH' if symbol.startswith('6') else 'SZ'
                    })
            
            df = pd.DataFrame(stocks)
            self.logger.info(f"获取到{len(df)}只股票信息")
            return df
            
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_daily_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        try:
            # 转换股票代码格式
            secid = self._convert_symbol(symbol)
            
            # 东方财富的历史数据接口
            url = f"{self.base_url}/api/qt/stock/kline/get"
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K线
                'fqt': '1',    # 前复权
                'beg': start_date,
                'end': end_date,
                'smplmt': '240',  # 数据数量限制
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"获取{symbol}历史数据失败，状态码: {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            # 添加详细的调试信息
            if data.get('rc') != 0:
                self.logger.warning(f"股票{symbol}历史数据API返回错误码: {data.get('rc')}, 消息: {data.get('msg', 'N/A')}")
                return self._try_alternative_history_api(symbol, start_date, end_date)
            
            if not data.get('data'):
                self.logger.warning(f"股票{symbol}无数据字段")
                return self._try_alternative_history_api(symbol, start_date, end_date)
            
            if not data.get('data', {}).get('klines'):
                self.logger.warning(f"股票{symbol}无K线数据")
                return self._try_alternative_history_api(symbol, start_date, end_date)
            
            # 解析K线数据
            klines = data['data']['klines']
            rows = []
            
            for kline in klines:
                parts = kline.split(',')
                if len(parts) >= 11:
                    try:
                        rows.append({
                            'date': parts[0],
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'high': float(parts[3]),
                            'low': float(parts[4]),
                            'volume': float(parts[5]),
                            'turnover': float(parts[6]),
                            'pct_change': float(parts[8]),
                            'symbol': symbol
                        })
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"解析K线数据失败: {e}, 数据: {kline}")
                        continue
            
            df = pd.DataFrame(rows)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                self.logger.info(f"获取到{symbol} {len(df)}条历史数据")
            else:
                self.logger.warning(f"股票{symbol}解析后无有效历史数据")
                return self._try_alternative_history_api(symbol, start_date, end_date)
            
            return df
            
        except Exception as e:
            self.logger.error(f"获取{symbol}历史数据失败: {e}")
            return self._try_alternative_history_api(symbol, start_date, end_date)
    
    def _try_alternative_history_api(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """尝试备用的历史数据获取接口"""
        try:
            # 使用备用接口
            secid = self._convert_symbol(symbol)
            url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
            
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
                'klt': '101',  # 日K线
                'fqt': '0',    # 不复权
                'beg': '0',    # 从最早开始
                'end': '20500101',  # 到未来日期
                'smplmt': '460',  # 增加数据限制
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"备用接口获取{symbol}历史数据失败，状态码: {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            
            if data.get('rc') != 0 or not data.get('data', {}).get('klines'):
                self.logger.warning(f"股票{symbol}备用接口也无历史数据")
                return pd.DataFrame()
            
            # 解析备用接口数据
            klines = data['data']['klines']
            rows = []
            
            for kline in klines:
                parts = kline.split(',')
                if len(parts) >= 8:
                    try:
                        date_str = parts[0]
                        # 过滤日期范围
                        if start_date <= date_str.replace('-', '') <= end_date:
                            rows.append({
                                'date': parts[0],
                                'open': float(parts[1]),
                                'close': float(parts[2]),
                                'high': float(parts[3]),
                                'low': float(parts[4]),
                                'volume': float(parts[5]),
                                'turnover': float(parts[6]) if len(parts) > 6 else 0,
                                'pct_change': 0,  # 备用接口可能没有涨跌幅
                                'symbol': symbol
                            })
                    except (ValueError, IndexError) as e:
                        continue
            
            df = pd.DataFrame(rows)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                # 计算涨跌幅
                df['pct_change'] = df['close'].pct_change() * 100
                df.loc[df['pct_change'].isna(), 'pct_change'] = 0
                
                self.logger.info(f"备用接口获取到{symbol} {len(df)}条历史数据")
                return df
            else:
                self.logger.warning(f"股票{symbol}备用接口解析后仍无有效数据")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"备用接口获取{symbol}历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_real_time_price(self, symbol: str) -> Dict:
        """获取实时价格"""
        try:
            secid = self._convert_symbol(symbol)
            
            url = f"{self.base_url}/api/qt/stock/get"
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields': 'f58,f57,f43,f169,f170,f46,f44,f51,f168,f47,f164,f163,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,f268,f255,f256,f257,f258'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return {}
            
            data = response.json()
            
            if data.get('rc') != 0 or not data.get('data'):
                return {}
            
            stock_data = data['data']
            
            return {
                'symbol': symbol,
                'name': stock_data.get('f58', ''),
                'price': stock_data.get('f43', 0) / 100.0,  # 当前价
                'change': stock_data.get('f169', 0) / 100.0,  # 涨跌额
                'pct_change': stock_data.get('f170', 0) / 100.0,  # 涨跌幅
                'open': stock_data.get('f46', 0) / 100.0,  # 开盘价
                'high': stock_data.get('f44', 0) / 100.0,  # 最高价
                'low': stock_data.get('f45', 0) / 100.0,   # 最低价
                'volume': stock_data.get('f47', 0),        # 成交量
                'turnover': stock_data.get('f48', 0),      # 成交额
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"获取{symbol}实时数据失败: {e}")
            return {}
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        try:
            # 先获取实时数据
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
        """转换股票代码为东方财富格式"""
        if symbol.startswith('6'):
            return f"1.{symbol}"  # 上海
        else:
            return f"0.{symbol}"  # 深圳
    
    def get_price_data(self, symbol: str, start_date: str = None, 
                      end_date: str = None, period: str = "daily") -> pd.DataFrame:
        """获取价格数据（对应get_daily_prices）"""
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