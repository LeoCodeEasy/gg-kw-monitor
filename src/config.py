import json
import os

class KeywordConfig:
    KEYWORDS_FILE = 'resources/keywords.json'

    @classmethod
    def load_keywords(cls):
        """加载关键词配置"""
        try:
            if not os.path.exists(cls.KEYWORDS_FILE):
                return {}
            with open(cls.KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    print("Invalid keywords data format")
                    return {}
                return data
        except Exception as e:
            print(f"Error loading keywords: {str(e)}")
            return {}

    @classmethod
    def save_keywords(cls, keywords_data):
        """保存关键词配置"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(cls.KEYWORDS_FILE), exist_ok=True)
            
            # 确保数据格式正确
            if not isinstance(keywords_data, dict):
                print("Invalid keywords data format")
                return False
            
            # 验证数据结构
            for category, data in keywords_data.items():
                if not isinstance(data, dict):
                    print(f"Invalid category data format for {category}")
                    return False
                
                if 'enabled' not in data or not isinstance(data['enabled'], bool):
                    data['enabled'] = True
                
                if 'keywords' not in data or not isinstance(data['keywords'], list):
                    data['keywords'] = []
                
                # 统一关键词格式
                keywords = []
                for kw in data['keywords']:
                    if isinstance(kw, str):
                        keywords.append({
                            'text': kw,
                            'enabled': True
                        })
                    elif isinstance(kw, dict) and 'text' in kw:
                        if 'enabled' not in kw:
                            kw['enabled'] = True
                        keywords.append(kw)
                data['keywords'] = keywords
                
            # 保存数据
            with open(cls.KEYWORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(keywords_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving keywords: {str(e)}")
            return False

    @classmethod
    def get_enabled_keywords(cls):
        """获取所有已启用的关键词"""
        keywords = cls.load_keywords()
        enabled_keywords = []
        
        for category, data in keywords.items():
            if not data.get('enabled', False):
                continue
                
            for kw in data.get('keywords', []):
                if isinstance(kw, str):
                    enabled_keywords.append(kw)
                elif isinstance(kw, dict) and kw.get('enabled', True):
                    enabled_keywords.append(kw['text'])
                    
        return enabled_keywords

    @classmethod
    def validate_keyword_format(cls, keyword_data):
        """验证关键词数据格式"""
        if not isinstance(keyword_data, dict):
            return False
            
        required_fields = {'text', 'enabled'}
        return all(field in keyword_data for field in required_fields)
