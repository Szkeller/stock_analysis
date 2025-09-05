"""
Flask Web应用
为散户提供简洁的股票分析Web界面
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
from datetime import datetime
import logging

from ..analysis.engine import AnalysisEngine
from ..risk.assessment import RiskAssessment
from ..database.manager import DatabaseManager
from ..data_source.factory import get_data_source_manager
from ..strategy.retail_strategy import RetailStrategy


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'stock_analysis_secret_key_2024'
    
    # 启用CORS
    CORS(app)
    
    # 初始化组件
    db_manager = DatabaseManager()
    analysis_engine = AnalysisEngine(db_manager)
    risk_assessment = RiskAssessment(db_manager)
    retail_strategy = RetailStrategy(db_manager)
    data_source_manager = get_data_source_manager()
    
    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')
    
    @app.route('/api/search_stock')
    def search_stock():
        """搜索股票"""
        try:
            query = request.args.get('q', '').strip()
            if not query:
                return jsonify({'success': False, 'message': '请输入搜索关键词'})
            
            # 从数据库获取股票列表
            stocks = db_manager.get_all_stocks()
            
            # 如果数据库为空，从数据源获取
            if not stocks:
                try:
                    data_source = data_source_manager.get_source()
                    stock_list = data_source.get_stock_list()
                    
                    if not stock_list.empty:
                        # 保存到数据库
                        for _, row in stock_list.head(100).iterrows():  # 先保存前100只
                            stock_data = {
                                'symbol': row.get('symbol', ''),
                                'name': row.get('name', ''),
                                'market': 'SH' if row.get('symbol', '').startswith('6') else 'SZ',
                                'is_active': True
                            }
                            db_manager.save_stock(stock_data)
                        
                        stocks = db_manager.get_all_stocks()
                except Exception as e:
                    app.logger.error(f"获取股票列表失败: {e}")
            
            # 搜索匹配的股票
            matched_stocks = []
            for stock in stocks:
                if (query in stock['symbol'] or 
                    query in stock['name'] or 
                    stock['symbol'].startswith(query)):
                    matched_stocks.append(stock)
            
            # 限制返回数量
            matched_stocks = matched_stocks[:20]
            
            return jsonify({
                'success': True,
                'data': matched_stocks
            })
            
        except Exception as e:
            app.logger.error(f"搜索股票失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/analyze/<symbol>')
    def analyze_stock(symbol):
        """分析股票"""
        try:
            days = request.args.get('days', 120, type=int)
            force_update = request.args.get('force', False, type=bool)
            
            app.logger.info(f"开始分析股票: {symbol}, 天数: {days}")
            
            # 执行分析
            result = analysis_engine.analyze_stock(symbol, days=days, force_update=force_update)
            
            if result['status'] == 'success':
                # 简化返回数据，避免数据量过大
                simplified_result = {
                    'symbol': result.get('symbol'),
                    'status': result.get('status'),
                    'summary': result.get('summary'),
                    'charts': result.get('charts', {}),
                    'timestamp': result.get('timestamp')
                }
                
                # 处理signals - 如果是字典，转换为列表格式
                signals = result.get('signals', {})
                if isinstance(signals, dict):
                    # 将字典转换为列表格式，取前5个
                    signal_list = [{'type': k, 'active': v} for k, v in list(signals.items())[:5]]
                    simplified_result['signals'] = signal_list
                elif isinstance(signals, list):
                    simplified_result['signals'] = signals[:5]  # 如果是列表，直接取前5个
                else:
                    simplified_result['signals'] = []
                
                # 添加最新指标数据
                if result.get('indicators'):
                    simplified_result['indicators'] = result['indicators']
                
                # 添加最近5天数据，并处理NaN值
                if result.get('data') and len(result['data']) > 0:
                    import pandas as pd
                    import numpy as np
                    
                    recent_data = result['data'][-5:]  # 最近5天
                    # 处理NaN值，转换为null
                    for item in recent_data:
                        for key, value in item.items():
                            if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
                                item[key] = None
                    
                    simplified_result['recent_data'] = recent_data
                    simplified_result['data_count'] = len(result['data'])
                
                app.logger.info(f"股票{symbol}分析成功，返回简化结果")
                
                return jsonify({
                    'success': True,
                    'data': simplified_result
                })
            else:
                app.logger.warning(f"股票{symbol}分析失败: {result.get('message', '未知错误')}")
                return jsonify({
                    'success': False,
                    'message': result.get('message', '分析失败')
                })
                
        except Exception as e:
            app.logger.error(f"分析股票{symbol}异常: {e}", exc_info=True)
            return jsonify({
                'success': False, 
                'message': f'分析异常: {str(e)}'
            })
    
    @app.route('/api/turtle_strategy/<symbol>')
    def get_turtle_strategy(symbol):
        """获取海龜策略分析"""
        try:
            result = retail_strategy.turtle_strategy.analyze_turtle_signals(symbol)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except Exception as e:
            app.logger.error(f"海龜策略分析{symbol}失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/trading_signals/<symbol>')
    def get_trading_signals(symbol):
        """获取综合交易信号（包含海龜策略）"""
        try:
            days = request.args.get('days', 120, type=int)
            
            result = retail_strategy.generate_trading_signals(symbol, days=days)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except Exception as e:
            app.logger.error(f"交易信号分析{symbol}失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/risk_assessment/<symbol>')
    def assess_risk(symbol):
        """风险评估"""
        try:
            days = request.args.get('days', 60, type=int)
            
            result = risk_assessment.assess_stock_risk(symbol, days=days)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
        except Exception as e:
            app.logger.error(f"风险评估{symbol}失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/watchlist')
    def get_watchlist():
        """获取自选股列表"""
        try:
            watchlist = db_manager.get_watchlist()
            return jsonify({
                'success': True,
                'data': watchlist
            })
        except Exception as e:
            app.logger.error(f"获取自选股失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/watchlist', methods=['POST'])
    def add_to_watchlist():
        """添加到自选股"""
        try:
            data = request.get_json()
            symbol = data.get('symbol')
            name = data.get('name', '')
            notes = data.get('notes', '')
            priority = data.get('priority', 1)
            
            if not symbol:
                return jsonify({'success': False, 'message': '股票代码不能为空'})
            
            success = db_manager.add_to_watchlist(symbol, name, notes, priority)
            
            if success:
                return jsonify({'success': True, 'message': '添加到自选股成功'})
            else:
                return jsonify({'success': False, 'message': '添加失败'})
                
        except Exception as e:
            app.logger.error(f"添加自选股失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/watchlist/<symbol>', methods=['DELETE'])
    def remove_from_watchlist(symbol):
        """从自选股移除"""
        try:
            success = db_manager.remove_from_watchlist(symbol)
            
            if success:
                return jsonify({'success': True, 'message': '移除成功'})
            else:
                return jsonify({'success': False, 'message': '移除失败'})
                
        except Exception as e:
            app.logger.error(f"移除自选股失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/ranking')
    def get_ranking():
        """获取股票排行榜"""
        try:
            criteria = request.args.get('criteria', '涨幅')
            limit = request.args.get('limit', 20, type=int)
            
            ranking = analysis_engine.get_stock_ranking(criteria, limit)
            
            return jsonify({
                'success': True,
                'data': ranking
            })
            
        except Exception as e:
            app.logger.error(f"获取排行榜失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/alerts')
    def get_alerts():
        """获取预警列表"""
        try:
            unread_only = request.args.get('unread', False, type=bool)
            limit = request.args.get('limit', 50, type=int)
            
            alerts = db_manager.get_alerts(unread_only=unread_only, limit=limit)
            
            return jsonify({
                'success': True,
                'data': alerts
            })
            
        except Exception as e:
            app.logger.error(f"获取预警失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/chart/<symbol>/<chart_type>')
    def get_chart(symbol, chart_type):
        """获取图表"""
        try:
            # 检查多个可能的图表路径
            possible_paths = [
                f"charts/{symbol}_{chart_type}_chart.png",
                f"/Volumes/WDSSD/stock_analysis/charts/{symbol}_{chart_type}_chart.png",
                f"src/web/charts/{symbol}_{chart_type}_chart.png",
                f"/Volumes/WDSSD/stock_analysis/src/web/charts/{symbol}_{chart_type}_chart.png"
            ]
            
            chart_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    chart_path = path
                    break
            
            if chart_path:
                return send_file(chart_path, mimetype='image/png')
            else:
                app.logger.warning(f"找不到图表文件: {symbol}_{chart_type}_chart.png")
                app.logger.info(f"已检查路径: {possible_paths}")
                return jsonify({'success': False, 'message': '图表不存在'})
                
        except Exception as e:
            app.logger.error(f"获取图表失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/api/market_status')
    def get_market_status():
        """获取市场状态"""
        try:
            data_source = data_source_manager.get_source()
            market_status = data_source.get_market_status()
            
            return jsonify({
                'success': True,
                'data': market_status
            })
            
        except Exception as e:
            app.logger.error(f"获取市场状态失败: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'message': '页面不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'message': '服务器内部错误'}), 500
    
    return app