"""
配置模块测试
"""
import os
import json
from pathlib import Path

from src.config import (
    BaseConfig,
    GoogleConfig,
    KeywordConfig,
    MonitorConfig,
    BrowserConfig,
    StorageConfig,
    TimeConfig
)

def test_base_config():
    """测试基础配置"""
    print("\n测试基础配置:")
    print(f"项目根目录: {BaseConfig.ROOT_DIR}")
    print(f"资源目录: {BaseConfig.RESOURCES_DIR}")
    
    # 测试目录创建
    BaseConfig.ensure_directories()
    assert BaseConfig.RESOURCES_DIR.exists(), "资源目录创建失败"
    print("✓ 基础配置测试通过")

def test_keyword_config():
    """测试关键词配置"""
    print("\n测试关键词配置:")
    
    # 测试保存关键词
    test_keywords = ["test1", "test2", "test3"]
    success = KeywordConfig.save_keywords(test_keywords)
    assert success, "关键词保存失败"
    print("✓ 关键词保存成功")
    
    # 测试加载关键词
    loaded_keywords = KeywordConfig.load_keywords()
    assert loaded_keywords == test_keywords, "加载的关键词与保存的不匹��"
    print("✓ 关键词加载成功")
    
    # 恢复原始关键词
    original_keywords = ["no experience work at home jobs"]
    KeywordConfig.save_keywords(original_keywords)
    print("✓ 关键词配置测试通过")

def test_storage_config():
    """测试存储配置"""
    print("\n测试存储配置:")
    
    # 测试目录创建
    StorageConfig.ensure_directories()
    assert StorageConfig.RESULTS_DIR.exists(), "结果目录创建失败"
    assert StorageConfig.SCREENSHOTS_DIR.exists(), "截图目录创建失败"
    print("✓ 存储目录创建成功")
    
    # 测试文件名前缀
    assert StorageConfig.RESULT_FILE_PREFIX == "monitoring_results_", "结果文件前缀不正确"
    print("✓ 存储配置测试通过")

def test_monitor_config():
    """测试监控配置"""
    print("\n测试监控配置:")
    
    # 测试市场配置
    assert 'in' in MonitorConfig.MARKETS, "印度市场配置缺失"
    assert 'gh' in MonitorConfig.MARKETS, "加纳市场配置缺失"
    print("✓ 市场配置正确")
    
    # 测试排除域名
    assert 'in3.tinrh.com' in MonitorConfig.EXCLUDED_DOMAINS, "排除域名配置缺失"
    print("✓ 排除域名配置正确")
    
    # 测试关键词加载
    keywords = MonitorConfig.get_keywords()
    assert isinstance(keywords, list), "关键词加载失败"
    print("✓ 监控配置测试通过")

def main():
    """运行所有测试"""
    print("开始测试配置模块...")
    
    # 运行测试
    test_base_config()
    test_keyword_config()
    test_storage_config()
    test_monitor_config()
    
    print("\n所有测试通过! ✨")

if __name__ == "__main__":
    main() 