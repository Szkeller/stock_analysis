"""
图表生成模块
生成技术分析图表
"""

import matplotlib
# 设置为非GUI后端，避免macOS线程问题
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import matplotlib.dates as mdates
from datetime import datetime
import os
import logging

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


class ChartGenerator:
    """图表生成器"""
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # 确保输出目录存在
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            self.logger.error(f"创建图表目录失败: {e}")
            self.output_dir = "."
        
        # 设置图表默认参数
        plt.style.use('default')
        
        # 设置中文字体（如果支持）
        try:
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        except:
            self.logger.warning("中文字体设置失败，使用默认字体")
    
    def create_price_chart(self, df: pd.DataFrame, symbol: str, save_path: str = None) -> Optional[str]:
        """
        创建价格走势图
        :param df: 股票数据
        :param symbol: 股票代码
        :param save_path: 保存路径
        :return: 图表文件路径
        """
        try:
            if df.empty:
                self.logger.warning(f"股票{symbol}数据为空，无法生成图表")
                return None
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # 转换日期
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                dates = df['date']
            else:
                dates = df.index
            
            # 主图：价格和移动平均线
            ax1.plot(dates, df['close'], label='收盘价', linewidth=1.5, color='black')
            
            # 添加移动平均线
            if 'ma5' in df.columns and not df['ma5'].isna().all():
                ax1.plot(dates, df['ma5'], label='MA5', linewidth=1, alpha=0.8)
            if 'ma10' in df.columns and not df['ma10'].isna().all():
                ax1.plot(dates, df['ma10'], label='MA10', linewidth=1, alpha=0.8)
            if 'ma20' in df.columns and not df['ma20'].isna().all():
                ax1.plot(dates, df['ma20'], label='MA20', linewidth=1, alpha=0.8)
            if 'ma60' in df.columns and not df['ma60'].isna().all():
                ax1.plot(dates, df['ma60'], label='MA60', linewidth=1, alpha=0.8)
            
            # 添加布林带
            if all(col in df.columns for col in ['boll_upper', 'boll_middle', 'boll_lower']):
                if not df['boll_upper'].isna().all():
                    ax1.plot(dates, df['boll_upper'], '--', alpha=0.5, color='red', label='布林上轨')
                    ax1.plot(dates, df['boll_middle'], '--', alpha=0.5, color='blue', label='布林中轨')
                    ax1.plot(dates, df['boll_lower'], '--', alpha=0.5, color='green', label='布林下轨')
                    ax1.fill_between(dates, df['boll_upper'], df['boll_lower'], alpha=0.1, color='blue')
            
            ax1.set_title(f'{symbol} 股价走势图')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 副图：成交量
            if 'volume' in df.columns and not df['volume'].isna().all():
                colors = ['red' if close >= open_price else 'green' 
                         for close, open_price in zip(df['close'], df['open']) 
                         if pd.notna(close) and pd.notna(open_price)]
                
                # 如果颜色数量不匹配，使用默认颜色
                if len(colors) != len(df):
                    colors = ['blue'] * len(df)
                    
                ax2.bar(dates, df['volume'], color=colors, alpha=0.6, width=0.8)
                
                # 添加成交量均线
                if 'vol_ma5' in df.columns and not df['vol_ma5'].isna().all():
                    ax2.plot(dates, df['vol_ma5'], label='成交量MA5', linewidth=1)
                if 'vol_ma10' in df.columns and not df['vol_ma10'].isna().all():
                    ax2.plot(dates, df['vol_ma10'], label='成交量MA10', linewidth=1)
                
                ax2.set_ylabel('成交量')
                if any(col in df.columns and not df[col].isna().all() 
                      for col in ['vol_ma5', 'vol_ma10']):
                    ax2.legend()
            else:
                ax2.set_ylabel('成交量')
                ax2.text(0.5, 0.5, '无成交量数据', 
                        transform=ax2.transAxes, ha='center', va='center', 
                        fontsize=12, alpha=0.5)
            
            ax2.grid(True, alpha=0.3)
            
            # 设置x轴日期格式
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator())
            ax2.xaxis.set_major_locator(mdates.MonthLocator())
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 保存图表
            if save_path is None:
                save_path = os.path.join(self.output_dir, f'{symbol}_price_chart.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"价格图表生成成功: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成{symbol}价格图表失败: {e}")
            plt.close('all')  # 清理图表
            return None
    
    def create_macd_chart(self, df: pd.DataFrame, symbol: str, save_path: str = None) -> Optional[str]:
        """创建MACD图表"""
        try:
            # 输入参数验证
            if df is None or df.empty:
                self.logger.warning(f"股票{symbol}数据为空，无法生成MACD图表")
                return None
            
            if not symbol or not isinstance(symbol, str):
                raise ValueError("股票代码不能为空且必须是字符串")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                dates = df['date']
            else:
                dates = df.index
            
            # 检查是否有MACD相关数据
            has_macd_data = any(col in df.columns and not df[col].isna().all() 
                               for col in ['macd', 'macd_signal', 'macd_histogram'])
            
            if not has_macd_data:
                ax.text(0.5, 0.5, '无MACD指标数据', 
                       transform=ax.transAxes, ha='center', va='center', 
                       fontsize=14, alpha=0.5)
            else:
                # MACD线和信号线
                if 'macd' in df.columns and not df['macd'].isna().all():
                    ax.plot(dates, df['macd'], label='MACD', linewidth=1.5)
                if 'macd_signal' in df.columns and not df['macd_signal'].isna().all():
                    ax.plot(dates, df['macd_signal'], label='信号线', linewidth=1.5)
                
                # MACD柱状图
                if 'macd_histogram' in df.columns and not df['macd_histogram'].isna().all():
                    colors = ['red' if pd.notna(x) and x >= 0 else 'green' for x in df['macd_histogram']]
                    ax.bar(dates, df['macd_histogram'], color=colors, alpha=0.6, width=0.8, label='MACD柱')
            
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax.set_title(f'{symbol} MACD指标')
            ax.set_ylabel('MACD值')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if save_path is None:
                save_path = os.path.join(self.output_dir, f'{symbol}_macd_chart.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"MACD图表生成成功: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成{symbol}的MACD图表失败: {e}")
            plt.close('all')  # 确保清理所有图表资源
            return None
    
    def create_rsi_chart(self, df: pd.DataFrame, symbol: str, save_path: str = None) -> Optional[str]:
        """创建RSI图表"""
        try:
            # 输入参数验证
            if df is None or df.empty:
                self.logger.warning(f"股票{symbol}数据为空，无法生成RSI图表")
                return None
                
            if not symbol or not isinstance(symbol, str):
                raise ValueError("股票代码不能为空且必须是字符串")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                dates = df['date']
            else:
                dates = df.index
            
            # 检查RSI数据
            if 'rsi' not in df.columns or df['rsi'].isna().all():
                ax.text(0.5, 0.5, '无RSI指标数据', 
                       transform=ax.transAxes, ha='center', va='center', 
                       fontsize=14, alpha=0.5)
            else:
                ax.plot(dates, df['rsi'], label='RSI', linewidth=1.5, color='purple')
            
            # 添加超买超卖线
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='超买线(70)')
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='超卖线(30)')
            ax.axhline(y=50, color='black', linestyle='-', alpha=0.3, label='中线(50)')
            
            # 填充区域
            ax.fill_between(dates, 70, 100, alpha=0.1, color='red', label='超买区域')
            ax.fill_between(dates, 0, 30, alpha=0.1, color='green', label='超卖区域')
            
            ax.set_title(f'{symbol} RSI指标')
            ax.set_ylabel('RSI值')
            ax.set_ylim(0, 100)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if save_path is None:
                save_path = os.path.join(self.output_dir, f'{symbol}_rsi_chart.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"RSI图表生成成功: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成{symbol}的RSI图表失败: {e}")
            plt.close('all')  # 确保清理所有图表资源
            return None
    
    def create_kdj_chart(self, df: pd.DataFrame, symbol: str, save_path: str = None) -> Optional[str]:
        """创建KDJ图表"""
        try:
            # 输入参数验证
            if df is None or df.empty:
                self.logger.warning(f"股票{symbol}数据为空，无法生成KDJ图表")
                return None
                
            if not symbol or not isinstance(symbol, str):
                raise ValueError("股票代码不能为空且必须是字符串")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                dates = df['date']
            else:
                dates = df.index
            
            # 检查KDJ数据
            has_kdj_data = any(col in df.columns and not df[col].isna().all() 
                              for col in ['kdj_k', 'kdj_d', 'kdj_j'])
            
            if not has_kdj_data:
                ax.text(0.5, 0.5, '无KDJ指标数据', 
                       transform=ax.transAxes, ha='center', va='center', 
                       fontsize=14, alpha=0.5)
            else:
                if 'kdj_k' in df.columns and not df['kdj_k'].isna().all():
                    ax.plot(dates, df['kdj_k'], label='K线', linewidth=1.5)
                if 'kdj_d' in df.columns and not df['kdj_d'].isna().all():
                    ax.plot(dates, df['kdj_d'], label='D线', linewidth=1.5)
                if 'kdj_j' in df.columns and not df['kdj_j'].isna().all():
                    ax.plot(dates, df['kdj_j'], label='J线', linewidth=1.5)
            
            # 添加参考线
            ax.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='超买线(80)')
            ax.axhline(y=20, color='green', linestyle='--', alpha=0.7, label='超卖线(20)')
            ax.axhline(y=50, color='black', linestyle='-', alpha=0.3, label='中线(50)')
            
            ax.set_title(f'{symbol} KDJ指标')
            ax.set_ylabel('KDJ值')
            ax.set_ylim(0, 100)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if save_path is None:
                save_path = os.path.join(self.output_dir, f'{symbol}_kdj_chart.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"KDJ图表生成成功: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成{symbol}的KDJ图表失败: {e}")
            plt.close('all')  # 确保清理所有图表资源
            return None
    
    def create_comprehensive_chart(self, df: pd.DataFrame, symbol: str, save_path: str = None) -> Optional[str]:
        """创建综合技术分析图表"""
        try:
            # 输入参数验证
            if df is None or df.empty:
                self.logger.warning(f"股票{symbol}数据为空，无法生成综合图表")
                return None
                
            if not symbol or not isinstance(symbol, str):
                raise ValueError("股票代码不能为空且必须是字符串")
            
            fig, axes = plt.subplots(4, 1, figsize=(15, 12), 
                                    gridspec_kw={'height_ratios': [3, 1, 1, 1]})
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                dates = df['date']
            else:
                dates = df.index
            
            # 1. 价格和移动平均线
            ax1 = axes[0]
            if 'close' in df.columns and not df['close'].isna().all():
                ax1.plot(dates, df['close'], label='收盘价', linewidth=1.5, color='black')
                
                if 'ma5' in df.columns and not df['ma5'].isna().all():
                    ax1.plot(dates, df['ma5'], label='MA5', linewidth=1)
                if 'ma20' in df.columns and not df['ma20'].isna().all():
                    ax1.plot(dates, df['ma20'], label='MA20', linewidth=1)
                if 'ma60' in df.columns and not df['ma60'].isna().all():
                    ax1.plot(dates, df['ma60'], label='MA60', linewidth=1)
                
                # 布林带
                if all(col in df.columns and not df[col].isna().all() 
                      for col in ['boll_upper', 'boll_lower']):
                    ax1.fill_between(dates, df['boll_upper'], df['boll_lower'], 
                                   alpha=0.1, color='blue', label='布林带')
            else:
                ax1.text(0.5, 0.5, '无价格数据', 
                        transform=ax1.transAxes, ha='center', va='center', 
                        fontsize=14, alpha=0.5)
            
            ax1.set_title(f'{symbol} 技术分析综合图')
            ax1.set_ylabel('价格 (元)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 2. MACD
            ax2 = axes[1]
            has_macd = any(col in df.columns and not df[col].isna().all() 
                          for col in ['macd', 'macd_signal', 'macd_histogram'])
            
            if has_macd:
                if 'macd' in df.columns and not df['macd'].isna().all():
                    ax2.plot(dates, df['macd'], label='MACD', linewidth=1)
                if 'macd_signal' in df.columns and not df['macd_signal'].isna().all():
                    ax2.plot(dates, df['macd_signal'], label='信号线', linewidth=1)
                if 'macd_histogram' in df.columns and not df['macd_histogram'].isna().all():
                    colors = ['red' if pd.notna(x) and x >= 0 else 'green' for x in df['macd_histogram']]
                    ax2.bar(dates, df['macd_histogram'], color=colors, alpha=0.6, width=0.8)
            else:
                ax2.text(0.5, 0.5, '无MACD数据', 
                        transform=ax2.transAxes, ha='center', va='center', 
                        fontsize=12, alpha=0.5)
            
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax2.set_ylabel('MACD')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 3. RSI
            ax3 = axes[2]
            if 'rsi' in df.columns and not df['rsi'].isna().all():
                ax3.plot(dates, df['rsi'], label='RSI', linewidth=1, color='purple')
                ax3.axhline(y=70, color='red', linestyle='--', alpha=0.7)
                ax3.axhline(y=30, color='green', linestyle='--', alpha=0.7)
                ax3.fill_between(dates, 70, 100, alpha=0.1, color='red')
                ax3.fill_between(dates, 0, 30, alpha=0.1, color='green')
            else:
                ax3.text(0.5, 0.5, '无RSI数据', 
                        transform=ax3.transAxes, ha='center', va='center', 
                        fontsize=12, alpha=0.5)
            
            ax3.set_ylabel('RSI')
            ax3.set_ylim(0, 100)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 4. KDJ
            ax4 = axes[3]
            has_kdj = any(col in df.columns and not df[col].isna().all() 
                         for col in ['kdj_k', 'kdj_d', 'kdj_j'])
            
            if has_kdj:
                if 'kdj_k' in df.columns and not df['kdj_k'].isna().all():
                    ax4.plot(dates, df['kdj_k'], label='K', linewidth=1)
                if 'kdj_d' in df.columns and not df['kdj_d'].isna().all():
                    ax4.plot(dates, df['kdj_d'], label='D', linewidth=1)
                if 'kdj_j' in df.columns and not df['kdj_j'].isna().all():
                    ax4.plot(dates, df['kdj_j'], label='J', linewidth=1)
                    
                ax4.axhline(y=80, color='red', linestyle='--', alpha=0.7)
                ax4.axhline(y=20, color='green', linestyle='--', alpha=0.7)
            else:
                ax4.text(0.5, 0.5, '无KDJ数据', 
                        transform=ax4.transAxes, ha='center', va='center', 
                        fontsize=12, alpha=0.5)
            
            ax4.set_ylabel('KDJ')
            ax4.set_ylim(0, 100)
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
            # 设置x轴
            for ax in axes:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.MonthLocator())
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            if save_path is None:
                save_path = os.path.join(self.output_dir, f'{symbol}_comprehensive_chart.png')
            
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"综合图表生成成功: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成{symbol}的综合图表失败: {e}")
            plt.close('all')  # 确保清理所有图表资源
            return None
    
    def create_simple_chart(self, df: pd.DataFrame, symbol: str, chart_type: str = "price") -> Optional[str]:
        """创建简单图表（用于Web显示）"""
        try:
            # 输入参数验证
            if df is None or df.empty:
                self.logger.warning(f"股票{symbol}数据为空，无法生成简单图表")
                return None
                
            if not symbol or not isinstance(symbol, str):
                raise ValueError("股票代码不能为空且必须是字符串")
                
            if chart_type not in ["price", "volume"]:
                raise ValueError("图表类型必须是'price'或'volume'")
            
            plt.figure(figsize=(10, 6))
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                dates = df['date']
            else:
                dates = df.index
            
            if chart_type == "price":
                if 'close' not in df.columns or df['close'].isna().all():
                    plt.text(0.5, 0.5, '无价格数据', 
                            transform=plt.gca().transAxes, ha='center', va='center', 
                            fontsize=14, alpha=0.5)
                else:
                    plt.plot(dates, df['close'], label='收盘价', linewidth=2)
                    if 'ma5' in df.columns and not df['ma5'].isna().all():
                        plt.plot(dates, df['ma5'], label='MA5', alpha=0.8)
                    if 'ma20' in df.columns and not df['ma20'].isna().all():
                        plt.plot(dates, df['ma20'], label='MA20', alpha=0.8)
                        
                plt.title(f'{symbol} 价格走势')
                plt.ylabel('价格 (元)')
            
            elif chart_type == "volume":
                if 'volume' not in df.columns or df['volume'].isna().all():
                    plt.text(0.5, 0.5, '无成交量数据', 
                            transform=plt.gca().transAxes, ha='center', va='center', 
                            fontsize=14, alpha=0.5)
                else:
                    plt.bar(dates, df['volume'], alpha=0.7)
                    
                plt.title(f'{symbol} 成交量')
                plt.ylabel('成交量')
            
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            save_path = os.path.join(self.output_dir, f'{symbol}_{chart_type}_simple.png')
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"简单{chart_type}图表生成成功: {save_path}")
            return save_path
            
        except Exception as e:
            self.logger.error(f"生成{symbol}的简单{chart_type}图表失败: {e}")
            plt.close('all')  # 确保清理所有图表资源
            return None