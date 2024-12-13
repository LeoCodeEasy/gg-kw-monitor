"""
URL 处理模块测试
"""
import json
from urllib.parse import urlparse
from src.utils.url.handlers import (
    normalize_url,
    is_excluded_domain,
    extract_google_ad_url
)

def test_normalize_url():
    """测试 URL 规范化"""
    print("\n测试 URL 规范化:")
    
    test_cases = [
        # Google 广告链接
        {
            'input': 'https://www.google.com/aclk?sa=L&ai=DChcSEwi...&adurl=https://example.com',
            'expected': 'https://example.com'
        },
        # 带跟踪参数的 URL
        {
            'input': 'https://example.com/page?utm_source=google&param1=value1',
            'expected': 'https://example.com/page?param1=value1'
        },
        # 子域名
        {
            'input': 'https://sub1.sub2.example.com/path',
            'expected': 'https://example.com/path'
        },
        # getpaidtoreadb.com
        {
            'input': 'https://getpaidtoreadb.com/page?param=value',
            'expected': 'https://getpaidtoreadb.com/page'
        }
    ]
    
    for case in test_cases:
        result = normalize_url(case['input'])
        print(f"输入: {case['input']}")
        print(f"期望: {case['expected']}")
        print(f"实际: {result}")
        assert result == case['expected'], f"URL 规范化失败: {case['input']}"
        print("✓ 测试通过")
    
    print("✓ URL 规范化测试通过")

def test_excluded_domain():
    """测试域名排除"""
    print("\n测试域名排除:")
    
    test_cases = [
        # 完整匹配
        {
            'url': 'https://in3.tinrh.com/page',
            'expected': True
        },
        # 主域名匹配
        {
            'url': 'https://sub.tinrh.com/page',
            'expected': True
        },
        # 不匹配
        {
            'url': 'https://example.com/page',
            'expected': False
        }
    ]
    
    for case in test_cases:
        result = is_excluded_domain(case['url'])
        print(f"测试 URL: {case['url']}")
        print(f"期望结果: {case['expected']}")
        print(f"实际结果: {result}")
        assert result == case['expected'], f"域名排除检查失败: {case['url']}"
        print("✓ 测试通过")
    
    print("✓ 域名排除测试通过")

def test_extract_google_ad_url():
    """测试 Google 广告 URL 提取"""
    print("\n测试 Google 广告 URL 提取:")
    
    test_cases = [
        # adurl 参数
        {
            'input': 'https://www.google.com/aclk?sa=L&ai=DChcSEwi...&adurl=https://example.com',
            'expected': 'https://example.com'
        },
        # dest 参数
        {
            'input': 'https://www.google.com/url?dest=https://example.org',
            'expected': 'https://example.org'
        },
        # 非广告链接
        {
            'input': 'https://example.com',
            'expected': None
        }
    ]
    
    for case in test_cases:
        result = extract_google_ad_url(case['input'])
        print(f"输入: {case['input']}")
        print(f"期望: {case['expected']}")
        print(f"实际: {result}")
        assert result == case['expected'], f"Google 广告 URL 提取失败: {case['input']}"
        print("✓ 测试通过")
    
    print("✓ Google 广告 URL 提取测试通过")

def main():
    """运行所有测试"""
    print("开始测试 URL 处理模块...")
    
    # 运行测试
    test_normalize_url()
    test_excluded_domain()
    test_extract_google_ad_url()
    
    print("\n所有测试通过! ✨")

if __name__ == "__main__":
    main() 