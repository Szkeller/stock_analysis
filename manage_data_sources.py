"""
数据源管理工具
提供数据源的启用、禁用、优先级调整等功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.data_source.factory import get_data_source_manager, DataSourceFactory, reset_data_source_manager
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.config_file = "config.py"
        self.source_info = DataSourceFactory.get_source_info()
    
    def show_status(self):
        """显示当前数据源状态"""
        print("=" * 70)
        print("📊 数据源状态管理")
        print("=" * 70)
        
        try:
            # 导入当前配置
            sys.path.insert(0, os.path.dirname(__file__))
            from config import DATA_SOURCES
            
            print("\n🔧 当前配置：")
            print("-" * 50)
            
            for source_name, config in DATA_SOURCES.items():
                info = self.source_info.get(source_name, {})
                status = "✅ 启用" if config.get('enabled', True) else "❌ 禁用"
                priority = config.get('priority', 99)
                
                print(f"{info.get('name', source_name)} ({source_name})")
                print(f"  状态：{status}")
                print(f"  优先级：{priority}")
                print(f"  描述：{config.get('description', 'N/A')}")
                if 'features' in config:
                    print(f"  功能：{', '.join(config['features'])}")
                print()
            
            # 测试连接状态
            print("🔗 连接测试：")
            print("-" * 50)
            
            manager = get_data_source_manager()
            connection_results = manager.connect_all()
            
            for source_name, connected in connection_results.items():
                status = "🟢 在线" if connected else "🔴 离线"
                print(f"  {source_name}: {status}")
            
            print(f"\n🎯 当前主数据源：{manager.primary_source}")
            
        except Exception as e:
            print(f"❌ 获取状态失败：{e}")
    
    def enable_source(self, source_name: str):
        """启用数据源"""
        if source_name not in self.source_info:
            print(f"❌ 未知的数据源：{source_name}")
            return False
        
        try:
            self._update_source_config(source_name, {'enabled': True})
            print(f"✅ 已启用数据源：{source_name}")
            return True
        except Exception as e:
            print(f"❌ 启用失败：{e}")
            return False
    
    def disable_source(self, source_name: str):
        """禁用数据源"""
        if source_name not in self.source_info:
            print(f"❌ 未知的数据源：{source_name}")
            return False
        
        try:
            self._update_source_config(source_name, {'enabled': False})
            print(f"✅ 已禁用数据源：{source_name}")
            return True
        except Exception as e:
            print(f"❌ 禁用失败：{e}")
            return False
    
    def set_priority(self, source_name: str, priority: int):
        """设置数据源优先级"""
        if source_name not in self.source_info:
            print(f"❌ 未知的数据源：{source_name}")
            return False
        
        if priority < 1 or priority > 10:
            print(f"❌ 优先级必须在1-10之间")
            return False
        
        try:
            self._update_source_config(source_name, {'priority': priority})
            print(f"✅ 已设置 {source_name} 优先级为：{priority}")
            return True
        except Exception as e:
            print(f"❌ 设置优先级失败：{e}")
            return False
    
    def set_primary(self, source_name: str):
        """设置主数据源"""
        if source_name not in self.source_info:
            print(f"❌ 未知的数据源：{source_name}")
            return False
        
        try:
            # 先测试连接
            reset_data_source_manager()
            manager = get_data_source_manager()
            
            if source_name not in manager.get_available_sources():
                print(f"❌ 数据源 {source_name} 不可用或连接失败")
                return False
            
            manager.set_primary_source(source_name)
            print(f"✅ 已设置主数据源为：{source_name}")
            return True
        except Exception as e:
            print(f"❌ 设置主数据源失败：{e}")
            return False
    
    def _update_source_config(self, source_name: str, updates: dict):
        """更新数据源配置"""
        # 读取当前配置文件
        with open(self.config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 这里简化处理，实际项目中可能需要更复杂的配置更新逻辑
        # 由于配置文件格式复杂，这里只提示用户手动修改
        print(f"⚠️ 请手动更新配置文件 {self.config_file} 中 {source_name} 的配置：")
        for key, value in updates.items():
            print(f"   {key}: {value}")
    
    def recommend_sources(self):
        """推荐数据源配置"""
        print("💡 数据源使用建议：")
        print("-" * 50)
        
        print("🔥 推荐配置（优先级从高到低）：")
        print("  1. 东方财富 (eastmoney) - 免费、稳定、数据全面")
        print("     • 优势：完全免费，数据及时，接口稳定")
        print("     • 劣势：无")
        print()
        
        print("  2. Tushare (tushare) - 专业数据接口")
        print("     • 优势：数据质量高，功能专业")
        print("     • 劣势：免费用户有API限制，需要token")
        print()
        
        print("  3. AKShare (akshare) - 开源数据接口")
        print("     • 优势：完全开源免费，功能丰富")
        print("     • 劣势：依赖第三方接口，稳定性一般")
        print()
        
        print("  4. 新浪财经 (sina) - 实时数据补充")
        print("     • 优势：实时性好")
        print("     • 劣势：只有实时数据，无历史数据")
        print()
        
        print("  5. 腾讯股票 (qqstock) - 备用选择")
        print("     • 优势：有K线数据")
        print("     • 劣势：接口不太稳定")
        print()
        
        print("  6. 网易财经 (wangyi) - 备用选择")
        print("     • 优势：数据格式简单")
        print("     • 劣势：功能有限")
        print()
        
        print("\n🎯 最佳实践：")
        print("  • 启用多个数据源作为备份")
        print("  • 东方财富设为最高优先级")
        print("  • 如有Tushare token，可设为第二优先级")
        print("  • 实时数据可使用新浪财经作为补充")


def main():
    """主函数"""
    manager = DataSourceManager()
    
    if len(sys.argv) < 2:
        print("📋 数据源管理工具使用说明：")
        print("-" * 50)
        print("  python manage_data_sources.py status           # 查看状态")
        print("  python manage_data_sources.py enable <源名称>   # 启用数据源")
        print("  python manage_data_sources.py disable <源名称>  # 禁用数据源")
        print("  python manage_data_sources.py priority <源名称> <优先级>  # 设置优先级")
        print("  python manage_data_sources.py primary <源名称>  # 设置主数据源")
        print("  python manage_data_sources.py recommend        # 查看推荐配置")
        print()
        print("📊 可用数据源：")
        for name, info in manager.source_info.items():
            print(f"  • {name} - {info['name']}")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        manager.show_status()
    
    elif command == "enable":
        if len(sys.argv) < 3:
            print("❌ 请指定要启用的数据源名称")
            return
        manager.enable_source(sys.argv[2])
    
    elif command == "disable":
        if len(sys.argv) < 3:
            print("❌ 请指定要禁用的数据源名称")
            return
        manager.disable_source(sys.argv[2])
    
    elif command == "priority":
        if len(sys.argv) < 4:
            print("❌ 请指定数据源名称和优先级")
            return
        try:
            priority = int(sys.argv[3])
            manager.set_priority(sys.argv[2], priority)
        except ValueError:
            print("❌ 优先级必须是数字")
    
    elif command == "primary":
        if len(sys.argv) < 3:
            print("❌ 请指定主数据源名称")
            return
        manager.set_primary(sys.argv[2])
    
    elif command == "recommend":
        manager.recommend_sources()
    
    else:
        print(f"❌ 未知命令：{command}")


if __name__ == "__main__":
    main()