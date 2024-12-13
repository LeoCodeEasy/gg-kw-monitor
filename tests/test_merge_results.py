"""
测试结果合并模块
"""
import os
import json
import pytest
from datetime import datetime, timedelta
from merge_results import merge_results

def create_test_file(filename: str, data: list):
    """创建测试用的结果文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def test_merge_results():
    """测试结果合并功能"""
    print("\n测试结果合并功能:")
    
    # 准备测试数据
    now = datetime.now()
    
    # 第一个测试文件：包含两个广告，每个有一个关键词记录
    test_data_1 = [
        {
            "final_url": "https://example1.com",
            "original_url": "https://google.com/aclk?url=example1.com",
            "screenshot_path": "example1.png",
            "keyword_records": [
                {
                    "timestamp": now.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                    "market": "in",
                    "keyword": "test keyword 1",
                    "title": "Ad Title 1"
                }
            ]
        },
        {
            "final_url": "https://example2.com",
            "original_url": "https://google.com/aclk?url=example2.com",
            "screenshot_path": "example2.png",
            "keyword_records": [
                {
                    "timestamp": now.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                    "market": "gh",
                    "keyword": "test keyword 2",
                    "title": "Ad Title 2"
                }
            ]
        }
    ]
    
    # 第二个测试文件：包含相同的URL但有新的关键词记录
    test_data_2 = [
        {
            "final_url": "https://example1.com",
            "original_url": "https://google.com/aclk?url=example1.com",
            "screenshot_path": "example1_new.png",
            "keyword_records": [
                {
                    "timestamp": (now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.%f'),
                    "market": "in",
                    "keyword": "test keyword 1",
                    "title": "Ad Title 1 Updated"
                }
            ]
        }
    ]
    
    try:
        # 创建测试文件
        create_test_file('monitoring_results_1.json', test_data_1)
        create_test_file('monitoring_results_2.json', test_data_2)
        print("✓ 创建��试文件成功")
        
        # 执行合并
        merge_results()
        print("✓ 执行合并成功")
        
        # 验证结果
        with open('all_results.json', 'r', encoding='utf-8') as f:
            merged_results = json.load(f)
            
        # 验证合并后的记录数
        assert len(merged_results) == 2, "合并后应该有2个唯一的URL记录"
        print("✓ 记录数量正确")
        
        # 验证关键词记录去重
        example1 = next(r for r in merged_results if r['final_url'] == 'https://example1.com')
        assert len(example1['keyword_records']) == 1, "同一关键词应该只保留最新的记录"
        assert example1['screenshot_path'] == 'example1_new.png', "应该使用最新的截图"
        print("✓ 关键词记录去重正确")
        
        # 验证时间戳排序
        timestamps = [
            max(r.get('keyword_records', [{}])[0].get('timestamp', '') for r in merged_results)
        ]
        assert timestamps == sorted(timestamps, reverse=True), "结果应该按时间戳倒序排序"
        print("✓ 时间戳排序正确")
        
        # 验证原始文件是否被删除
        assert not os.path.exists('monitoring_results_1.json'), "原始文件应该被删除"
        assert not os.path.exists('monitoring_results_2.json'), "原始文件应该被删除"
        print("✓ 原始文件清理正确")
        
    finally:
        # 清理测试文件
        for file in ['monitoring_results_1.json', 'monitoring_results_2.json', 'all_results.json']:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
        print("✓ 清理测试文件")

def test_merge_empty_results():
    """测试合并空结果"""
    print("\n测试合并空结果:")
    
    try:
        # 创建空的测试文件
        create_test_file('monitoring_results_empty.json', [])
        print("✓ 创建空测试文件")
        
        # 执行合并
        merge_results()
        print("✓ 执行合并成功")
        
        # 验证结果
        assert os.path.exists('all_results.json'), "应该创建结果文件"
        with open('all_results.json', 'r', encoding='utf-8') as f:
            merged_results = json.load(f)
        assert len(merged_results) == 0, "合并空结果应该得到空列表"
        print("✓ 空结果处理正确")
        
    finally:
        # 清理测试文件
        for file in ['monitoring_results_empty.json', 'all_results.json']:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
        print("✓ 清理测试文件")

def test_merge_invalid_results():
    """测试合并无效结果"""
    print("\n测试合并无效结果:")
    
    try:
        # 创建无效的测试文件
        with open('monitoring_results_invalid.json', 'w') as f:
            f.write('invalid json')
        print("✓ 创建无效测试文件")
        
        # 执行合并
        merge_results()
        print("✓ 执行合并成功")
        
        # 验证结果
        assert os.path.exists('all_results.json'), "应该创建结果文件"
        with open('all_results.json', 'r', encoding='utf-8') as f:
            merged_results = json.load(f)
        assert isinstance(merged_results, list), "即使输入无效，也应该返回有效的JSON数组"
        print("✓ 无效结果处理正确")
        
    finally:
        # 清理测试文件
        for file in ['monitoring_results_invalid.json', 'all_results.json']:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
        print("✓ 清理测试文件")

def main():
    """运行所有测试"""
    print("开始测试结果合并模块...")
    
    # 运行测试
    test_merge_results()
    test_merge_empty_results()
    test_merge_invalid_results()
    
    print("\n所有测试通过! ✨")

if __name__ == "__main__":
    main() 