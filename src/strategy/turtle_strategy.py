"""
海龟交易法则策略
经典的趋势跟踪策略，适合散户使用的简化版本
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from ..database.manager import DatabaseManager


class TurtleTradingStrategy:
    """海龟交易法则策略"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # 海龟交易法则参数
        self.params = {
            # 系统1参数（短期）
            'system1_entry_period': 20,    # 20天突破入场
            'system1_exit_period': 10,     # 10天突破出场
            
            # 系统2参数（长期）
            'system2_entry_period': 55,    # 55天突破入场
            'system2_exit_period': 20,     # 20天突破出场
            
            # 风险管理参数
            'atr_period': 20,              # ATR计算周期
            'stop_loss_atr_multiple': 2.0, # 止损为2倍ATR
            'position_risk_pct': 0.02,     # 每笔交易风险2%
            'max_positions': 4,            # 最大同时持仓数
            'max_sector_positions': 2,     # 同行业最大持仓数
            
            # 资金管理
            'total_capital': 100000,       # 总资金
            'unit_limit_single': 0.05,     # 单个市场最大仓位5%
            'unit_limit_sector': 0.12,     # 同行业最大仓位12%
            'unit_limit_direction': 0.20,  # 同方向最大仓位20%
        }
    
    def analyze_turtle_signals(self, symbol: str, days: int = 120) -> Dict:
        """分析海龟交易信号"""
        result = {
            'symbol': symbol,
            'system1': {},
            'system2': {},
            'combined_signal': 'HOLD',
            'position_size': 0,
            'stop_loss': None,
            'take_profit': None,
            'risk_metrics': {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 获取数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            price_data = self.db_manager.get_daily_prices(symbol, start_date, end_date)
            
            if price_data.empty or len(price_data) < max(self.params['system2_entry_period'], 
                                                        self.params['atr_period']) + 5:
                result['error'] = '数据不足，需要至少60天历史数据'
                return result
            
            # 计算ATR
            atr_data = self._calculate_atr(price_data)
            current_atr = atr_data.iloc[-1] if not atr_data.empty else 0
            
            # 分析两套系统
            result['system1'] = self._analyze_system(symbol, 1, price_data, atr_data)
            result['system2'] = self._analyze_system(symbol, 2, price_data, atr_data)
            
            # 综合信号判断
            result['combined_signal'] = self._combine_signals(result['system1'], result['system2'])
            
            # 计算仓位大小
            if result['combined_signal'] in ['BUY', 'SELL']:
                result['position_size'] = self._calculate_position_size(price_data, current_atr)
                result['stop_loss'] = self._calculate_stop_loss(price_data, current_atr, result['combined_signal'])
            
            # 风险指标
            result['risk_metrics'] = self._calculate_risk_metrics(price_data, atr_data)
            
            self.logger.info(f"海龟策略分析完成: {symbol}")
            
        except Exception as e:
            self.logger.error(f"海龟策略分析失败: {e}")
            result['error'] = str(e)
        
        return result
    
    def _analyze_system(self, symbol: str, system_num: int, price_data: pd.DataFrame, atr_data: pd.Series) -> Dict:
        """分析单个系统的信号"""
        if system_num == 1:
            entry_period = self.params['system1_entry_period']
            exit_period = self.params['system1_exit_period']
        else:
            entry_period = self.params['system2_entry_period']
            exit_period = self.params['system2_exit_period']
        
        system_result = {
            'entry_signal': 'NONE',
            'exit_signal': 'NONE',
            'entry_price': None,
            'exit_price': None,
            'breakout_high': None,
            'breakout_low': None,
            'confidence': 0.0
        }
        
        if len(price_data) < entry_period + 1:
            return system_result
        
        # 计算突破点
        current_price = price_data['close'].iloc[-1]
        current_high = price_data['high'].iloc[-1]
        current_low = price_data['low'].iloc[-1]
        
        # 入场突破点（不包括当天）
        entry_high = price_data['high'].iloc[-(entry_period+1):-1].max()
        entry_low = price_data['low'].iloc[-(entry_period+1):-1].min()
        
        # 出场突破点
        if len(price_data) >= exit_period + 1:
            exit_high = price_data['high'].iloc[-(exit_period+1):-1].max()
            exit_low = price_data['low'].iloc[-(exit_period+1):-1].min()
        else:
            exit_high = entry_high
            exit_low = entry_low
        
        system_result.update({
            'breakout_high': entry_high,
            'breakout_low': entry_low,
            'exit_high': exit_high,
            'exit_low': exit_low
        })
        
        # 入场信号判断
        if current_high > entry_high:
            system_result['entry_signal'] = 'BUY'
            system_result['entry_price'] = entry_high
            system_result['confidence'] = self._calculate_breakout_strength(price_data, entry_high, True)
        elif current_low < entry_low:
            system_result['entry_signal'] = 'SELL'
            system_result['entry_price'] = entry_low
            system_result['confidence'] = self._calculate_breakout_strength(price_data, entry_low, False)
        
        # 出场信号判断
        if current_low < exit_low:
            system_result['exit_signal'] = 'EXIT_LONG'
            system_result['exit_price'] = exit_low
        elif current_high > exit_high:
            system_result['exit_signal'] = 'EXIT_SHORT'
            system_result['exit_price'] = exit_high
        
        return system_result
    
    def _calculate_breakout_strength(self, price_data: pd.DataFrame, breakout_level: float, is_upward: bool) -> float:
        """计算突破强度（置信度）"""
        try:
            current_price = price_data['close'].iloc[-1]
            current_volume = price_data['volume'].iloc[-1] if 'volume' in price_data.columns else 0
            
            # 计算突破幅度
            if is_upward:
                breakout_pct = (current_price - breakout_level) / breakout_level
            else:
                breakout_pct = (breakout_level - current_price) / breakout_level
            
            # 计算成交量倍数
            avg_volume = price_data['volume'].tail(20).mean() if 'volume' in price_data.columns else 1
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # 综合置信度计算
            base_confidence = min(breakout_pct * 10, 0.5)  # 突破幅度贡献
            volume_boost = min((volume_ratio - 1) * 0.1, 0.3)  # 成交量贡献
            
            confidence = min(base_confidence + volume_boost + 0.3, 0.9)
            return max(confidence, 0.1)
            
        except Exception:
            return 0.5
    
    def _combine_signals(self, system1: Dict, system2: Dict) -> str:
        """合并两套系统的信号"""
        # 优先级：系统2 > 系统1（长期系统更可靠）
        if system2['entry_signal'] != 'NONE':
            return system2['entry_signal']
        elif system1['entry_signal'] != 'NONE' and system1['confidence'] > 0.6:
            return system1['entry_signal']
        elif system2['exit_signal'] != 'NONE':
            return 'EXIT'
        elif system1['exit_signal'] != 'NONE':
            return 'EXIT'
        else:
            return 'HOLD'
    
    def _calculate_atr(self, price_data: pd.DataFrame) -> pd.Series:
        """计算ATR（真实波动幅度）"""
        try:
            high = price_data['high']
            low = price_data['low']
            close = price_data['close']
            
            # 计算真实范围
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # 计算ATR（指数移动平均）
            atr = tr.ewm(span=self.params['atr_period']).mean()
            
            return atr
            
        except Exception as e:
            self.logger.error(f"ATR计算失败: {e}")
            return pd.Series()
    
    def _calculate_position_size(self, price_data: pd.DataFrame, atr: float) -> float:
        """根据海龟法则计算仓位大小"""
        try:
            current_price = price_data['close'].iloc[-1]
            
            if atr <= 0 or current_price <= 0:
                return 0.05  # 默认5%仓位
            
            # 海龟单位计算
            # Unit = (账户规模 × 风险比例) / (ATR × 合约乘数)
            risk_amount = self.params['total_capital'] * self.params['position_risk_pct']
            dollar_volatility = atr  # 股票的美元波动
            
            position_value = risk_amount / dollar_volatility
            position_size = position_value / self.params['total_capital']
            
            # 限制仓位大小
            max_position = self.params['unit_limit_single']
            return min(position_size, max_position)
            
        except Exception as e:
            self.logger.error(f"仓位计算失败: {e}")
            return 0.05
    
    def _calculate_stop_loss(self, price_data: pd.DataFrame, atr: float, signal: str) -> float:
        """计算止损价格"""
        try:
            current_price = price_data['close'].iloc[-1]
            stop_distance = atr * self.params['stop_loss_atr_multiple']
            
            if signal == 'BUY':
                return current_price - stop_distance
            elif signal == 'SELL':
                return current_price + stop_distance
            else:
                return None
                
        except Exception:
            return None
    
    def _calculate_risk_metrics(self, price_data: pd.DataFrame, atr_data: pd.Series) -> Dict:
        """计算风险指标"""
        try:
            current_price = price_data['close'].iloc[-1]
            current_atr = atr_data.iloc[-1] if not atr_data.empty else 0
            
            # 价格波动率
            returns = price_data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # 年化波动率
            
            # ATR相对值
            atr_pct = (current_atr / current_price) * 100 if current_price > 0 else 0
            
            # 最大回撤
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # 趋势强度
            ma20 = price_data['close'].rolling(20).mean().iloc[-1]
            ma60 = price_data['close'].rolling(60).mean().iloc[-1]
            trend_strength = ((current_price - ma20) / ma20) * 100 if ma20 > 0 else 0
            
            return {
                'volatility': round(volatility * 100, 2),
                'atr_pct': round(atr_pct, 2),
                'max_drawdown': round(max_drawdown * 100, 2),
                'trend_strength': round(trend_strength, 2),
                'ma20_vs_ma60': 'bullish' if ma20 > ma60 else 'bearish'
            }
            
        except Exception as e:
            self.logger.error(f"风险指标计算失败: {e}")
            return {}
    
    def get_turtle_recommendation(self, symbol: str) -> Dict:
        """获取海龟策略建议"""
        turtle_analysis = self.analyze_turtle_signals(symbol)
        
        if 'error' in turtle_analysis:
            return {
                'symbol': symbol,
                'strategy': 'turtle',
                'recommendation': 'NO_ACTION',
                'reason': turtle_analysis['error'],
                'confidence': 0.0
            }
        
        signal = turtle_analysis['combined_signal']
        system1 = turtle_analysis['system1']
        system2 = turtle_analysis['system2']
        
        # 生成建议
        recommendation = {
            'symbol': symbol,
            'strategy': 'turtle',
            'recommendation': signal,
            'confidence': 0.0,
            'reason': '',
            'position_size': turtle_analysis.get('position_size', 0),
            'stop_loss': turtle_analysis.get('stop_loss'),
            'system_details': {
                'system1': system1,
                'system2': system2
            },
            'risk_metrics': turtle_analysis.get('risk_metrics', {})
        }
        
        # 生成详细说明
        if signal == 'BUY':
            active_system = 2 if system2['entry_signal'] == 'BUY' else 1
            recommendation['confidence'] = system2['confidence'] if active_system == 2 else system1['confidence']
            recommendation['reason'] = f"价格突破{self.params[f'system{active_system}_entry_period']}天高点，海龟系统{active_system}发出买入信号"
            
        elif signal == 'SELL':
            active_system = 2 if system2['entry_signal'] == 'SELL' else 1
            recommendation['confidence'] = system2['confidence'] if active_system == 2 else system1['confidence']
            recommendation['reason'] = f"价格跌破{self.params[f'system{active_system}_entry_period']}天低点，海龟系统{active_system}发出卖出信号"
            
        elif signal == 'EXIT':
            recommendation['confidence'] = 0.8
            recommendation['reason'] = "价格触发出场信号，建议平仓"
            
        else:
            recommendation['confidence'] = 0.3
            recommendation['reason'] = "价格在震荡区间内，未触发海龟交易信号"
        
        return recommendation