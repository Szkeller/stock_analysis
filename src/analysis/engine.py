"""
分析引擎
整合数据获取、技术指标计算和图表生成
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from .technical_indicators import TechnicalIndicators
from .chart_generator import ChartGenerator
from ..data_source.factory import get_data_source_manager
from ..database.manager import DatabaseManager


class AnalysisEngine:
    """分析引擎"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.technical_indicators = TechnicalIndicators()
        self.chart_generator = ChartGenerator()
        self.db_manager = db_manager or DatabaseManager()
        self.data_source_manager = get_data_source_manager()
        self.logger = logging.getLogger(__name__)
    
    def analyze_stock(self, symbol: str, period: str = "daily", 
                     days: int = 250, force_update: bool = False) -> Dict:
        """
        分析单只股票
        :param symbol: 股票代码
        :param period: 数据周期
        :param days: 分析天数
        :param force_update: 是否强制更新数据
        :return: 分析结果
        """
        result = {
            'symbol': symbol,
            'status': 'success',
            'data': None,
            'indicators': None,
            'signals': None,
            'charts': None,
            'summary': None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 1. 获取股票数据
            df = self._get_stock_data(symbol, period, days, force_update)
            
            if df.empty:
                result['status'] = 'error'
                result['message'] = '无法获取股票数据'
                return result
            
            # 2. 计算技术指标
            df_with_indicators = self.technical_indicators.calculate_all_indicators(df)
            
            # 3. 获取技术信号
            signals = self.technical_indicators.get_latest_signals(df_with_indicators)
            
            # 4. 生成图表
            charts = self._generate_charts(df_with_indicators, symbol)
            
            # 5. 生成分析摘要
            summary = self._generate_summary(df_with_indicators, signals)
            
            # 6. 保存结果到数据库 (非关键操作，失败不影响结果)
            try:
                self._save_analysis_results(symbol, df_with_indicators)
                self.logger.info(f"股票{symbol}的分析结果已保存到数据库")
            except Exception as save_error:
                self.logger.warning(f"保存{symbol}分析结果失败（不影响主要功能）: {save_error}")
            
            result.update({
                'data': df_with_indicators.tail(30).to_dict('records'),  # 返回最近30天数据
                'indicators': self._extract_latest_indicators(df_with_indicators),
                'signals': signals,
                'charts': charts,
                'summary': summary
            })
            
            self.logger.info(f"股票{symbol}分析完成")
            
        except Exception as e:
            self.logger.error(f"股票{symbol}分析失败: {e}")
            result.update({
                'status': 'error',
                'message': str(e)
            })
        
        return result
    
    def batch_analyze_stocks(self, symbols: List[str], 
                           period: str = "daily", days: int = 100) -> Dict:
        """
        批量分析股票
        :param symbols: 股票代码列表
        :param period: 数据周期
        :param days: 分析天数
        :return: 批量分析结果
        """
        results = {}
        
        for symbol in symbols:
            try:
                result = self.analyze_stock(symbol, period, days)
                results[symbol] = result
                self.logger.info(f"股票{symbol}分析完成")
            except Exception as e:
                self.logger.error(f"股票{symbol}分析失败: {e}")
                results[symbol] = {
                    'symbol': symbol,
                    'status': 'error',
                    'message': str(e)
                }
        
        return results
    
    def analyze_watchlist(self) -> Dict:
        """分析自选股"""
        try:
            # 获取自选股列表
            watchlist = self.db_manager.get_watchlist()
            
            if not watchlist:
                return {
                    'status': 'success',
                    'message': '自选股列表为空',
                    'results': {}
                }
            
            symbols = [item['symbol'] for item in watchlist]
            results = self.batch_analyze_stocks(symbols)
            
            # 添加自选股的额外信息
            for item in watchlist:
                symbol = item['symbol']
                if symbol in results:
                    results[symbol]['watchlist_info'] = {
                        'priority': item['priority'],
                        'notes': item['notes'],
                        'added_date': item['added_date'].strftime('%Y-%m-%d') if item['added_date'] else None
                    }
            
            return {
                'status': 'success',
                'count': len(results),
                'results': results,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"自选股分析失败: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_stock_data(self, symbol: str, period: str, days: int, force_update: bool) -> pd.DataFrame:
        """获取股票数据，支持多数据源备用"""
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
        
        # 先从数据库获取数据
        if not force_update:
            df = self.db_manager.get_daily_prices(symbol, start_date.replace('-', ''), end_date.replace('-', ''))
            if not df.empty and len(df) >= days * 0.8:  # 如果数据覆盖率超过80%，使用数据库数据
                return df
        
        # 从数据源获取数据，尝试多个数据源
        df = pd.DataFrame()
        available_sources = self.data_source_manager.get_available_sources()
        
        for source_name in available_sources:
            try:
                # 获取指定数据源
                source = self.data_source_manager.get_source_by_name(source_name)
                if source and source.is_connected:
                    df = source.get_price_data(symbol, start_date, end_date, period)
                    
                    if not df.empty:
                        self.logger.info(f"使用{source_name}数据源成功获取{symbol}数据")
                        break
                    else:
                        self.logger.warning(f"{source_name}数据源无法获取{symbol}数据")
                        
            except Exception as e:
                self.logger.error(f"使用{source_name}数据源获取{symbol}数据失败: {e}")
                continue
        
        # 如果仍然无数据，尝试缩短时间范围
        if df.empty and days > 30:
            self.logger.warning(f"无法获取{symbol}长期数据，尝试获取短期数据")
            shorter_start = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            for source_name in available_sources:
                try:
                    source = self.data_source_manager.get_source_by_name(source_name)
                    if source and source.is_connected:
                        df = source.get_price_data(symbol, shorter_start, end_date, period)
                        if not df.empty:
                            self.logger.info(f"使用{source_name}数据源获取到{symbol}短期数据")
                            break
                except Exception as e:
                    continue
        
        # 保存到数据库 (非关键操作)
        if not df.empty:
            try:
                self.db_manager.save_daily_prices(df)
                self.logger.debug(f"成功保存{symbol}数据到数据库")
            except Exception as e:
                self.logger.warning(f"保存{symbol}数据到数据库失败（不影响功能）: {e}")
        
        return df
    
    def _generate_charts(self, df: pd.DataFrame, symbol: str) -> Dict:
        """生成图表"""
        charts = {}
        
        try:
            # 综合图表
            charts['comprehensive'] = self.chart_generator.create_comprehensive_chart(df, symbol)
            
            # 单独图表
            charts['price'] = self.chart_generator.create_price_chart(df, symbol)
            charts['macd'] = self.chart_generator.create_macd_chart(df, symbol)
            charts['rsi'] = self.chart_generator.create_rsi_chart(df, symbol)
            charts['kdj'] = self.chart_generator.create_kdj_chart(df, symbol)
            
        except Exception as e:
            self.logger.error(f"生成图表失败: {e}")
        
        return charts
    
    def _extract_latest_indicators(self, df: pd.DataFrame) -> Dict:
        """提取最新的技术指标值"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        
        indicators = {}
        
        # 移动平均线
        for ma in ['ma5', 'ma10', 'ma20', 'ma60']:
            if ma in latest and pd.notna(latest[ma]):
                indicators[ma] = round(float(latest[ma]), 2)
        
        # MACD
        for macd_col in ['macd', 'macd_signal', 'macd_histogram']:
            if macd_col in latest and pd.notna(latest[macd_col]):
                indicators[macd_col] = round(float(latest[macd_col]), 4)
        
        # RSI
        if 'rsi' in latest and pd.notna(latest['rsi']):
            indicators['rsi'] = round(float(latest['rsi']), 2)
        
        # KDJ
        for kdj_col in ['kdj_k', 'kdj_d', 'kdj_j']:
            if kdj_col in latest and pd.notna(latest[kdj_col]):
                indicators[kdj_col] = round(float(latest[kdj_col]), 2)
        
        # 布林带
        for boll_col in ['boll_upper', 'boll_middle', 'boll_lower']:
            if boll_col in latest and pd.notna(latest[boll_col]):
                indicators[boll_col] = round(float(latest[boll_col]), 2)
        
        return indicators
    
    def _generate_summary(self, df: pd.DataFrame, signals: Dict) -> Dict:
        """生成分析摘要"""
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        summary = {
            'basic_info': {
                'latest_price': round(float(latest['close']), 2),
                'price_change': round(float(latest['close'] - prev['close']), 2),
                'price_change_pct': round(float((latest['close'] - prev['close']) / prev['close'] * 100), 2),
                'volume': int(latest['volume']) if pd.notna(latest['volume']) else 0
            },
            'technical_status': self._analyze_technical_status(df),
            'signals_count': len(signals),
            'active_signals': list(signals.keys()),
            'risk_level': self._calculate_risk_level(df),
            'recommendation': self._generate_recommendation(df, signals)
        }
        
        return summary
    
    def _analyze_technical_status(self, df: pd.DataFrame) -> Dict:
        """分析技术状态"""
        latest = df.iloc[-1]
        status = {}
        
        # 趋势分析
        if 'ma5' in latest and 'ma20' in latest and pd.notna(latest['ma5']) and pd.notna(latest['ma20']):
            if latest['ma5'] > latest['ma20']:
                status['trend'] = '上升趋势'
            else:
                status['trend'] = '下降趋势'
        
        # RSI状态
        if 'rsi' in latest and pd.notna(latest['rsi']):
            rsi_val = latest['rsi']
            if rsi_val > 70:
                status['rsi_status'] = '超买'
            elif rsi_val < 30:
                status['rsi_status'] = '超卖'
            else:
                status['rsi_status'] = '正常'
        
        # MACD状态
        if 'macd' in latest and 'macd_signal' in latest and pd.notna(latest['macd']) and pd.notna(latest['macd_signal']):
            if latest['macd'] > latest['macd_signal']:
                status['macd_status'] = '多头'
            else:
                status['macd_status'] = '空头'
        
        return status
    
    def _calculate_risk_level(self, df: pd.DataFrame) -> str:
        """计算风险等级"""
        if len(df) < 20:
            return '数据不足'
        
        # 基于价格波动率计算风险
        price_volatility = df['close'].pct_change().std() * 100
        
        if price_volatility > 5:
            return '高风险'
        elif price_volatility > 3:
            return '中风险'
        else:
            return '低风险'
    
    def _generate_recommendation(self, df: pd.DataFrame, signals: Dict) -> str:
        """生成投资建议"""
        if df.empty:
            return '数据不足，无法给出建议'
        
        positive_signals = 0
        negative_signals = 0
        
        # 分析信号
        for signal in signals.keys():
            if any(keyword in signal for keyword in ['golden_cross', 'oversold', 'breakthrough_lower']):
                positive_signals += 1
            elif any(keyword in signal for keyword in ['death_cross', 'overbought', 'breakthrough_upper']):
                negative_signals += 1
        
        # 生成建议
        if positive_signals > negative_signals:
            return '建议关注，可能存在买入机会'
        elif negative_signals > positive_signals:
            return '建议谨慎，可能存在风险'
        else:
            return '建议观望，保持关注'
    
    def _save_analysis_results(self, symbol: str, df: pd.DataFrame):
        """保存分析结果到数据库"""
        try:
            # 保存技术指标数据
            indicator_columns = [
                'date', 'ma5', 'ma10', 'ma20', 'ma60',
                'macd', 'macd_signal', 'macd_histogram',
                'rsi', 'kdj_k', 'kdj_d', 'kdj_j',
                'boll_upper', 'boll_middle', 'boll_lower'
            ]
            
            # 只选择DataFrame中实际存在的指标列
            available_columns = [col for col in indicator_columns if col in df.columns]
            
            if len(available_columns) > 0:  # 至少要有一个指标列
                indicators_df = df[available_columns].copy()
                indicators_df['symbol'] = symbol
                
                self.db_manager.save_technical_indicators(indicators_df)
                
        except Exception as e:
            self.logger.error(f"保存分析结果失败: {e}")
    
    def get_stock_ranking(self, criteria: str = "综合", limit: int = 20) -> List[Dict]:
        """
        获取股票排行榜
        :param criteria: 排序标准（涨幅、成交量、技术分数等）
        :param limit: 返回数量
        :return: 排行榜列表
        """
        try:
            # 从数据源获取所有股票数据
            data_source = self.data_source_manager.get_source()
            stock_list = data_source.get_stock_list()
            
            if stock_list.empty:
                return []
            
            # 根据条件排序
            if criteria == "涨幅":
                sorted_stocks = stock_list.sort_values('pct_change', ascending=False)
            elif criteria == "成交量":
                sorted_stocks = stock_list.sort_values('volume', ascending=False)
            elif criteria == "换手率":
                sorted_stocks = stock_list.sort_values('turnover_rate', ascending=False)
            else:
                # 默认按涨幅排序
                sorted_stocks = stock_list.sort_values('pct_change', ascending=False)
            
            # 返回前N只股票
            result = []
            for _, row in sorted_stocks.head(limit).iterrows():
                result.append({
                    'symbol': row['symbol'],
                    'name': row['name'],
                    'price': round(row['price'], 2) if pd.notna(row['price']) else 0,
                    'pct_change': round(row['pct_change'], 2) if pd.notna(row['pct_change']) else 0,
                    'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                    'turnover_rate': round(row['turnover_rate'], 2) if pd.notna(row['turnover_rate']) else 0
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取股票排行榜失败: {e}")
            return []