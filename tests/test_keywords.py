"""
关键词管理模块测试
"""
import json
import pytest
from pathlib import Path
from src.config import KeywordConfig, BaseConfig
from app import app

def test_keywords_file_location():
    """测试关键词文件位置"""
    print("\n测试关键词文件位置:")
    
    # 验证配置的文件路径
    expected_path = BaseConfig.RESOURCES_DIR / 'keywords.json'
    actual_path = KeywordConfig.KEYWORDS_FILE
    
    print(f"期望路径: {expected_path}")
    print(f"实际路径: {actual_path}")
    
    assert actual_path == expected_path, "关键词文件路径配置错误"
    print("✓ 文件路径配置正确")
    
    # 保存测试关键词以验证实际保存位置
    test_keywords = ["test keyword"]
    KeywordConfig.save_keywords(test_keywords)
    
    # 验证文件是否在正确位置
    assert actual_path.exists(), "关键词文件未在配置的位置创建"
    print("✓ 文件保存在正确位置")
    
    print("✓ 文件位置测试通过")

def test_load_keywords():
    """测试加载关键词"""
    print("\n测试加载关键词:")
    
    # 加载关键词
    keywords = KeywordConfig.load_keywords()
    print(f"当前关键词列表: {keywords}")
    
    # 验证加载的是正确位置的文件
    file_path = KeywordConfig.KEYWORDS_FILE
    print(f"加载自: {file_path}")
    
    assert isinstance(keywords, list), "关键词列表应该是列表类型"
    print("✓ 加载关键词测试通过")

def test_save_keywords():
    """测试保存关键词"""
    print("\n测试保存关键词:")
    
    # 备份当前关键词
    original_keywords = KeywordConfig.load_keywords()
    
    # 测试数据
    test_keywords = [
        "test keyword 1",
        "test keyword 2",
        "test keyword 3"
    ]
    
    # 保存测试关键词
    success = KeywordConfig.save_keywords(test_keywords)
    assert success, "保存关键词失败"
    print("✓ 保存关键词成功")
    
    # 验证保存的关键词
    loaded_keywords = KeywordConfig.load_keywords()
    assert loaded_keywords == test_keywords, "加载的关键词与保存的不匹配"
    print("✓ 验证保存的关键词成功")
    
    # 验证文件位置
    file_path = KeywordConfig.KEYWORDS_FILE
    assert file_path.exists(), f"文件未保存在正确位置: {file_path}"
    print(f"✓ 文件已保存到: {file_path}")
    
    # 恢复原始关键词
    KeywordConfig.save_keywords(original_keywords)
    print("✓ 保存关键词测试通过")

def test_add_keyword():
    """测试添加关键词"""
    print("\n测试添加关键词:")
    
    # 备份当前关键词
    original_keywords = KeywordConfig.load_keywords()
    
    # 测试添加新关键词
    new_keyword = "new test keyword"
    success = KeywordConfig.add_keyword(new_keyword)
    assert success, "添加关键词失败"
    
    # 验证关键词已添加
    current_keywords = KeywordConfig.load_keywords()
    assert new_keyword in current_keywords, "新关键词未被添加"
    print(f"✓ 成功添加关键词: {new_keyword}")
    
    # 验证文件位置
    file_path = KeywordConfig.KEYWORDS_FILE
    assert file_path.exists(), f"文件未保存在正确位置: {file_path}"
    print(f"✓ 文件已保存到: {file_path}")
    
    # 测试添加重复关键词
    success = KeywordConfig.add_keyword(new_keyword)
    assert success, "处理重复关键词失败"
    current_keywords = KeywordConfig.load_keywords()
    assert current_keywords.count(new_keyword) == 1, "出现重复关键词"
    print("✓ 重��关键词处理正确")
    
    # 恢复原始关键词
    KeywordConfig.save_keywords(original_keywords)
    print("✓ 添加关键词测试通过")

def test_remove_keyword():
    """测试移除关键词"""
    print("\n测试移除关键词:")
    
    # 备份当前关键词
    original_keywords = KeywordConfig.load_keywords()
    
    # 准备测试数据
    test_keywords = ["keyword1", "keyword2", "keyword3"]
    KeywordConfig.save_keywords(test_keywords)
    
    # 测试移除存在的关键词
    keyword_to_remove = "keyword2"
    success = KeywordConfig.remove_keyword(keyword_to_remove)
    assert success, "移除关键词失败"
    
    # 验证关键词已移除
    current_keywords = KeywordConfig.load_keywords()
    assert keyword_to_remove not in current_keywords, "关键词未被移除"
    print(f"✓ 成功移除关键词: {keyword_to_remove}")
    
    # 验证文件位置
    file_path = KeywordConfig.KEYWORDS_FILE
    assert file_path.exists(), f"文件未保存在正确位置: {file_path}"
    print(f"✓ 文件已保存到: {file_path}")
    
    # 测试移除不存在的关键词
    success = KeywordConfig.remove_keyword("non-existent-keyword")
    assert success, "处理不存在的关键词失败"
    print("✓ 处理不存在的关键词正确")
    
    # 恢复原始关键词
    KeywordConfig.save_keywords(original_keywords)
    print("✓ 移除关键词测试通过")

def test_web_api():
    """测试 Web API 接口"""
    print("\n测试 Web API 接口:")
    
    # 创建测试客户端
    client = app.test_client()
    
    # 备份当前关键词
    original_keywords = KeywordConfig.load_keywords()
    
    # 测试获取关键词
    print("测试获取关键词:")
    response = client.get('/api/keywords')
    assert response.status_code == 200, "获取关键词请求失败"
    data = response.get_json()
    assert 'keywords' in data, "响应中缺少 keywords 字段"
    print("✓ 获取关键词成功")
    
    # 测试保存关键词
    print("\n测试保存关键词:")
    test_keywords = ["test1", "test2", "test3"]
    response = client.post('/api/keywords', 
                         json={'keywords': test_keywords})
    assert response.status_code == 200, "保存关键词请求失败"
    data = response.get_json()
    assert 'message' in data, "响应中缺少 message 字段"
    
    # 验证保存结果
    saved_keywords = KeywordConfig.load_keywords()
    assert saved_keywords == test_keywords, "保存的关键词与预期不符"
    print("✓ 保存关键词成功")
    
    # 测试添加关键词
    print("\n测试添加关键词:")
    new_keyword = "test4"
    response = client.put('/api/keywords',
                        json={'keyword': new_keyword})
    assert response.status_code == 200, "添加关键词请求失败"
    
    # 验证添加结果
    current_keywords = KeywordConfig.load_keywords()
    assert new_keyword in current_keywords, "新关键词未被添加"
    print("✓ 添加关键词成功")
    
    # 测试删除关键词
    print("\n测试删除关键词:")
    response = client.delete(f'/api/keywords/{new_keyword}')
    assert response.status_code == 200, "删除关键词请求失败"
    
    # 验证删除结果
    current_keywords = KeywordConfig.load_keywords()
    assert new_keyword not in current_keywords, "关键词未被删除"
    print("✓ 删除关键词成功")
    
    # 测试错误处理
    print("\n测试错误处理:")
    
    # 测试无效的保存请求
    response = client.post('/api/keywords', 
                         json={'keywords': "not a list"})
    assert response.status_code == 400, "应该拒绝无效的关键词格式"
    print("✓ 无效格式处理正确")
    
    # 测试空关键词添加
    response = client.put('/api/keywords',
                        json={'keyword': ""})
    assert response.status_code == 400, "应该拒绝空关键词"
    print("✓ 空关键词处理正确")
    
    # 恢复原始关键词
    KeywordConfig.save_keywords(original_keywords)
    print("\n✓ Web API 测试通过")

def main():
    """运行所有测试"""
    print("开始测试关键词管理模块...")
    
    # 运行测试
    test_keywords_file_location()
    test_load_keywords()
    test_save_keywords()
    test_add_keyword()
    test_remove_keyword()
    test_web_api()  # 新增的 Web API 测试
    
    print("\n所有测试通过! ✨")

if __name__ == "__main__":
    main() 