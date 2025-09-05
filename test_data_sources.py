"""
数据源测试脚本
测试所有可用的数据源连接状态和数据获取能力
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.data_source.factory import get_data_source_manager, DataSourceFactory
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def test_all_data_sources():
    """测试所有数据源"""
    print("=" * 60)
    print("🔍 股票数据源连接测试")
    print("=" * 60)
    
    # 获取数据源信息
    source_info = DataSourceFactory.get_source_info()
    
    print(f"\n📊 可用数据源列表：")
    for name, info in source_info.items():
        print(f"  • {info['name']} ({name})")
        print(f"    - 描述：{info['description']}")
        print(f"    - 功能：{', '.join(info['features'])}")
        print(f"    - 免费：{'是' if info['free'] else '否'}")
        print(f"    - 实时：{'是' if info['realtime'] else '否'}")
        print(f"    - 优先级：{info['priority']}")
        print()
    
    # 创建数据源管理器
    print("🚀 正在初始化数据源管理器...")
    manager = get_data_source_manager()
    
    # 测试各个数据源连接
    print("\n🔗 测试数据源连接状态：")
    connection_results = manager.connect_all()
    
    connected_sources = []
    failed_sources = []
    
    for source_name, connected in connection_results.items():
        status = "✅ 连接成功" if connected else "❌ 连接失败"
        print(f"  {source_name}: {status}")
        
        if connected:
            connected_sources.append(source_name)
        else:
            failed_sources.append(source_name)
    
    # 显示统计信息
    print(f"\n📈 连接统计：")
    print(f"  • 成功连接：{len(connected_sources)} 个")
    print(f"  • 连接失败：{len(failed_sources)} 个")
    print(f"  • 成功率：{len(connected_sources) / len(connection_results) * 100:.1f}%")
    
    if connected_sources:
        print(f"\n✅ 可用数据源：{', '.join(connected_sources)}")
        print(f"🎯 当前主数据源：{manager.primary_source}")
    
    if failed_sources:
        print(f"\n❌ 不可用数据源：{', '.join(failed_sources)}")
    
    # 测试数据获取
    if connected_sources:
        print(f"\n🧪 测试数据获取功能...")
        test_symbol = "000001"  # 测试股票：平安银行
        
        print(f"测试股票：{test_symbol}")
        
        # 测试获取股票基本信息
        try:
            stock_info = manager.get_stock_info(test_symbol)
            if stock_info:
                print(f"  ✅ 基本信息：{stock_info.get('name', 'N/A')} - 价格：{stock_info.get('price', 0):.2f}")
            else:
                print(f"  ❌ 无法获取基本信息")
        except Exception as e:
            print(f"  ❌ 获取基本信息失败：{e}")
        
        # 测试获取实时价格
        try:
            real_time = manager.get_real_time_price(test_symbol)
            if real_time:
                print(f"  ✅ 实时数据：价格 {real_time.get('price', 0):.2f}, 涨跌幅 {real_time.get('pct_change', 0):.2f}%")
            else:
                print(f"  ❌ 无法获取实时数据")
        except Exception as e:
            print(f"  ❌ 获取实时数据失败：{e}")
        
        # 测试获取历史数据
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            df = manager.get_daily_prices(test_symbol, start_date, end_date)
            if not df.empty:
                print(f"  ✅ 历史数据：获取到 {len(df)} 条记录")
            else:
                print(f"  ⚠️ 历史数据为空")
        except Exception as e:
            print(f"  ❌ 获取历史数据失败：{e}")
    
    # 推荐最佳数据源组合
    print(f"\n💡 使用建议：")
    
    if 'eastmoney' in connected_sources:
        print("  🔥 推荐使用东方财富作为主数据源（免费、稳定、功能全面）")
    elif 'tushare' in connected_sources:
        print("  📊 可以使用Tushare作为主数据源（专业数据，需要token）")
    elif 'akshare' in connected_sources:
        print("  🆓 可以使用AKShare作为主数据源（免费，功能丰富）")
    elif any(source in connected_sources for source in ['sina', 'qqstock', 'wangyi']):
        available_real_time = [s for s in ['sina', 'qqstock', 'wangyi'] if s in connected_sources]
        print(f"  ⚡ 可以使用 {', '.join(available_real_time)} 获取实时数据")
    
    if len(connected_sources) >= 2:
        print("  🔄 建议启用多数据源备份，提高系统稳定性")
    
    print(f"\n🎉 数据源测试完成！")
    
    return len(connected_sources) > 0


if __name__ == "__main__":
    success = test_all_data_sources()
    
    if success:
        print("\n✅ 至少有一个数据源可用，系统可以正常运行！")
        exit(0)
    else:
        print("\n❌ 所有数据源都不可用，请检查网络连接或配置！")
        exit(1)