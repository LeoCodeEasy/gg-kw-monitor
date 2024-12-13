"""
数据清理模块测试
"""
import json
from src.utils.cleaner.handlers import (
    clean_google_urls,
    clean_landing_page,
    clean_global_data,
    clean_data
)

def test_clean_google_urls():
    """测试 Google URL 清理"""
    print("\n测试 Google URL 清理:")
    
    # 测试数据
    test_data = {
        'original_url': 'https://www.google.com/aclk?sa=L&ai=DChcSEwi...',
        'final_url': 'https://example.com?utm_source=google&utm_medium=cpc'
    }
    
    # 执行清理
    cleaned_data = clean_google_urls(test_data)
    print(f"原始 URL: {test_data['original_url']}")
    print(f"清理后 URL: {cleaned_data.get('original_url', '')}")
    
    assert isinstance(cleaned_data, dict), "清理后的数据应该是字典类型"
    print("✓ Google URL 清理测试通过")

def test_clean_landing_page():
    """测试落地页清理"""
    print("\n测试落地页清理:")
    
    # 测试数据
    test_data = {
        'final_url': 'https://example.com/page?param1=value1',
        'screenshot_path': '20241211_134310_examplecom.png'
    }
    
    # 执行清��
    cleaned_data = clean_landing_page(test_data)
    print(f"原始落地页: {test_data['final_url']}")
    print(f"清理后落地页: {cleaned_data.get('final_url', '')}")
    
    assert isinstance(cleaned_data, dict), "清理后的数据应该是字典类型"
    print("✓ 落地页清理测试通过")

def test_clean_global_data():
    """测试全局数据清理"""
    print("\n测试全局数据清理:")
    
    # 测试数据
    test_data = {
        'original_url': 'https://example.com',
        'final_url': 'https://example.com/page',
        'screenshot_path': 'screenshot.png',
        'keyword_records': [
            {
                'keyword': 'test keyword',
                'market': 'us',
                'timestamp': '2024-12-11T00:00:00'
            }
        ]
    }
    
    # 执行清理
    cleaned_data = clean_global_data(test_data)
    print(f"原始数据: {json.dumps(test_data, indent=2)}")
    print(f"清理后数据: {json.dumps(cleaned_data, indent=2)}")
    
    assert isinstance(cleaned_data, dict), "清理后的数据应该是字典类型"
    print("✓ 全局数据清理测试通过")

def test_clean_data():
    """测试完整的数据清理流程"""
    print("\n测试完整数据清理流程:")
    
    # 测试数据
    test_data = {
        'original_url': 'https://www.google.com/aclk?sa=L&ai=DChcSEwi...',
        'final_url': 'https://example.com/page?utm_source=google',
        'screenshot_path': 'screenshot.png',
        'keyword_records': [
            {
                'keyword': 'test keyword',
                'market': 'us',
                'timestamp': '2024-12-11T00:00:00'
            }
        ]
    }
    
    # 执行完整清理
    cleaned_data = clean_data(test_data)
    print(f"原始数据: {json.dumps(test_data, indent=2)}")
    print(f"清理后数据: {json.dumps(cleaned_data, indent=2)}")
    
    assert isinstance(cleaned_data, dict), "清理后的数据应该是字典类型"
    print("✓ 完整数据清理测试通过")

def main():
    """运行所有测试"""
    print("开始测试数据清理模块...")
    
    # 运行测试
    test_clean_google_urls()
    test_clean_landing_page()
    test_clean_global_data()
    test_clean_data()
    
    print("\n所有测试通过! ✨")

if __name__ == "__main__":
    main() 