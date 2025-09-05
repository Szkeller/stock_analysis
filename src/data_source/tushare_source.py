"""
Tushare数据源实现
专业的金融数据接口（需要token）
"""

import tushare as ts
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import os

from .base import BaseDataSource


class TushareDataSource(BaseDataSource):
    """Tushare数据源"""
    
    def __init__(self, token: str = None):
        super().__init__("tushare")
        self.token = token or os.getenv('TUSHARE_TOKEN')
        self.pro = None
        self.logger = logging.getLogger(__name__)
        
        if not self.token:
            self.logger.warning("未设置Tushare token，请在环境变量中设置TUSHARE_TOKEN")
    
    def connect(self) -> bool:
        """连接Tushare"""
        try:
            if not self.token:
                self.logger.error("Tushare token未设置")
                return False
            
            # 设置token并获取接口
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            
            # 测试连接
            test_data = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
            
            if test_data is not None and not test_data.empty:
                self.is_connected = True
                self.logger.info("Tushare连接成功")
                return True
        
        except Exception as e:
            self.logger.error(f"Tushare连接失败: {e}")
            self.is_connected = False
        
        return False
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            if not self.pro:
                raise Exception("Tushare未连接")
            
            # 获取基础股票信息
            df = self.pro.stock_basic(exchange='', 
                                     list_status='L', 
                                     fields='ts_code,symbol,name,area,industry,market,list_date')
            
            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    'ts_code': 'ts_code',
                    'symbol': 'symbol',
                    'name': 'name',
                    'area': 'area',
                    'industry': 'industry',
                    'market': 'market',
                    'list_date': 'list_date'
                })
                
                self.logger.info(f"获取股票列表成功，共{len(df)}只股票")
                return df
        
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
        
        return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        try:
            if not self.pro:
                raise Exception("Tushare未连接")
            
            # 转换symbol格式
            ts_code = self._convert_symbol_to_ts_code(symbol)
            
            # 获取基本信息
            basic_info = self.pro.stock_basic(ts_code=ts_code, 
                                            fields='ts_code,symbol,name,area,industry,market,list_date,delist_date')
            
            info = {}
            if basic_info is not None and not basic_info.empty:
                row = basic_info.iloc[0]
                info = {
                    'symbol': row['symbol'],
                    'name': row['name'],
                    'area': row['area'],
                    'industry': row['industry'],
                    'market': row['market'],
                    'list_date': row['list_date'],
                    'delist_date': row['delist_date']
                }
            
            # 获取最新交易数据
            try:
                latest_data = self.pro.daily(ts_code=ts_code, 
                                           start_date=(datetime.now() - timedelta(days=5)).strftime('%Y%m%d'),
                                           end_date=datetime.now().strftime('%Y%m%d'))
                
                if latest_data is not None and not latest_data.empty:
                    latest = latest_data.iloc[0]
                    info.update({
                        'price': latest['close'],
                        'pct_change': latest['pct_chg'],
                        'volume': latest['vol'],
                        'amount': latest['amount'],
                        'update_time': latest['trade_date']
                    })
            except:
                pass
            
            return info
        
        except Exception as e:
            self.logger.error(f"获取股票{symbol}信息失败: {e}")
            return {}
    
    def get_price_data(self, symbol: str, start_date: str = None, 
                      end_date: str = None, period: str = "daily") -> pd.DataFrame:
        """获取价格数据"""
        try:
            if not self.pro:
                raise Exception("Tushare未连接")
            
            # 转换symbol格式
            ts_code = self._convert_symbol_to_ts_code(symbol)
            
            # 设置默认日期
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 获取数据
            if period == "daily":
                df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            elif period == "weekly":
                df = self.pro.weekly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            elif period == "monthly":
                df = self.pro.monthly(ts_code=ts_code, start_date=start_date, end_date=end_date)
            else:
                df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    'trade_date': 'date',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'vol': 'volume',
                    'amount': 'amount',
                    'pct_chg': 'pct_change',
                    'change': 'change'
                })
                
                # 转换日期格式
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                # 添加symbol列
                df['symbol'] = symbol
                
                self.logger.info(f"获取股票{symbol}价格数据成功，共{len(df)}条记录")
                return df
        
        except Exception as e:
            self.logger.error(f"获取股票{symbol}价格数据失败: {e}")
        
        return pd.DataFrame()
    
    def get_realtime_data(self, symbols: List[str]) -> pd.DataFrame:
        """获取实时数据（Tushare需要额外接口权限）"""
        try:
            if not self.pro:
                raise Exception("Tushare未连接")
            
            # Tushare的实时数据需要特殊权限
            # 这里使用最新的日线数据作为替代
            all_data = []
            for symbol in symbols:
                ts_code = self._convert_symbol_to_ts_code(symbol)
                data = self.pro.daily(ts_code=ts_code, 
                                    start_date=(datetime.now() - timedelta(days=5)).strftime('%Y%m%d'),
                                    end_date=datetime.now().strftime('%Y%m%d'))
                
                if data is not None and not data.empty:
                    latest = data.iloc[0]
                    latest['symbol'] = symbol
                    latest['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    all_data.append(latest)
            
            if all_data:
                df = pd.DataFrame(all_data)
                self.logger.info(f"获取{len(symbols)}只股票最新数据成功")
                return df
        
        except Exception as e:
            self.logger.error(f"获取实时数据失败: {e}")
        
        return pd.DataFrame()
    
    def _convert_symbol_to_ts_code(self, symbol: str) -> str:
        """转换股票代码为Tushare格式"""
        if len(symbol) == 6:
            if symbol.startswith('60') or symbol.startswith('68'):
                return f"{symbol}.SH"
            elif symbol.startswith('00') or symbol.startswith('30'):
                return f"{symbol}.SZ"
        return symbol
    
    def get_financial_data(self, symbol: str, year: str = None) -> pd.DataFrame:
        """获取财务数据"""
        try:
            if not self.pro:
                raise Exception("Tushare未连接")
            
            ts_code = self._convert_symbol_to_ts_code(symbol)
            
            # 获取利润表
            income = self.pro.income(ts_code=ts_code, 
                                   start_date=f"{year or datetime.now().year}0101",
                                   end_date=f"{year or datetime.now().year}1231")
            
            # 获取资产负债表
            balancesheet = self.pro.balancesheet(ts_code=ts_code,
                                                start_date=f"{year or datetime.now().year}0101",
                                                end_date=f"{year or datetime.now().year}1231")
            
            # 获取现金流量表
            cashflow = self.pro.cashflow(ts_code=ts_code,
                                       start_date=f"{year or datetime.now().year}0101",
                                       end_date=f"{year or datetime.now().year}1231")
            
            return {
                'income': income,
                'balancesheet': balancesheet,
                'cashflow': cashflow
            }
        
        except Exception as e:
            self.logger.error(f"获取财务数据失败: {e}")
            return {}
    
    def get_fund_flow(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取资金流向数据"""
        try:
            if not self.pro:
                raise Exception("Tushare未连接")
            
            ts_code = self._convert_symbol_to_ts_code(symbol)
            
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = self.pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is not None and not df.empty:
                self.logger.info(f"获取股票{symbol}资金流向数据成功")
                return df
        
        except Exception as e:
            self.logger.error(f"获取资金流向数据失败: {e}")
        
        return pd.DataFrame()