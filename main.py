"""
A股散户分析系统 - 主程序入口
提供命令行接口和Web界面启动功能
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_source.factory import get_data_source_manager
from src.database.manager import DatabaseManager
from src.analysis.engine import AnalysisEngine
from config import PROJECT_NAME, VERSION


def setup_logging():
    """设置日志"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"stock_analysis_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def test_data_connection():
    """测试数据连接"""
    print("正在测试数据源连接...")
    
    # 获取数据源管理器
    data_manager = get_data_source_manager()
    
    if not data_manager.get_available_sources():
        print("❌ 没有可用的数据源！")
        print("请检查以下配置：")
        print("1. 网络连接是否正常")
        print("2. 是否已配置 TUSHARE_TOKEN 环境变量")
        print("3. 请访问 https://tushare.pro 注册并获取token")
        print("4. 在 .env 文件中设置: TUSHARE_TOKEN=your_token_here")
        return False
    
    print(f"✅ 可用数据源: {', '.join(data_manager.get_available_sources())}")
    
    # 测试获取股票列表
    try:
        source = data_manager.get_source()
        stock_list = source.get_stock_list()
        
        if not stock_list.empty:
            print(f"✅ 成功获取股票数据，共 {len(stock_list)} 只股票")
            return True
        else:
            print("❌ 获取股票数据失败")
            return False
    
    except Exception as e:
        print(f"❌ 数据连接测试失败: {e}")
        return False


def analyze_single_stock(symbol: str):
    """分析单只股票"""
    print(f"\n正在分析股票 {symbol}...")
    
    # 初始化组件
    db_manager = DatabaseManager()
    analysis_engine = AnalysisEngine(db_manager)
    
    # 执行分析
    result = analysis_engine.analyze_stock(symbol, days=120)
    
    if result['status'] == 'success':
        print(f"✅ 股票 {symbol} 分析完成")
        
        # 显示分析结果
        if result['summary']:
            summary = result['summary']
            basic_info = summary.get('basic_info', {})
            
            print(f"\n📊 基本信息:")
            print(f"   最新价格: {basic_info.get('latest_price', 'N/A')} 元")
            print(f"   涨跌幅: {basic_info.get('price_change_pct', 'N/A')}%")
            print(f"   成交量: {basic_info.get('volume', 'N/A')}")
            
            print(f"\n🔍 技术状态:")
            tech_status = summary.get('technical_status', {})
            for key, value in tech_status.items():
                print(f"   {key}: {value}")
            
            print(f"\n📈 投资建议: {summary.get('recommendation', 'N/A')}")
            print(f"   风险等级: {summary.get('risk_level', 'N/A')}")
            
            if result['signals']:
                print(f"\n⚡ 技术信号:")
                for signal in result['signals']:
                    print(f"   - {signal}")
        
        # 显示图表文件路径
        if result['charts']:
            print(f"\n📈 图表文件:")
            for chart_type, path in result['charts'].items():
                if os.path.exists(path):
                    print(f"   {chart_type}: {path}")
    
    else:
        print(f"❌ 股票 {symbol} 分析失败: {result.get('message', '未知错误')}")


def start_web_server():
    """启动Web服务器"""
    try:
        from src.web.app import create_app
        
        app = create_app()
        print(f"\n🚀 启动Web界面...")
        print(f"📱 访问地址: http://localhost:8080")
        print(f"按 Ctrl+C 停止服务器\n")
        
        app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
        
    except ImportError as e:
        print(f"❌ Web模块未完成: {e}")
        print("请先实现Web界面模块")
    except Exception as e:
        print(f"❌ 启动Web服务器失败: {e}")


def show_help():
    """显示帮助信息"""
    help_text = f"""
{PROJECT_NAME} v{VERSION}

用法:
    python main.py [命令] [参数]

命令:
    test        测试数据源连接
    analyze     分析股票（需要股票代码）
    web         启动Web界面
    help        显示帮助信息

示例:
    python main.py test                 # 测试数据连接
    python main.py analyze 000001       # 分析平安银行
    python main.py web                  # 启动Web界面

注意:
    - 首次运行必须先配置 TUSHARE_TOKEN 环境变量
    - 请访问 https://tushare.pro 注册并获取token
    - 在 .env 文件中设置: TUSHARE_TOKEN=your_token_here
    - 分析结果和图表保存在 output/ 和 charts/ 目录

更多信息请查看 README.md 文件
"""
    print(help_text)


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description=f'{PROJECT_NAME} v{VERSION}')
    parser.add_argument('command', nargs='?', default='help', 
                       help='命令: test/analyze/web/help')
    parser.add_argument('symbol', nargs='?', 
                       help='股票代码（用于analyze命令）')
    
    args = parser.parse_args()
    
    print(f"🏛️  {PROJECT_NAME} v{VERSION}")
    print("=" * 50)
    
    if args.command == 'test':
        success = test_data_connection()
        if success:
            print("\n✅ 系统检查通过，可以开始使用")
        else:
            print("\n❌ 系统检查失败，请检查配置")
            sys.exit(1)
    
    elif args.command == 'analyze':
        if not args.symbol:
            print("❌ 请提供股票代码")
            print("示例: python main.py analyze 000001")
            sys.exit(1)
        
        # 先测试连接
        if not test_data_connection():
            print("❌ 数据连接失败，无法进行分析")
            sys.exit(1)
        
        analyze_single_stock(args.symbol)
    
    elif args.command == 'web':
        # 先测试连接
        if not test_data_connection():
            print("❌ 数据连接失败，无法启动Web服务")
            sys.exit(1)
        
        start_web_server()
    
    elif args.command == 'help':
        show_help()
    
    else:
        print(f"❌ 未知命令: {args.command}")
        show_help()
        sys.exit(1)


if __name__ == '__main__':
    main()