"""
数据源工厂类
统一管理和创建数据源实例
"""

from typing import Dict, Optional, List
import logging
from .base import DataSourceManager
from .akshare_source import AKShareDataSource
from .tushare_source import TushareDataSource
from .eastmoney_source import EastMoneyDataSource
from .sina_source import SinaDataSource
from .qqstock_source import QQStockDataSource
from .wangyi_source import WangYiDataSource


class DataSourceFactory:
    """数据源工厂"""
    
    @staticmethod
    def create_data_source_manager(config: Optional[Dict] = None) -> DataSourceManager:
        """创建数据源管理器"""
        manager = DataSourceManager()
        logger = logging.getLogger(__name__)
        
        # 默认配置（启用所有数据源作为备用）
        default_config = {
            'akshare': {'enabled': True, 'priority': 3},
            'tushare': {'enabled': True, 'priority': 2, 'token': None},
            'eastmoney': {'enabled': True, 'priority': 1},
            'sina': {'enabled': True, 'priority': 4},
            'qqstock': {'enabled': True, 'priority': 5},
            'wangyi': {'enabled': True, 'priority': 6}
        }
        
        if config:
            # 合并配置，保持优先级设置
            for source_name, source_config in config.items():
                if source_name in default_config:
                    default_config[source_name].update(source_config)
                else:
                    default_config[source_name] = source_config
        
        # 按优先级排序数据源
        sorted_sources = sorted(default_config.items(), key=lambda x: x[1].get('priority', 99))
        
        # 添加各个数据源
        for source_name, source_config in sorted_sources:
            if not source_config.get('enabled', True):
                continue
                
            try:
                if source_name == 'akshare':
                    source = AKShareDataSource()
                elif source_name == 'tushare':
                    token = source_config.get('token')
                    source = TushareDataSource(token=token)
                elif source_name == 'eastmoney':
                    source = EastMoneyDataSource()
                elif source_name == 'sina':
                    source = SinaDataSource()
                elif source_name == 'qqstock':
                    source = QQStockDataSource()
                elif source_name == 'wangyi':
                    source = WangYiDataSource()
                else:
                    logger.warning(f"未知的数据源类型: {source_name}")
                    continue
                
                manager.add_source(source)
                logger.info(f"{source_name}数据源已添加")
                
            except Exception as e:
                logger.error(f"添加{source_name}数据源失败: {e}")
        
        return manager
    
    @staticmethod
    def get_available_sources() -> List[str]:
        """获取可用的数据源列表"""
        return ['eastmoney', 'tushare', 'akshare', 'sina', 'qqstock', 'wangyi']
    
    @staticmethod
    def get_source_info() -> Dict:
        """获取数据源信息"""
        return {
            'eastmoney': {
                'name': '东方财富',
                'description': '免费可靠的股票数据接口',
                'features': ['股票行情', '历史数据', '基本信息', '实时数据'],
                'free': True,
                'realtime': True,
                'priority': 1
            },
            'tushare': {
                'name': 'Tushare',
                'description': '专业的金融数据接口',
                'features': ['股票行情', '财务数据', '资金流向', '基本面数据'],
                'free': False,
                'realtime': False,
                'requires_token': True,
                'priority': 2
            },
            'akshare': {
                'name': 'AKShare',
                'description': '免费的中国金融数据接口',
                'features': ['股票行情', '基本信息', '行业数据', '概念数据'],
                'free': True,
                'realtime': True,
                'priority': 3
            },
            'sina': {
                'name': '新浪财经',
                'description': '实时股票行情数据',
                'features': ['实时数据', '分时数据'],
                'free': True,
                'realtime': True,
                'priority': 4
            },
            'qqstock': {
                'name': '腾讯股票',
                'description': '实时行情数据',
                'features': ['实时数据', '历史数据', 'K线数据'],
                'free': True,
                'realtime': True,
                'priority': 5
            },
            'wangyi': {
                'name': '网易财经',
                'description': '股票行情数据',
                'features': ['实时数据', '历史数据'],
                'free': True,
                'realtime': True,
                'priority': 6
            }
        }


# 全局数据源管理器实例
_global_manager: Optional[DataSourceManager] = None


def get_data_source_manager(config: Optional[Dict] = None) -> DataSourceManager:
    """获取全局数据源管理器"""
    global _global_manager
    
    if _global_manager is None:
        # 如果没有传入配置，使用config.py中的配置
        if config is None:
            try:
                import sys
                import os
                # 添加项目根目录到路径
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                sys.path.insert(0, project_root)
                from config import DATA_SOURCES
                config = DATA_SOURCES
            except ImportError:
                # 如果无法导入，使用默认配置
                config = {
                    'eastmoney': {'enabled': True, 'priority': 1},
                    'tushare': {'enabled': True, 'priority': 2, 'token': None},
                    'akshare': {'enabled': True, 'priority': 3},
                    'sina': {'enabled': True, 'priority': 4},
                    'qqstock': {'enabled': True, 'priority': 5},
                    'wangyi': {'enabled': True, 'priority': 6}
                }
        
        _global_manager = DataSourceFactory.create_data_source_manager(config)
        
        # 尝试连接所有数据源
        connection_results = _global_manager.connect_all()
        logger = logging.getLogger(__name__)
        
        connected_sources = []
        for source_name, connected in connection_results.items():
            if connected:
                logger.info(f"数据源 {source_name} 连接成功")
                connected_sources.append(source_name)
            else:
                logger.warning(f"数据源 {source_name} 连接失败")
        
        # 设置主数据源（优先使用连接成功的优先级最高的）
        available_sources = _global_manager.get_available_sources()
        if available_sources:
            # 按优先级顺序选择主数据源
            priority_order = ['eastmoney', 'tushare', 'akshare', 'sina', 'qqstock', 'wangyi']
            
            primary_source = None
            for source_name in priority_order:
                if source_name in connected_sources:
                    primary_source = source_name
                    break
            
            if primary_source:
                _global_manager.set_primary_source(primary_source)
                logger.info(f"主数据源设置为: {primary_source}")
            else:
                # 如果没有连接成功的，使用第一个可用的
                _global_manager.set_primary_source(available_sources[0])
                logger.warning(f"所有数据源连接失败，使用默认数据源: {available_sources[0]}")
        else:
            logger.error("没有可用的数据源！")
    
    return _global_manager


def reset_data_source_manager():
    """重置全局数据源管理器"""
    global _global_manager
    _global_manager = None