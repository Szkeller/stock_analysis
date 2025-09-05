"""
技术指标计算模块
实现常用的技术分析指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging


class TechnicalIndicators:
    """技术指标计算类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_ma(self, prices: pd.Series, periods: List[int] = [5, 10, 20, 60]) -> Dict[str, pd.Series]:
        """
        计算移动平均线
        :param prices: 价格序列（通常是收盘价）
        :param periods: 计算周期列表
        :return: 各周期移动平均线字典
        """
        ma_dict = {}
        for period in periods:
            if len(prices) >= period:
                ma_dict[f'ma{period}'] = prices.rolling(window=period).mean()
            else:
                ma_dict[f'ma{period}'] = pd.Series([np.nan] * len(prices), index=prices.index)
        
        return ma_dict
    
    def calculate_ema(self, prices: pd.Series, periods: List[int] = [12, 26]) -> Dict[str, pd.Series]:
        """
        计算指数移动平均线
        :param prices: 价格序列
        :param periods: 计算周期列表
        :return: 各周期EMA字典
        """
        ema_dict = {}
        for period in periods:
            if len(prices) >= period:
                ema_dict[f'ema{period}'] = prices.ewm(span=period).mean()
            else:
                ema_dict[f'ema{period}'] = pd.Series([np.nan] * len(prices), index=prices.index)
        
        return ema_dict
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        计算MACD指标
        :param prices: 价格序列
        :param fast: 快线周期
        :param slow: 慢线周期
        :param signal: 信号线周期
        :return: MACD指标字典
        """
        if len(prices) < slow:
            return {
                'macd': pd.Series([np.nan] * len(prices), index=prices.index),
                'macd_signal': pd.Series([np.nan] * len(prices), index=prices.index),
                'macd_histogram': pd.Series([np.nan] * len(prices), index=prices.index)
            }
        
        # 计算快慢线EMA
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        # 计算MACD线
        macd_line = ema_fast - ema_slow
        
        # 计算信号线（MACD的EMA）
        signal_line = macd_line.ewm(span=signal).mean()
        
        # 计算MACD柱状图
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算RSI相对强弱指数
        :param prices: 价格序列
        :param period: 计算周期
        :return: RSI序列
        """
        if len(prices) < period + 1:
            return pd.Series([np.nan] * len(prices), index=prices.index)
        
        # 计算价格变化
        delta = prices.diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均收益和平均损失
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series, 
                     k_period: int = 9, d_period: int = 3, j_period: int = 3) -> Dict[str, pd.Series]:
        """
        计算KDJ随机指标
        :param high: 最高价序列
        :param low: 最低价序列
        :param close: 收盘价序列
        :param k_period: K值计算周期
        :param d_period: D值计算周期
        :param j_period: J值计算周期
        :return: KDJ指标字典
        """
        if len(close) < k_period:
            nan_series = pd.Series([np.nan] * len(close), index=close.index)
            return {'kdj_k': nan_series, 'kdj_d': nan_series, 'kdj_j': nan_series}
        
        # 计算RSV（未成熟随机值）
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        
        # 计算K值（K值是RSV的移动平均）
        k_values = []
        k_prev = 50  # K值初始值
        
        for rsv_val in rsv:
            if pd.isna(rsv_val):
                k_values.append(np.nan)
            else:
                k_current = (2/3) * k_prev + (1/3) * rsv_val
                k_values.append(k_current)
                k_prev = k_current
        
        k_series = pd.Series(k_values, index=close.index)
        
        # 计算D值（K值的移动平均）
        d_values = []
        d_prev = 50  # D值初始值
        
        for k_val in k_series:
            if pd.isna(k_val):
                d_values.append(np.nan)
            else:
                d_current = (2/3) * d_prev + (1/3) * k_val
                d_values.append(d_current)
                d_prev = d_current
        
        d_series = pd.Series(d_values, index=close.index)
        
        # 计算J值
        j_series = 3 * k_series - 2 * d_series
        
        return {
            'kdj_k': k_series,
            'kdj_d': d_series,
            'kdj_j': j_series
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        计算布林带
        :param prices: 价格序列
        :param period: 计算周期
        :param std_dev: 标准差倍数
        :return: 布林带字典
        """
        if len(prices) < period:
            nan_series = pd.Series([np.nan] * len(prices), index=prices.index)
            return {
                'boll_upper': nan_series,
                'boll_middle': nan_series,
                'boll_lower': nan_series
            }
        
        # 计算中轨（移动平均线）
        middle_band = prices.rolling(window=period).mean()
        
        # 计算标准差
        std = prices.rolling(window=period).std()
        
        # 计算上轨和下轨
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return {
            'boll_upper': upper_band,
            'boll_middle': middle_band,
            'boll_lower': lower_band
        }
    
    def calculate_volume_ma(self, volume: pd.Series, periods: List[int] = [5, 10, 20]) -> Dict[str, pd.Series]:
        """
        计算成交量移动平均线
        :param volume: 成交量序列
        :param periods: 计算周期列表
        :return: 成交量均线字典
        """
        vol_ma_dict = {}
        for period in periods:
            if len(volume) >= period:
                vol_ma_dict[f'vol_ma{period}'] = volume.rolling(window=period).mean()
            else:
                vol_ma_dict[f'vol_ma{period}'] = pd.Series([np.nan] * len(volume), index=volume.index)
        
        return vol_ma_dict
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        计算平均真实范围（ATR）
        :param high: 最高价序列
        :param low: 最低价序列
        :param close: 收盘价序列
        :param period: 计算周期
        :return: ATR序列
        """
        if len(close) < 2:
            return pd.Series([np.nan] * len(close), index=close.index)
        
        # 计算真实范围TR
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 计算ATR（TR的移动平均）
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def calculate_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        计算能量潮指标（OBV）
        :param close: 收盘价序列
        :param volume: 成交量序列
        :return: OBV序列
        """
        if len(close) < 2:
            return pd.Series([np.nan] * len(close), index=close.index)
        
        # 计算价格变化方向
        price_change = close.diff()
        
        # 根据价格变化确定成交量的正负
        obv_values = []
        obv_current = 0
        
        for i, (price_diff, vol) in enumerate(zip(price_change, volume)):
            if i == 0 or pd.isna(price_diff) or pd.isna(vol):
                obv_values.append(np.nan)
            else:
                if price_diff > 0:
                    obv_current += vol
                elif price_diff < 0:
                    obv_current -= vol
                # 价格不变时，OBV不变
                obv_values.append(obv_current)
        
        return pd.Series(obv_values, index=close.index)
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标
        :param df: 包含OHLCV数据的DataFrame
        :return: 包含所有技术指标的DataFrame
        """
        result_df = df.copy()
        
        try:
            # 移动平均线
            ma_indicators = self.calculate_ma(df['close'])
            for key, value in ma_indicators.items():
                result_df[key] = value
            
            # MACD
            macd_indicators = self.calculate_macd(df['close'])
            for key, value in macd_indicators.items():
                result_df[key] = value
            
            # RSI
            result_df['rsi'] = self.calculate_rsi(df['close'])
            
            # KDJ
            kdj_indicators = self.calculate_kdj(df['high'], df['low'], df['close'])
            for key, value in kdj_indicators.items():
                result_df[key] = value
            
            # 布林带
            boll_indicators = self.calculate_bollinger_bands(df['close'])
            for key, value in boll_indicators.items():
                result_df[key] = value
            
            # 成交量指标
            if 'volume' in df.columns:
                vol_ma_indicators = self.calculate_volume_ma(df['volume'])
                for key, value in vol_ma_indicators.items():
                    result_df[key] = value
                
                # OBV
                result_df['obv'] = self.calculate_obv(df['close'], df['volume'])
            
            # ATR
            result_df['atr'] = self.calculate_atr(df['high'], df['low'], df['close'])
            
            self.logger.info("技术指标计算完成")
            
        except Exception as e:
            self.logger.error(f"技术指标计算失败: {e}")
        
        return result_df
    
    def get_latest_signals(self, df: pd.DataFrame) -> Dict:
        """
        获取最新的技术指标信号
        :param df: 包含技术指标的DataFrame
        :return: 信号字典
        """
        if df.empty or len(df) < 2:
            return {}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        signals = {}
        
        try:
            # MA信号
            if not pd.isna(latest.get('ma5')) and not pd.isna(latest.get('ma20')):
                if latest['ma5'] > latest['ma20'] and prev['ma5'] <= prev['ma20']:
                    signals['ma_golden_cross'] = True
                elif latest['ma5'] < latest['ma20'] and prev['ma5'] >= prev['ma20']:
                    signals['ma_death_cross'] = True
            
            # MACD信号
            if not pd.isna(latest.get('macd')) and not pd.isna(latest.get('macd_signal')):
                if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                    signals['macd_golden_cross'] = True
                elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                    signals['macd_death_cross'] = True
            
            # RSI信号
            if not pd.isna(latest.get('rsi')):
                if latest['rsi'] > 70:
                    signals['rsi_overbought'] = True
                elif latest['rsi'] < 30:
                    signals['rsi_oversold'] = True
            
            # KDJ信号
            if not pd.isna(latest.get('kdj_k')) and not pd.isna(latest.get('kdj_d')):
                if latest['kdj_k'] > latest['kdj_d'] and prev['kdj_k'] <= prev['kdj_d']:
                    signals['kdj_golden_cross'] = True
                elif latest['kdj_k'] < latest['kdj_d'] and prev['kdj_k'] >= prev['kdj_d']:
                    signals['kdj_death_cross'] = True
            
            # 布林带信号
            if (not pd.isna(latest.get('close')) and 
                not pd.isna(latest.get('boll_upper')) and 
                not pd.isna(latest.get('boll_lower'))):
                
                if latest['close'] > latest['boll_upper']:
                    signals['boll_breakthrough_upper'] = True
                elif latest['close'] < latest['boll_lower']:
                    signals['boll_breakthrough_lower'] = True
        
        except Exception as e:
            self.logger.error(f"获取技术信号失败: {e}")
        
        return signals