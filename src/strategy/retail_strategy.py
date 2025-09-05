"""
散户策略工具
为散户提供简单易懂的买卖点提示和投资建议
集成海龟交易法则，提供更专业的趋势跟踪策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from ..database.manager import DatabaseManager
from .turtle_strategy import TurtleTradingStrategy


class RetailStrategy:
    """散户策略分析器"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # 初始化海龟策略
        self.turtle_strategy = TurtleTradingStrategy(db_manager)
        
        # 策略参数
        self.params = {
            'stop_loss_ratio': 0.08,      # 8%止损
            'take_profit_ratio': 0.15,    # 15%止盈
            'oversold_threshold': 30,     # RSI超卖
            'overbought_threshold': 70,   # RSI超买
            'volume_spike_ratio': 2.0,    # 成交量放大倍数
            'enable_turtle': True,        # 启用海龟策略
            'turtle_weight': 0.6,         # 海龟策略权重
        }
    
    def generate_trading_signals(self, symbol: str, days: int = 60) -> Dict:
        """生成交易信号（集成海龟策略）"""
        result = {
            'symbol': symbol,
            'action': 'HOLD',
            'confidence': 0.5,
            'reasons': [],
            'entry_price': None,
            'stop_loss': None,
            'take_profit': None,
            'position_size': 0.1,
            'strategy_details': {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # 获取数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            price_data = self.db_manager.get_daily_prices(symbol, start_date, end_date)
            tech_data = self.db_manager.get_technical_indicators(symbol, start_date, end_date)
            
            if price_data.empty:
                result['reasons'].append('数据不足，无法生成信号')
                return result
            
            # 1. 传统技术分析信号
            traditional_signals = self._analyze_traditional_signals(price_data, tech_data)
            
            # 2. 海龟策略信号（如果启用）
            turtle_signals = None
            if self.params.get('enable_turtle', True):
                turtle_signals = self.turtle_strategy.get_turtle_recommendation(symbol)
                result['strategy_details']['turtle'] = turtle_signals
            
            # 3. 综合决策
            final_decision = self._make_combined_decision(traditional_signals, turtle_signals)
            result.update(final_decision)
            
            # 4. 计算风险管理参数
            risk_mgmt = self._calculate_enhanced_risk_management(price_data, result['action'], turtle_signals)
            result.update(risk_mgmt)
            
        except Exception as e:
            self.logger.error(f"策略信号生成失败: {e}")
            result['reasons'].append(f'信号生成错误: {str(e)}')
        
        return result
    
    def _analyze_traditional_signals(self, price_data: pd.DataFrame, tech_data: pd.DataFrame) -> Dict:
        """分析传统技术信号"""
        signals = {'trend': 0, 'technical': 0, 'volume': 0}
        
        if tech_data.empty:
            return signals
            
        latest_tech = tech_data.iloc[-1]
        latest_price = price_data.iloc[-1]
        
        # 趋势信号
        ma5 = latest_tech.get('ma5', 0)
        ma20 = latest_tech.get('ma20', 0)
        if ma5 > ma20:
            signals['trend'] += 0.3
        else:
            signals['trend'] -= 0.3
        
        # 技术指标信号
        rsi = latest_tech.get('rsi', 50)
        if rsi < self.params['oversold_threshold']:
            signals['technical'] += 0.4
        elif rsi > self.params['overbought_threshold']:
            signals['technical'] -= 0.4
        
        # MACD信号
        macd = latest_tech.get('macd', 0)
        macd_signal = latest_tech.get('macd_signal', 0)
        if macd > macd_signal:
            signals['technical'] += 0.2
        else:
            signals['technical'] -= 0.2
        
        # 成交量信号
        if len(price_data) >= 20 and 'volume' in price_data.columns:
            avg_volume = price_data['volume'].tail(20).mean()
            current_volume = latest_price['volume']
            if current_volume > avg_volume * self.params['volume_spike_ratio']:
                price_change = latest_price['close'] - price_data.iloc[-2]['close']
                if price_change > 0:
                    signals['volume'] += 0.2
                else:
                    signals['volume'] -= 0.1
        
        return signals
    
    def _make_combined_decision(self, traditional_signals: Dict, turtle_signals: Optional[Dict]) -> Dict:
        """综合传统信号和海龟策略做出决策"""
        # 传统信号分数
        traditional_score = sum(traditional_signals.values()) if traditional_signals else 0
        traditional_weight = 1 - self.params.get('turtle_weight', 0.6)
        
        # 海龟策略分数
        turtle_score = 0
        turtle_confidence = 0
        turtle_reasons = []
        
        if turtle_signals and turtle_signals.get('recommendation') != 'NO_ACTION':
            turtle_recommendation = turtle_signals['recommendation']
            turtle_confidence = turtle_signals.get('confidence', 0)
            
            if turtle_recommendation == 'BUY':
                turtle_score = turtle_confidence
                turtle_reasons.append(f"海龟策略: {turtle_signals.get('reason', '买入信号')}")
            elif turtle_recommendation == 'SELL':
                turtle_score = -turtle_confidence
                turtle_reasons.append(f"海龜策略: {turtle_signals.get('reason', '卖出信号')}")
            elif turtle_recommendation == 'EXIT':
                turtle_score = -0.8  # 出场信号强度较高
                turtle_reasons.append("海龜策略: 触发出场信号")
        
        # 综合计分
        total_score = (traditional_score * traditional_weight + 
                      turtle_score * self.params.get('turtle_weight', 0.6))
        
        # 生成原因说明
        reasons = []
        
        # 传统信号原因
        if traditional_signals:
            if traditional_signals['trend'] > 0:
                reasons.append('短期均线上穿长期均线')
            elif traditional_signals['trend'] < 0:
                reasons.append('短期均线下穿长期均线')
            
            if traditional_signals['technical'] > 0.2:
                reasons.append('技术指标显示超卖或多头信号')
            elif traditional_signals['technical'] < -0.2:
                reasons.append('技术指标显示超买或空头信号')
            
            if traditional_signals['volume'] > 0:
                reasons.append('放量上涨')
            elif traditional_signals['volume'] < 0:
                reasons.append('放量下跌')
        
        # 海龜策略原因
        reasons.extend(turtle_reasons)
        
        # 决策逻辑
        if total_score > 0.3:
            action = 'BUY'
            confidence = min(0.9, 0.5 + abs(total_score))
        elif total_score < -0.3:
            action = 'SELL'
            confidence = min(0.9, 0.5 + abs(total_score))
        else:
            action = 'HOLD'
            confidence = 0.5
            if not reasons:
                reasons.append('信号不明确，建议观望')
        
        return {
            'action': action,
            'confidence': confidence,
            'reasons': reasons,
            'traditional_score': traditional_score,
            'turtle_score': turtle_score,
            'total_score': total_score
        }
    
    def _make_decision(self, signals: Dict, price_data: pd.DataFrame, tech_data: pd.DataFrame) -> Dict:
        """做出最终决策"""
        total_score = sum(signals.values())
        reasons = []
        
        # 生成原因说明
        if signals['trend'] > 0:
            reasons.append('短期均线上穿长期均线')
        elif signals['trend'] < 0:
            reasons.append('短期均线下穿长期均线')
        
        if signals['technical'] > 0.2:
            reasons.append('技术指标显示超卖或多头信号')
        elif signals['technical'] < -0.2:
            reasons.append('技术指标显示超买或空头信号')
        
        if signals['volume'] > 0:
            reasons.append('放量上涨')
        elif signals['volume'] < 0:
            reasons.append('放量下跌')
        
        # 决策逻辑
        if total_score > 0.3:
            action = 'BUY'
            confidence = min(0.9, 0.5 + total_score)
        elif total_score < -0.3:
            action = 'SELL'
            confidence = min(0.9, 0.5 + abs(total_score))
        else:
            action = 'HOLD'
            confidence = 0.5
            reasons.append('信号不明确，建议观望')
        
        return {
            'action': action,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def _calculate_enhanced_risk_management(self, price_data: pd.DataFrame, action: str, turtle_signals: Optional[Dict]) -> Dict:
        """计算增强的风险管理参数（结合海龜法则）"""
        current_price = price_data['close'].iloc[-1]
        
        result = {
            'entry_price': current_price,
            'stop_loss': None,
            'take_profit': None,
            'position_size': 0.1
        }
        
        if action in ['BUY', 'SELL']:
            # 优先使用海龜策略的风险管理
            if turtle_signals and turtle_signals.get('stop_loss'):
                result['stop_loss'] = turtle_signals['stop_loss']
                result['position_size'] = turtle_signals.get('position_size', 0.1)
                
                # 海龜策略的止盈目标（使用2倍ATR）
                if action == 'BUY' and turtle_signals.get('risk_metrics', {}).get('atr_pct'):
                    atr_pct = turtle_signals['risk_metrics']['atr_pct'] / 100
                    result['take_profit'] = current_price * (1 + atr_pct * 2)
                elif action == 'SELL' and turtle_signals.get('risk_metrics', {}).get('atr_pct'):
                    atr_pct = turtle_signals['risk_metrics']['atr_pct'] / 100
                    result['take_profit'] = current_price * (1 - atr_pct * 2)
            else:
                # 使用传统风险管理
                if action == 'BUY':
                    result['stop_loss'] = current_price * (1 - self.params['stop_loss_ratio'])
                    result['take_profit'] = current_price * (1 + self.params['take_profit_ratio'])
                elif action == 'SELL':
                    result['stop_loss'] = current_price * (1 + self.params['stop_loss_ratio'])
                    result['take_profit'] = current_price * (1 - self.params['take_profit_ratio'])
                
                # 根据波动率调整仓位
                volatility = price_data['close'].pct_change().std()
                if volatility > 0.05:
                    result['position_size'] = 0.05  # 高波动小仓位
                elif volatility > 0.03:
                    result['position_size'] = 0.1   # 中波动
                else:
                    result['position_size'] = 0.15  # 低波动大仓位
        
        return result
    
    def get_position_advice(self, symbol: str, cost_price: float, shares: int) -> Dict:
        """获取持仓建议"""
        try:
            # 获取当前价格
            price_data = self.db_manager.get_daily_prices(symbol, limit=1)
            if price_data.empty:
                return {'error': '无法获取当前价格'}
            
            current_price = price_data.iloc[-1]['close']
            pnl_pct = (current_price - cost_price) / cost_price * 100
            
            advice = {
                'symbol': symbol,
                'current_price': current_price,
                'cost_price': cost_price,
                'pnl_pct': pnl_pct,
                'action': 'HOLD',
                'reasons': []
            }
            
            # 止损建议
            if pnl_pct < -self.params['stop_loss_ratio'] * 100:
                advice['action'] = 'SELL'
                advice['reasons'].append(f'已达止损线({-self.params["stop_loss_ratio"]*100:.1f}%)')
            
            # 止盈建议
            elif pnl_pct > self.params['take_profit_ratio'] * 100:
                advice['action'] = 'SELL'
                advice['reasons'].append(f'已达止盈线({self.params["take_profit_ratio"]*100:.1f}%)')
            
            # 获取最新交易信号
            signals = self.generate_trading_signals(symbol)
            if signals['action'] == 'SELL' and signals['confidence'] > 0.7:
                advice['action'] = 'SELL'
                advice['reasons'].extend(signals['reasons'])
            
            return advice
            
        except Exception as e:
            self.logger.error(f"持仓建议生成失败: {e}")
            return {'error': f'分析失败: {str(e)}'}
    
    def save_strategy_result(self, symbol: str, strategy_result: Dict) -> bool:
        """保存策略结果到数据库"""
        try:
            return self.db_manager.session.execute(
                "INSERT INTO strategies (symbol, strategy_type, action, confidence, reason, price, stop_loss, take_profit) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    symbol,
                    'retail_strategy',
                    strategy_result.get('action'),
                    strategy_result.get('confidence'),
                    '; '.join(strategy_result.get('reasons', [])),
                    strategy_result.get('entry_price'),
                    strategy_result.get('stop_loss'),
                    strategy_result.get('take_profit')
                )
            )
        except Exception as e:
            self.logger.error(f"保存策略结果失败: {e}")
            return False