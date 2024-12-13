"""
运行所有测试
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试模块
from tests.test_config import main as test_config
from tests.test_cleaner import main as test_cleaner
from tests.test_url import main as test_url
from tests.test_keywords import main as test_keywords

def main():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行所有测试...")
    print("=" * 50)
    
    # 配置模块测试
    print("\n配置模块测试")
    print("-" * 30)
    test_config()
    
    # 数据清理模块测试
    print("\n数据清理模块测试")
    print("-" * 30)
    test_cleaner()
    
    # URL 处理模块测试
    print("\n URL 处理模块测试")
    print("-" * 30)
    test_url()
    
    # 关键词管理模块测试
    print("\n关键词管理模块测试")
    print("-" * 30)
    test_keywords()
    
    print("\n" + "=" * 50)
    print("所有测试完成! 🎉")
    print("=" * 50)

if __name__ == "__main__":
    main() 