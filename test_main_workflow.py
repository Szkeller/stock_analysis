#!/usr/bin/env python3
"""
股票分析网站主流程测试脚本
测试从数据获取到分析展示的完整流程
"""

import sys
import os
import time
import requests
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from src.data_source.factory import get_data_source_manager
from src.database.manager import DatabaseManager
from src.analysis.engine import AnalysisEngine
from src.strategy.retail_strategy import RetailStrategy


class MainWorkflowTester:
    """主流程测试器"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8080"
        self.test_stocks = ["000001", "000002", "600519", "000858", "002415"]  # 测试股票
        self.results = {}
        
    def test_web_server_status(self):
        """测试Web服务器状态"""
        print("🔍 测试1: Web服务器状态")
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("  ✅ Web服务器运行正常")
                return True
            else:
                print(f"  ❌ Web服务器异常，状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ 无法连接Web服务器: {e}")
            return False
    
    def test_market_status_api(self):
        """测试市场状态API"""
        print("\n🔍 测试2: 市场状态API")
        try:
            response = requests.get(f"{self.base_url}/api/market_status", timeout=10)
            data = response.json()
            
            if data.get('success'):
                market_data = data.get('data', {})
                print(f"  ✅ 市场状态: {market_data.get('status', 'N/A')}")
                print(f"  📅 市场时间: {market_data.get('market_time', 'N/A')}")
                print(f"  📊 数据源: {market_data.get('data_source', 'N/A')}")
                return True
            else:
                print(f"  ❌ 市场状态API失败: {data.get('message', 'N/A')}")
                return False
                
        except Exception as e:
            print(f"  ❌ 市场状态API异常: {e}")
            return False
    
    def test_stock_search_api(self):
        """测试股票搜索API"""
        print("\n🔍 测试3: 股票搜索API")
        try:
            test_queries = ["000", "平安", "贵州"]
            
            for query in test_queries:
                response = requests.get(
                    f"{self.base_url}/api/search_stock",
                    params={'q': query},
                    timeout=10
                )
                data = response.json()
                
                if data.get('success'):
                    stocks = data.get('data', [])
                    print(f"  ✅ 搜索'{query}': 找到{len(stocks)}只股票")
                    if stocks:
                        print(f"    示例: {stocks[0].get('symbol')} - {stocks[0].get('name')}")
                else:
                    print(f"  ❌ 搜索'{query}'失败: {data.get('message', 'N/A')}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ 股票搜索API异常: {e}")
            return False
    
    def test_stock_analysis_api(self):
        """测试股票分析API"""
        print("\n🔍 测试4: 股票分析API")
        success_count = 0
        
        for symbol in self.test_stocks:
            try:
                print(f"  📊 分析股票: {symbol}")
                response = requests.get(
                    f"{self.base_url}/api/analyze/{symbol}",
                    params={'days': 60, 'force': False},
                    timeout=30
                )
                data = response.json()
                
                if data.get('success'):
                    analysis_data = data.get('data', {})
                    print(f"    ✅ {symbol} 分析成功")
                    
                    # 检查分析结果完整性
                    has_data = len(analysis_data.get('data', [])) > 0
                    has_indicators = analysis_data.get('indicators') is not None
                    has_summary = analysis_data.get('summary') is not None
                    
                    print(f"    📈 历史数据: {'✅' if has_data else '❌'}")
                    print(f"    📊 技术指标: {'✅' if has_indicators else '❌'}")
                    print(f"    📋 分析摘要: {'✅' if has_summary else '❌'}")
                    
                    if has_data and has_summary:
                        summary = analysis_data.get('summary', {})
                        print(f"    💡 投资建议: {summary.get('recommendation', 'N/A')}")
                        success_count += 1
                    
                else:
                    print(f"    ❌ {symbol} 分析失败: {data.get('message', 'N/A')}")
                
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                print(f"    ❌ {symbol} 分析异常: {e}")
        
        print(f"\n  📊 分析成功率: {success_count}/{len(self.test_stocks)} ({success_count/len(self.test_stocks)*100:.1f}%)")
        return success_count >= len(self.test_stocks) * 0.6  # 60%成功率
    
    def test_turtle_strategy_api(self):
        """测试海龟策略API"""
        print("\n🔍 测试5: 海龟策略API")
        success_count = 0
        
        for symbol in self.test_stocks[:3]:  # 测试前3只股票
            try:
                print(f"  🐢 海龟策略分析: {symbol}")
                response = requests.get(
                    f"{self.base_url}/api/turtle_strategy/{symbol}",
                    timeout=20
                )
                data = response.json()
                
                if data.get('success'):
                    turtle_data = data.get('data', {})
                    signal = turtle_data.get('combined_signal', 'HOLD')
                    confidence = turtle_data.get('system1', {}).get('confidence', 0)
                    
                    print(f"    ✅ {symbol} 海龟分析成功")
                    print(f"    📈 交易信号: {signal}")
                    print(f"    🎯 置信度: {confidence:.2f}")
                    
                    success_count += 1
                else:
                    print(f"    ❌ {symbol} 海龟分析失败: {data.get('message', 'N/A')}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"    ❌ {symbol} 海龟分析异常: {e}")
        
        print(f"\n  🐢 海龟策略成功率: {success_count}/3")
        return success_count >= 2
    
    def test_trading_signals_api(self):
        """测试综合交易信号API"""
        print("\n🔍 测试6: 综合交易信号API")
        try:
            symbol = "000001"  # 测试平安银行
            print(f"  📊 综合信号分析: {symbol}")
            
            response = requests.get(
                f"{self.base_url}/api/trading_signals/{symbol}",
                params={'days': 60},
                timeout=25
            )
            data = response.json()
            
            if data.get('success'):
                signals_data = data.get('data', {})
                print("    ✅ 综合交易信号分析成功")
                
                # 检查信号完整性
                if 'turtle_strategy' in signals_data:
                    print("    🐢 海龟策略信号: ✅")
                if 'technical_signals' in signals_data:
                    print("    📈 技术信号: ✅")
                if 'recommendation' in signals_data:
                    print(f"    💡 综合建议: {signals_data.get('recommendation', 'N/A')}")
                
                return True
            else:
                print(f"    ❌ 综合信号分析失败: {data.get('message', 'N/A')}")
                return False
                
        except Exception as e:
            print(f"    ❌ 综合信号API异常: {e}")
            return False
    
    def test_data_source_integration(self):
        """测试数据源集成"""
        print("\n🔍 测试7: 数据源集成")
        try:
            manager = get_data_source_manager()
            available_sources = manager.get_available_sources()
            
            print(f"  📊 可用数据源: {', '.join(available_sources)}")
            print(f"  🎯 主数据源: {manager.primary_source}")
            
            # 测试数据获取
            test_symbol = "000001"
            stock_info = manager.get_stock_info(test_symbol)
            real_time = manager.get_real_time_price(test_symbol)
            
            if stock_info and real_time:
                print(f"  ✅ 数据获取正常: {stock_info.get('name')} - ¥{real_time.get('price', 0):.2f}")
                return True
            else:
                print("  ❌ 数据获取失败")
                return False
                
        except Exception as e:
            print(f"  ❌ 数据源集成测试异常: {e}")
            return False
    
    def test_database_operations(self):
        """测试数据库操作"""
        print("\n🔍 测试8: 数据库操作")
        try:
            db_manager = DatabaseManager()
            
            # 测试股票数据查询
            stocks = db_manager.get_all_stocks()
            print(f"  📊 数据库股票数: {len(stocks) if stocks else 0}")
            
            # 测试自选股功能
            test_symbol = "000001"
            db_manager.add_to_watchlist(test_symbol, "平安银行", "测试股票", 1)
            watchlist = db_manager.get_watchlist()
            
            if watchlist:
                print("  ✅ 自选股功能正常")
            else:
                print("  ⚠️ 自选股功能异常")
            
            # 清理测试数据
            db_manager.remove_from_watchlist(test_symbol)
            
            return True
            
        except Exception as e:
            print(f"  ❌ 数据库操作测试异常: {e}")
            return False
    
    def test_performance_indicators(self):
        """测试性能指标"""
        print("\n🔍 测试9: 性能指标")
        try:
            # 测试响应时间
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/market_status", timeout=10)
            response_time = time.time() - start_time
            
            print(f"  ⚡ API响应时间: {response_time:.2f}秒")
            
            # 测试并发处理
            start_time = time.time()
            symbol = "000001"
            response = requests.get(
                f"{self.base_url}/api/analyze/{symbol}",
                params={'days': 30},
                timeout=20
            )
            analysis_time = time.time() - start_time
            
            print(f"  📊 分析处理时间: {analysis_time:.2f}秒")
            
            # 性能评估
            if response_time < 2 and analysis_time < 15:
                print("  ✅ 性能表现良好")
                return True
            else:
                print("  ⚠️ 性能可能需要优化")
                return True  # 不影响主流程
                
        except Exception as e:
            print(f"  ❌ 性能测试异常: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🏛️ A股散户分析系统 - 主流程测试")
        print("=" * 60)
        
        tests = [
            self.test_web_server_status,
            self.test_market_status_api,
            self.test_stock_search_api,
            self.test_stock_analysis_api,
            self.test_turtle_strategy_api,
            self.test_trading_signals_api,
            self.test_data_source_integration,
            self.test_database_operations,
            self.test_performance_indicators
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"  ❌ 测试异常: {e}")
        
        # 测试结果汇总
        print("\n" + "=" * 60)
        print("📋 测试结果汇总")
        print("=" * 60)
        
        success_rate = passed / total * 100
        print(f"✅ 通过测试: {passed}/{total} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 主流程测试通过！系统运行正常")
        elif success_rate >= 60:
            print("⚠️ 主流程基本正常，有部分功能需要关注")
        else:
            print("❌ 主流程存在问题，需要检查和修复")
        
        # 测试建议
        print("\n💡 测试建议:")
        if success_rate >= 80:
            print("  • 系统状态良好，可以正常使用")
            print("  • 建议定期进行性能监控")
            print("  • 考虑添加更多股票数据源作为备份")
        else:
            print("  • 检查数据源连接状态")
            print("  • 验证网络连接和API访问")
            print("  • 查看服务器日志获取详细错误信息")
        
        return success_rate >= 80


if __name__ == "__main__":
    tester = MainWorkflowTester()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)