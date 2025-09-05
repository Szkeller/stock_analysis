"""
AKShare数据源实现
免费的中国金融数据接口
"""

import akshare as ak
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time
import logging

from .base import BaseDataSource


class AKShareDataSource(BaseDataSource):
    """AKShare数据源"""
    
    def __init__(self):
        super().__init__("akshare")
        self.logger = logging.getLogger(__name__)
        self._stock_list_cache = None
        self._cache_time = None
        self._cache_expire = 3600  # 缓存1小时
    
    def connect(self) -> bool:
        """连接AKShare"""
        try:
            # 测试连接 - 获取股票列表
            test_data = ak.stock_zh_a_spot_em()
            if test_data is not None and not test_data.empty:
                self.is_connected = True
                self.logger.info("AKShare连接成功")
                return True
        except Exception as e:
            self.logger.error(f"AKShare连接失败: {e}")
            self.is_connected = False
        return False
    
    def get_stock_list(self) -> pd.DataFrame:
        """获取A股股票列表"""
        try:
            # 检查缓存
            if (self._stock_list_cache is not None and 
                self._cache_time is not None and 
                time.time() - self._cache_time < self._cache_expire):
                return self._stock_list_cache
            
            # 获取A股实时行情数据
            df = ak.stock_zh_a_spot_em()
            
            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    '代码': 'symbol',
                    '名称': 'name',
                    '最新价': 'price',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '最高': 'high',
                    '最低': 'low',
                    '今开': 'open',
                    '昨收': 'pre_close',
                    '量比': 'volume_ratio',
                    '换手率': 'turnover_rate',
                    '市盈率-动态': 'pe_ttm',
                    '市净率': 'pb'
                })
                
                # 缓存结果
                self._stock_list_cache = df
                self._cache_time = time.time()
                
                self.logger.info(f"获取股票列表成功，共{len(df)}只股票")
                return df
        
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
        
        return pd.DataFrame()
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        try:
            # 获取股票基本信息
            info = {}
            
            # 从股票列表中获取基本信息
            stock_list = self.get_stock_list()
            if not stock_list.empty:
                stock_data = stock_list[stock_list['symbol'] == symbol]
                if not stock_data.empty:
                    stock_row = stock_data.iloc[0]
                    info = {
                        'symbol': symbol,
                        'name': stock_row.get('name', ''),
                        'price': stock_row.get('price', 0),
                        'pct_change': stock_row.get('pct_change', 0),
                        'pe_ttm': stock_row.get('pe_ttm', 0),
                        'pb': stock_row.get('pb', 0),
                        'market_cap': stock_row.get('amount', 0) * 10000,  # 估算市值
                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            # 尝试获取更多基本信息
            try:
                # 获取股票基本面信息
                fundamental = ak.stock_individual_info_em(symbol=symbol)
                if fundamental is not None and not fundamental.empty:
                    # 将fundamental数据添加到info中
                    for _, row in fundamental.iterrows():
                        key = row.get('item', '')
                        value = row.get('value', '')
                        if key == '总市值':
                            info['total_market_cap'] = value
                        elif key == '流通市值':
                            info['float_market_cap'] = value
                        elif key == '行业':
                            info['industry'] = value
            except:
                pass  # 如果获取基本面信息失败，忽略
            
            return info
        
        except Exception as e:
            self.logger.error(f"获取股票{symbol}信息失败: {e}")
            return {}
    
    def get_price_data(self, symbol: str, start_date: str = None, 
                      end_date: str = None, period: str = "daily") -> pd.DataFrame:
        """获取价格数据"""
        try:
            # 设置默认日期
            if end_date is None:
                end_date = datetime.now().strftime('%Y%m%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            # 根据周期获取数据
            if period == "daily":
                df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, 
                                       end_date=end_date, adjust="qfq")
            elif period == "weekly":
                df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, 
                                       end_date=end_date, period="weekly", adjust="qfq")
            elif period == "monthly":
                df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, 
                                       end_date=end_date, period="monthly", adjust="qfq")
            else:
                df = ak.stock_zh_a_hist(symbol=symbol, start_date=start_date, 
                                       end_date=end_date, adjust="qfq")
            
            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'pct_change',
                    '涨跌额': 'change',
                    '换手率': 'turnover_rate'
                })
                
                # 确保日期列是datetime类型
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
        """获取实时数据"""
        try:
            # 获取所有股票的实时数据
            all_data = self.get_stock_list()
            
            if not all_data.empty and symbols:
                # 筛选指定的股票
                filtered_data = all_data[all_data['symbol'].isin(symbols)]
                
                # 添加时间戳
                filtered_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                self.logger.info(f"获取{len(symbols)}只股票实时数据成功")
                return filtered_data
        
        except Exception as e:
            self.logger.error(f"获取实时数据失败: {e}")
        
        return pd.DataFrame()
    
    def get_market_status(self) -> Dict:
        """获取市场状态"""
        base_status = super().get_market_status()
        
        try:
            # 尝试获取市场的额外信息
            # 获取上证指数信息
            sz_index = ak.stock_zh_index_spot_em(symbol="sh000001")
            if sz_index is not None and not sz_index.empty:
                base_status['shanghai_index'] = {
                    'value': sz_index.iloc[0]['最新价'],
                    'change': sz_index.iloc[0]['涨跌额'],
                    'pct_change': sz_index.iloc[0]['涨跌幅']
                }
        except:
            pass
        
        return base_status
    
    def get_industry_data(self) -> pd.DataFrame:
        """获取行业数据"""
        try:
            df = ak.stock_board_industry_summary_ths()
            if df is not None and not df.empty:
                self.logger.info(f"获取行业数据成功，共{len(df)}个行业")
                return df
        except Exception as e:
            self.logger.error(f"获取行业数据失败: {e}")
        return pd.DataFrame()
    
    def get_concept_data(self) -> pd.DataFrame:
        """获取概念板块数据"""
        try:
            df = ak.stock_board_concept_summary_ths()
            if df is not None and not df.empty:
                self.logger.info(f"获取概念数据成功，共{len(df)}个概念")
                return df
        except Exception as e:
            self.logger.error(f"获取概念数据失败: {e}")
        return pd.DataFrame()