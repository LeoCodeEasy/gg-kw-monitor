"""
截图模块测试
"""
import os
import pytest
from datetime import datetime
from src.utils.screenshot import (
    create_driver,
    capture_screenshot,
    wait_for_page_load,
    generate_filename,
    update_results_json
)

def test_mobile_screenshot():
    """测试移动端截图功能"""
    print("\n开始测试移动端截图功能:")
    
    # 测试URL列表
    test_urls = [
        "https://www.baidu.com",
        "https://www.google.com",
        "https://www.bing.com"
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        
        # 使用移动端模式截图
        success, filename, error = capture_screenshot(
            url=url,
            mobile=True,
            update_results=False
        )
        
        print(f"截图结果: {'成功' if success else '失败'}")
        print(f"文件名: {filename}")
        if error:
            print(f"错误信息: {error}")
            
        if success:
            # 检查文件是否存在
            screenshot_path = os.path.join('screenshots', filename)
            assert os.path.exists(screenshot_path), f"截图文件不存在: {screenshot_path}"
            
            # 检查文件大小
            file_size = os.path.getsize(screenshot_path)
            print(f"文件大小: {file_size} 字节")
            assert file_size > 0, "截图文件大小为0"
            
            # 检查文件名格式
            assert filename.endswith('.png'), "文件名应该以.png结尾"
            assert not any(c for c in filename if not (c.isalnum() or c == '.')), "文件名应该只包含字母数字和.png后缀"

def test_screenshot_with_different_options():
    """测试不同截图选项"""
    print("\n测试不同截图选项:")
    
    test_url = "https://www.example.com"
    
    # 测试配置列表
    test_configs = [
        {
            "name": "移动端",
            "options": {"mobile": True}
        },
        {
            "name": "桌面端",
            "options": {"mobile": False}
        }
    ]
    
    for config in test_configs:
        print(f"\n测试配置: {config['name']}")
        success, filename, error = capture_screenshot(
            url=test_url,
            **config['options'],
            update_results=False
        )
        
        print(f"截图结果: {'成功' if success else '失败'}")
        print(f"文件名: {filename}")
        if error:
            print(f"错误信息: {error}")
            
        if success:
            screenshot_path = os.path.join('screenshots', filename)
            assert os.path.exists(screenshot_path), f"截图文件不存在: {screenshot_path}"

def test_page_load_waiting():
    """测试页面加载等待功能"""
    print("\n测试页面加载等待功能:")
    
    # 创建驱动
    driver = create_driver(mobile_emulation=True)
    assert driver is not None, "创建驱动失败"
    
    try:
        # 测试动态页面
        url = "https://www.baidu.com"
        print(f"测试URL: {url}")
        
        # 访问页面
        driver.get(url)
        
        # 测试等待功能
        success = wait_for_page_load(driver)
        print(f"页面加载: {'成功' if success else '失败'}")
        assert success, "页面加载等���失败"
        
    finally:
        driver.quit()

def test_filename_generation():
    """测试文件名生成功能"""
    print("\n测试文件名生成功能:")
    
    test_urls = [
        "https://www.example.com/page?param=1",
        "https://sub.domain.com/path/to/page",
        "https://www.test-site.com/特殊字符"
    ]
    
    expected_results = {
        "https://www.example.com/page?param=1": "examplecom.png",
        "https://sub.domain.com/path/to/page": "subdomaincom.png",
        "https://www.test-site.com/特殊字符": "testsitecom.png"
    }
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        
        filename = generate_filename(url)
        print(f"生成的文件名: {filename}")
        
        # 验证文件名
        assert filename == expected_results[url], f"文件名不符合预期: 期望 {expected_results[url]}, 实际 {filename}"
        assert filename.endswith('.png'), "文件名应该以.png结尾"
        assert not any(c for c in filename if not (c.isalnum() or c == '.')), "文件名应该只包含字母数字和.png后缀"

def main():
    """运行所有测试"""
    print("开始测试截图模块...")
    
    # 确保截图目录存在
    os.makedirs('screenshots', exist_ok=True)
    
    # 运行测试
    test_mobile_screenshot()
    test_screenshot_with_different_options()
    test_page_load_waiting()
    test_filename_generation()
    
    print("\n所有测试完成! ✨")

if __name__ == "__main__":
    main() 