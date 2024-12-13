from src.config import KeywordConfig

def test_keywords_loading():
    """测试关键词加载功能"""
    print("1. 测试加载所有关键词配置:")
    all_keywords = KeywordConfig.load_all_keywords()
    print("完整配置:", all_keywords)
    print("\n" + "="*50 + "\n")
    
    print("2. 测试只加载启用的关键词:")
    enabled_keywords = KeywordConfig.load_keywords()
    print("启用的关键词:", enabled_keywords)
    
if __name__ == '__main__':
    test_keywords_loading()
