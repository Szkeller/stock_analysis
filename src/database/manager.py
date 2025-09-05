"""
数据库操作类
提供数据库的CRUD操作接口
"""

from typing import List, Dict, Optional, Union
import pandas as pd
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc, and_, or_
from datetime import datetime, timedelta
import logging
import os

from .models import (
    Base, Stock, DailyPrice, RealtimePrice, TechnicalIndicator, 
    Watchlist, Alert, Strategy, UserConfig
)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # 确保data目录存在
            data_dir = "/Volumes/WDSSD/stock_analysis/data"
            os.makedirs(data_dir, exist_ok=True)
            database_url = f"sqlite:///{data_dir}/stock_analysis.db"
        
        self.database_url = database_url
        # 添加连接池配置，避免数据库锁定问题
        self.engine = create_engine(
            database_url, 
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={'check_same_thread': False, 'timeout': 10}
        )
        Base.metadata.create_all(self.engine)
        
        self.Session = sessionmaker(bind=self.engine)
        self.logger = logging.getLogger(__name__)
    
    def get_session(self):
        """获取新的数据库会话"""
        return self.Session()
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
    # 股票基本信息操作
    def save_stock(self, stock_data: Dict) -> bool:
        """保存股票基本信息"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(Stock).filter_by(symbol=stock_data['symbol']).first()
            
            if existing:
                # 更新现有记录
                for key, value in stock_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.now()
            else:
                # 创建新记录
                stock = Stock(**stock_data)
                session.add(stock)
            
            session.commit()
            return True
        
        except Exception as e:
            self.logger.error(f"保存股票信息失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_stock(self, symbol: str) -> Optional[Dict]:
        """获取股票信息"""
        session = self.get_session()
        try:
            stock = session.query(Stock).filter_by(symbol=symbol).first()
            if stock:
                return {
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'market': stock.market,
                    'industry': stock.industry,
                    'area': stock.area,
                    'list_date': stock.list_date,
                    'is_active': stock.is_active
                }
        except Exception as e:
            self.logger.error(f"获取股票信息失败: {e}")
        finally:
            session.close()
        return None
    
    def get_all_stocks(self, active_only: bool = True) -> List[Dict]:
        """获取所有股票列表"""
        session = self.get_session()
        try:
            query = session.query(Stock)
            if active_only:
                query = query.filter_by(is_active=True)
            
            stocks = query.all()
            return [{
                'symbol': stock.symbol,
                'name': stock.name,
                'market': stock.market,
                'industry': stock.industry,
                'area': stock.area
            } for stock in stocks]
        
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            return []
        finally:
            session.close()
    
    # 价格数据操作
    def save_daily_prices(self, price_data: Union[Dict, List[Dict], pd.DataFrame]) -> bool:
        """保存日线价格数据"""
        session = self.get_session()
        try:
            if isinstance(price_data, pd.DataFrame):
                price_data = price_data.to_dict('records')
            elif isinstance(price_data, dict):
                price_data = [price_data]
            
            for data in price_data:
                # 处理Pandas Timestamp类型问题
                if 'date' in data and hasattr(data['date'], 'to_pydatetime'):
                    data['date'] = data['date'].to_pydatetime().date()
                elif 'date' in data and hasattr(data['date'], 'date'):
                    data['date'] = data['date'].date()
                
                # 检查是否已存在
                existing = session.query(DailyPrice).filter_by(
                    symbol=data['symbol'], 
                    date=data['date']
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # 创建新记录
                    daily_price = DailyPrice(**data)
                    session.add(daily_price)
            
            session.commit()
            return True
        
        except Exception as e:
            self.logger.error(f"保存日线数据失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_daily_prices(self, symbol: str, start_date: str = None, 
                        end_date: str = None, limit: int = None) -> pd.DataFrame:
        """获取日线价格数据"""
        session = self.get_session()
        try:
            query = session.query(DailyPrice).filter_by(symbol=symbol)
            
            if start_date:
                query = query.filter(DailyPrice.date >= start_date)
            if end_date:
                query = query.filter(DailyPrice.date <= end_date)
            
            query = query.order_by(DailyPrice.date)
            
            if limit:
                query = query.limit(limit)
            
            prices = query.all()
            
            data = []
            for price in prices:
                data.append({
                    'symbol': price.symbol,
                    'date': price.date,
                    'open': price.open,
                    'close': price.close,
                    'high': price.high,
                    'low': price.low,
                    'volume': price.volume,
                    'amount': price.amount,
                    'pct_change': price.pct_change,
                    'change': price.change,
                    'turnover_rate': price.turnover_rate
                })
            
            return pd.DataFrame(data)
        
        except Exception as e:
            self.logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def save_realtime_price(self, price_data: Dict) -> bool:
        """保存实时价格数据"""
        session = self.get_session()
        try:
            realtime_price = RealtimePrice(**price_data)
            session.add(realtime_price)
            session.commit()
            return True
        
        except Exception as e:
            self.logger.error(f"保存实时数据失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_latest_realtime_price(self, symbol: str) -> Optional[Dict]:
        """获取最新实时价格"""
        session = self.get_session()
        try:
            price = session.query(RealtimePrice).filter_by(symbol=symbol)\
                         .order_by(desc(RealtimePrice.timestamp)).first()
            
            if price:
                return {
                    'symbol': price.symbol,
                    'price': price.price,
                    'open': price.open,
                    'pre_close': price.pre_close,
                    'high': price.high,
                    'low': price.low,
                    'volume': price.volume,
                    'amount': price.amount,
                    'pct_change': price.pct_change,
                    'change': price.change,
                    'turnover_rate': price.turnover_rate,
                    'pe_ttm': price.pe_ttm,
                    'pb': price.pb,
                    'timestamp': price.timestamp
                }
        
        except Exception as e:
            self.logger.error(f"获取实时价格失败: {e}")
        finally:
            session.close()
        return None
    
    # 技术指标操作
    def save_technical_indicators(self, indicator_data: Union[Dict, List[Dict], pd.DataFrame]) -> bool:
        """保存技术指标数据"""
        session = self.get_session()
        try:
            if isinstance(indicator_data, pd.DataFrame):
                indicator_data = indicator_data.to_dict('records')
            elif isinstance(indicator_data, dict):
                indicator_data = [indicator_data]
            
            for data in indicator_data:
                # 处理Pandas Timestamp类型问题
                if 'date' in data and hasattr(data['date'], 'to_pydatetime'):
                    data['date'] = data['date'].to_pydatetime().date()
                elif 'date' in data and hasattr(data['date'], 'date'):
                    data['date'] = data['date'].date()
                    
                # 检查是否已存在
                existing = session.query(TechnicalIndicator).filter_by(
                    symbol=data['symbol'], 
                    date=data['date']
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # 创建新记录
                    indicator = TechnicalIndicator(**data)
                    session.add(indicator)
            
            session.commit()
            return True
        
        except Exception as e:
            self.logger.error(f"保存技术指标失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_technical_indicators(self, symbol: str, start_date: str = None, 
                               end_date: str = None) -> pd.DataFrame:
        """获取技术指标数据"""
        session = self.get_session()
        try:
            query = session.query(TechnicalIndicator).filter_by(symbol=symbol)
            
            if start_date:
                query = query.filter(TechnicalIndicator.date >= start_date)
            if end_date:
                query = query.filter(TechnicalIndicator.date <= end_date)
            
            query = query.order_by(TechnicalIndicator.date)
            indicators = query.all()
            
            data = []
            for indicator in indicators:
                data.append({
                    'symbol': indicator.symbol,
                    'date': indicator.date,
                    'ma5': indicator.ma5,
                    'ma10': indicator.ma10,
                    'ma20': indicator.ma20,
                    'ma60': indicator.ma60,
                    'macd': indicator.macd,
                    'macd_signal': indicator.macd_signal,
                    'macd_histogram': indicator.macd_histogram,
                    'rsi': indicator.rsi,
                    'kdj_k': indicator.kdj_k,
                    'kdj_d': indicator.kdj_d,
                    'kdj_j': indicator.kdj_j,
                    'boll_upper': indicator.boll_upper,
                    'boll_middle': indicator.boll_middle,
                    'boll_lower': indicator.boll_lower
                })
            
            return pd.DataFrame(data)
        
        except Exception as e:
            self.logger.error(f"获取技术指标失败: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    # 自选股操作
    def add_to_watchlist(self, symbol: str, name: str = None, notes: str = None, priority: int = 1) -> bool:
        """添加到自选股"""
        session = self.get_session()
        try:
            # 检查是否已存在
            existing = session.query(Watchlist).filter_by(symbol=symbol).first()
            
            if existing:
                existing.is_active = True
                existing.notes = notes or existing.notes
                existing.priority = priority
            else:
                watchlist_item = Watchlist(
                    symbol=symbol,
                    name=name,
                    notes=notes,
                    priority=priority
                )
                session.add(watchlist_item)
            
            session.commit()
            return True
        
        except Exception as e:
            self.logger.error(f"添加自选股失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def remove_from_watchlist(self, symbol: str) -> bool:
        """从自选股移除"""
        session = self.get_session()
        try:
            watchlist_item = session.query(Watchlist).filter_by(symbol=symbol).first()
            if watchlist_item:
                watchlist_item.is_active = False
                session.commit()
                return True
        
        except Exception as e:
            self.logger.error(f"移除自选股失败: {e}")
            session.rollback()
        finally:
            session.close()
        return False
    
    def get_watchlist(self, active_only: bool = True) -> List[Dict]:
        """获取自选股列表"""
        session = self.get_session()
        try:
            query = session.query(Watchlist)
            if active_only:
                query = query.filter_by(is_active=True)
            
            query = query.order_by(desc(Watchlist.priority), desc(Watchlist.added_date))
            watchlist = query.all()
            
            return [{
                'symbol': item.symbol,
                'name': item.name,
                'notes': item.notes,
                'priority': item.priority,
                'added_date': item.added_date
            } for item in watchlist]
        
        except Exception as e:
            self.logger.error(f"获取自选股失败: {e}")
            return []
        finally:
            session.close()
    
    # 预警操作
    def add_alert(self, symbol: str, alert_type: str, title: str, message: str, 
                 severity: str = 'INFO') -> bool:
        """添加预警"""
        session = self.get_session()
        try:
            alert = Alert(
                symbol=symbol,
                alert_type=alert_type,
                title=title,
                message=message,
                severity=severity
            )
            session.add(alert)
            session.commit()
            return True
        
        except Exception as e:
            self.logger.error(f"添加预警失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_alerts(self, symbol: str = None, unread_only: bool = False, 
                  limit: int = None) -> List[Dict]:
        """获取预警列表"""
        session = self.get_session()
        try:
            query = session.query(Alert)
            
            if symbol:
                query = query.filter_by(symbol=symbol)
            if unread_only:
                query = query.filter_by(is_read=False)
            
            query = query.order_by(desc(Alert.created_at))
            
            if limit:
                query = query.limit(limit)
            
            alerts = query.all()
            
            return [{
                'id': alert.id,
                'symbol': alert.symbol,
                'alert_type': alert.alert_type,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity,
                'is_read': alert.is_read,
                'created_at': alert.created_at
            } for alert in alerts]
        
        except Exception as e:
            self.logger.error(f"获取预警失败: {e}")
            return []
        finally:
            session.close()
    
    def mark_alert_read(self, alert_id: int) -> bool:
        """标记预警为已读"""
        session = self.get_session()
        try:
            alert = session.query(Alert).filter_by(id=alert_id).first()
            if alert:
                alert.is_read = True
                session.commit()
                return True
        
        except Exception as e:
            self.logger.error(f"标记预警已读失败: {e}")
            session.rollback()
        finally:
            session.close()
        return False
    
    # 配置操作
    def set_config(self, key: str, value: str, description: str = None) -> bool:
        """设置配置"""
        session = self.get_session()
        try:
            config = session.query(UserConfig).filter_by(key=key).first()
            
            if config:
                config.value = value
                config.description = description or config.description
                config.updated_at = datetime.now()
            else:
                config = UserConfig(key=key, value=value, description=description)
                session.add(config)
            
            session.commit()
            return True
        
        except Exception as e:
            self.logger.error(f"设置配置失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_config(self, key: str, default_value: str = None) -> str:
        """获取配置"""
        session = self.get_session()
        try:
            config = session.query(UserConfig).filter_by(key=key).first()
            return config.value if config else default_value
        
        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            return default_value
        finally:
            session.close()