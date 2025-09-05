"""
风险评估模块
为散户提供简单易懂的风险评级和预警
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from ..database.manager import DatabaseManager


class RiskAssessment:
    """风险评估器"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
        # 风险评估参数
        self.risk_params = {
            'volatility_thresholds': {
                'low': 0.02,      # 2%以下为低风险
                'medium': 0.05,   # 5%以下为中风险
                'high': float('inf')  # 5%以上为高风险
            },
            'volume_spike_threshold': 2.0,  # 成交量放大2倍以上为异常
            'price_gap_threshold': 0.05,    # 价格跳空5%以上为异常
            'consecutive_decline_days': 5,   # 连续下跌5天为警示
            'support_resistance_threshold': 0.03  # 3%范围内为支撑/阻力位
        }
    
    def assess_stock_risk(self, symbol: str, days: int = 60) -> Dict:
        """
        评估单只股票的风险
        :param symbol: 股票代码
        :param days: 评估天数
        :return: 风险评估结果
        """
        result = {
            'symbol': symbol,
            'risk_level': 'unknown',
            'risk_score': 0,  # 0-100分，分数越高风险越大
            'risk_factors': [],
            'warnings': [],
            'recommendations': [],
            'assessment_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        try:
            # 获取股票价格数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = self.db_manager.get_daily_prices(symbol, start_date, end_date)
            
            if df.empty or len(df) < 10:
                result['risk_level'] = 'data_insufficient'
                result['warnings'].append('数据不足，无法进行风险评估')
                return result
            
            # 1. 价格波动性风险
            volatility_risk = self._assess_volatility_risk(df)
            result['risk_factors'].append(volatility_risk)
            
            # 2. 成交量异常风险
            volume_risk = self._assess_volume_risk(df)
            result['risk_factors'].append(volume_risk)
            
            # 3. 技术指标风险
            technical_risk = self._assess_technical_risk(symbol, df)
            result['risk_factors'].append(technical_risk)
            
            # 4. 趋势风险
            trend_risk = self._assess_trend_risk(df)
            result['risk_factors'].append(trend_risk)
            
            # 5. 流动性风险
            liquidity_risk = self._assess_liquidity_risk(df)
            result['risk_factors'].append(liquidity_risk)
            
            # 计算综合风险分数
            risk_scores = [factor['score'] for factor in result['risk_factors']]
            result['risk_score'] = np.mean(risk_scores)
            
            # 确定风险等级
            result['risk_level'] = self._determine_risk_level(result['risk_score'])
            
            # 生成预警和建议
            result['warnings'] = self._generate_warnings(result['risk_factors'])
            result['recommendations'] = self._generate_recommendations(result['risk_level'], result['risk_factors'])
            
            self.logger.info(f"股票{symbol}风险评估完成，风险等级：{result['risk_level']}")
            
        except Exception as e:
            self.logger.error(f"股票{symbol}风险评估失败: {e}")
            result['risk_level'] = 'error'
            result['warnings'].append(f'风险评估出错: {str(e)}')
        
        return result
    
    def _assess_volatility_risk(self, df: pd.DataFrame) -> Dict:
        """评估价格波动性风险"""
        try:
            # 计算日收益率
            returns = df['close'].pct_change().dropna()
            
            # 计算波动率（标准差）
            volatility = returns.std()
            
            # 计算最大回撤
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # 评分（0-100，分数越高风险越大）
            if volatility < self.risk_params['volatility_thresholds']['low']:
                score = 20
                level = '低'
            elif volatility < self.risk_params['volatility_thresholds']['medium']:
                score = 50
                level = '中'
            else:
                score = 80
                level = '高'
            
            # 最大回撤调整
            if abs(max_drawdown) > 0.2:  # 最大回撤超过20%
                score += 15
            elif abs(max_drawdown) > 0.1:  # 最大回撤超过10%
                score += 10
            
            return {
                'factor': '价格波动性',
                'score': min(score, 100),
                'level': level,
                'details': {
                    'volatility': round(volatility * 100, 2),
                    'max_drawdown': round(max_drawdown * 100, 2)
                },
                'description': f'价格波动率{volatility*100:.2f}%，最大回撤{abs(max_drawdown)*100:.2f}%'
            }
            
        except Exception as e:
            return {
                'factor': '价格波动性',
                'score': 50,
                'level': '未知',
                'details': {},
                'description': f'波动性评估失败: {str(e)}'
            }
    
    def _assess_volume_risk(self, df: pd.DataFrame) -> Dict:
        """评估成交量异常风险"""
        try:
            if 'volume' not in df.columns or df['volume'].isna().all():
                return {
                    'factor': '成交量',
                    'score': 30,
                    'level': '无数据',
                    'details': {},
                    'description': '缺少成交量数据'
                }
            
            # 计算成交量的移动平均
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
            
            # 检查成交量异常放大
            volume_ratio = df['volume'] / df['volume_ma']
            spike_days = len(volume_ratio[volume_ratio > self.risk_params['volume_spike_threshold']])
            
            # 计算成交量变异系数
            volume_cv = df['volume'].std() / df['volume'].mean()
            
            # 评分
            score = 20  # 基础分数
            
            if spike_days > len(df) * 0.1:  # 超过10%的交易日出现成交量异常
                score += 30
            elif spike_days > len(df) * 0.05:  # 超过5%的交易日出现成交量异常
                score += 20
            
            if volume_cv > 1.5:  # 成交量变异系数过大
                score += 20
            elif volume_cv > 1.0:
                score += 10
            
            level = '低' if score < 40 else '中' if score < 70 else '高'
            
            return {
                'factor': '成交量',
                'score': min(score, 100),
                'level': level,
                'details': {
                    'spike_days': spike_days,
                    'volume_cv': round(volume_cv, 2)
                },
                'description': f'成交量异常天数{spike_days}天，变异系数{volume_cv:.2f}'
            }
            
        except Exception as e:
            return {
                'factor': '成交量',
                'score': 50,
                'level': '未知',
                'details': {},
                'description': f'成交量评估失败: {str(e)}'
            }
    
    def _assess_technical_risk(self, symbol: str, df: pd.DataFrame) -> Dict:
        """评估技术指标风险"""
        try:
            # 获取技术指标数据
            end_date = df['date'].max() if 'date' in df.columns else datetime.now().strftime('%Y%m%d')
            start_date = df['date'].min() if 'date' in df.columns else (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
            
            tech_df = self.db_manager.get_technical_indicators(symbol, start_date, end_date)
            
            if tech_df.empty:
                return {
                    'factor': '技术指标',
                    'score': 40,
                    'level': '无数据',
                    'details': {},
                    'description': '缺少技术指标数据'
                }
            
            latest = tech_df.iloc[-1]
            score = 20  # 基础分数
            
            # RSI风险
            if 'rsi' in latest and pd.notna(latest['rsi']):
                rsi = latest['rsi']
                if rsi > 80:  # 严重超买
                    score += 25
                elif rsi > 70:  # 超买
                    score += 15
                elif rsi < 20:  # 严重超卖（也是风险）
                    score += 20
                elif rsi < 30:  # 超卖
                    score += 10
            
            # MACD风险
            if ('macd' in latest and 'macd_signal' in latest and 
                pd.notna(latest['macd']) and pd.notna(latest['macd_signal'])):
                
                macd_diff = latest['macd'] - latest['macd_signal']
                if abs(macd_diff) > 0.5:  # MACD差值过大
                    score += 15
            
            # 均线偏离风险
            if ('ma5' in latest and 'ma20' in latest and 
                pd.notna(latest['ma5']) and pd.notna(latest['ma20'])):
                
                ma_deviation = abs(latest['ma5'] - latest['ma20']) / latest['ma20']
                if ma_deviation > 0.1:  # 短期均线偏离长期均线超过10%
                    score += 20
                elif ma_deviation > 0.05:
                    score += 10
            
            level = '低' if score < 40 else '中' if score < 70 else '高'
            
            return {
                'factor': '技术指标',
                'score': min(score, 100),
                'level': level,
                'details': {
                    'rsi': round(latest.get('rsi', 0), 2) if pd.notna(latest.get('rsi', np.nan)) else None,
                    'macd_status': '多头' if latest.get('macd', 0) > latest.get('macd_signal', 0) else '空头'
                },
                'description': f'RSI: {latest.get("rsi", "N/A"):.1f}, MACD: {"多头" if latest.get("macd", 0) > latest.get("macd_signal", 0) else "空头"}'
            }
            
        except Exception as e:
            return {
                'factor': '技术指标',
                'score': 50,
                'level': '未知',
                'details': {},
                'description': f'技术指标评估失败: {str(e)}'
            }
    
    def _assess_trend_risk(self, df: pd.DataFrame) -> Dict:
        """评估趋势风险"""
        try:
            # 计算连续下跌天数
            df['price_change'] = df['close'].diff()
            consecutive_decline = 0
            max_consecutive_decline = 0
            
            for change in df['price_change']:
                if change < 0:
                    consecutive_decline += 1
                    max_consecutive_decline = max(max_consecutive_decline, consecutive_decline)
                else:
                    consecutive_decline = 0
            
            # 计算趋势斜率（线性回归）
            x = np.arange(len(df))
            y = df['close'].values
            slope = np.polyfit(x, y, 1)[0]
            
            # 计算价格相对位置（当前价格在近期高低点的位置）
            recent_high = df['high'].tail(20).max()
            recent_low = df['low'].tail(20).min()
            current_price = df['close'].iloc[-1]
            
            if recent_high != recent_low:
                price_position = (current_price - recent_low) / (recent_high - recent_low)
            else:
                price_position = 0.5
            
            # 评分
            score = 20
            
            # 连续下跌风险
            if max_consecutive_decline >= self.risk_params['consecutive_decline_days']:
                score += 30
            elif max_consecutive_decline >= 3:
                score += 15
            
            # 趋势斜率风险
            if slope < -0.1:  # 明显下降趋势
                score += 25
            elif slope < 0:  # 轻微下降趋势
                score += 10
            
            # 价格位置风险
            if price_position < 0.2:  # 价格接近近期低点
                score += 20
            elif price_position > 0.8:  # 价格接近近期高点
                score += 15
            
            level = '低' if score < 40 else '中' if score < 70 else '高'
            
            return {
                'factor': '趋势',
                'score': min(score, 100),
                'level': level,
                'details': {
                    'max_consecutive_decline': max_consecutive_decline,
                    'trend_slope': round(slope, 4),
                    'price_position': round(price_position * 100, 1)
                },
                'description': f'最大连续下跌{max_consecutive_decline}天，价格位置{price_position*100:.1f}%'
            }
            
        except Exception as e:
            return {
                'factor': '趋势',
                'score': 50,
                'level': '未知',
                'details': {},
                'description': f'趋势评估失败: {str(e)}'
            }
    
    def _assess_liquidity_risk(self, df: pd.DataFrame) -> Dict:
        """评估流动性风险"""
        try:
            if 'volume' not in df.columns or df['volume'].isna().all():
                return {
                    'factor': '流动性',
                    'score': 50,
                    'level': '无数据',
                    'details': {},
                    'description': '缺少成交量数据'
                }
            
            # 计算平均成交量
            avg_volume = df['volume'].mean()
            
            # 计算零成交量天数
            zero_volume_days = len(df[df['volume'] == 0])
            
            # 计算低成交量天数（低于平均成交量的50%）
            low_volume_threshold = avg_volume * 0.5
            low_volume_days = len(df[df['volume'] < low_volume_threshold])
            
            # 评分
            score = 10  # 基础分数（流动性风险通常较低）
            
            if zero_volume_days > 0:
                score += 40  # 有零成交量天数是严重问题
            
            low_volume_ratio = low_volume_days / len(df)
            if low_volume_ratio > 0.3:  # 超过30%的天数成交量偏低
                score += 30
            elif low_volume_ratio > 0.2:
                score += 20
            elif low_volume_ratio > 0.1:
                score += 10
            
            level = '低' if score < 30 else '中' if score < 60 else '高'
            
            return {
                'factor': '流动性',
                'score': min(score, 100),
                'level': level,
                'details': {
                    'avg_volume': int(avg_volume),
                    'zero_volume_days': zero_volume_days,
                    'low_volume_ratio': round(low_volume_ratio * 100, 1)
                },
                'description': f'平均成交量{int(avg_volume/10000):.1f}万，低量天数占比{low_volume_ratio*100:.1f}%'
            }
            
        except Exception as e:
            return {
                'factor': '流动性',
                'score': 30,
                'level': '未知',
                'details': {},
                'description': f'流动性评估失败: {str(e)}'
            }
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """根据风险分数确定风险等级"""
        if risk_score < 30:
            return '低风险'
        elif risk_score < 60:
            return '中风险'
        else:
            return '高风险'
    
    def _generate_warnings(self, risk_factors: List[Dict]) -> List[str]:
        """生成风险预警"""
        warnings = []
        
        for factor in risk_factors:
            if factor['score'] > 70:
                warnings.append(f"⚠️ {factor['factor']}风险较高: {factor['description']}")
            elif factor['score'] > 50:
                warnings.append(f"⚡ {factor['factor']}存在风险: {factor['description']}")
        
        return warnings
    
    def _generate_recommendations(self, risk_level: str, risk_factors: List[Dict]) -> List[str]:
        """生成风险管理建议"""
        recommendations = []
        
        if risk_level == '高风险':
            recommendations.extend([
                "🚨 建议减少仓位或考虑止损",
                "📊 密切关注市场动态和基本面变化",
                "⏱️ 避免追涨杀跌，等待更好的入场时机"
            ])
        elif risk_level == '中风险':
            recommendations.extend([
                "⚖️ 建议控制仓位，不宜重仓",
                "📈 可以考虑分批建仓或减仓",
                "🔍 加强对技术指标和基本面的监控"
            ])
        else:  # 低风险
            recommendations.extend([
                "✅ 风险相对较低，可适度参与",
                "📊 仍需关注市场变化，保持谨慎",
                "💼 可考虑作为投资组合的一部分"
            ])
        
        # 根据具体风险因素给出针对性建议
        for factor in risk_factors:
            if factor['factor'] == '价格波动性' and factor['score'] > 60:
                recommendations.append("📉 价格波动较大，建议设置止损点")
            elif factor['factor'] == '成交量' and factor['score'] > 60:
                recommendations.append("📊 成交量异常，注意市场情绪变化")
            elif factor['factor'] == '技术指标' and factor['score'] > 60:
                recommendations.append("📈 技术指标显示风险，建议等待确认信号")
            elif factor['factor'] == '趋势' and factor['score'] > 60:
                recommendations.append("📉 趋势不明朗，建议观望或轻仓操作")
        
        return recommendations
    
    def create_risk_alert(self, symbol: str, alert_type: str, message: str, severity: str = 'WARNING') -> bool:
        """创建风险预警"""
        try:
            title = f"风险预警 - {symbol}"
            success = self.db_manager.add_alert(
                symbol=symbol,
                alert_type=alert_type,
                title=title,
                message=message,
                severity=severity
            )
            
            if success:
                self.logger.info(f"创建风险预警成功: {symbol} - {alert_type}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"创建风险预警失败: {e}")
            return False
    
    def batch_risk_assessment(self, symbols: List[str]) -> Dict:
        """批量风险评估"""
        results = {}
        
        for symbol in symbols:
            try:
                result = self.assess_stock_risk(symbol)
                results[symbol] = result
                
                # 如果风险较高，创建预警
                if result['risk_level'] == '高风险':
                    self.create_risk_alert(
                        symbol=symbol,
                        alert_type='high_risk',
                        message=f"股票{symbol}风险评级为高风险，风险分数{result['risk_score']:.1f}",
                        severity='CRITICAL'
                    )
                
            except Exception as e:
                self.logger.error(f"股票{symbol}风险评估失败: {e}")
                results[symbol] = {
                    'symbol': symbol,
                    'risk_level': 'error',
                    'error': str(e)
                }
        
        return results