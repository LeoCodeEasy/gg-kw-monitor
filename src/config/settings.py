"""
配置模块：管理所有配置项
"""
import json
import os
from typing import List, Dict, Set
from pathlib import Path

class BaseConfig:
    """基础配置类"""
    # 项目根目录
    ROOT_DIR = Path(__file__).parent.parent.parent
    
    # 资源目录
    RESOURCES_DIR = ROOT_DIR / 'resources'
    
    @classmethod
    def ensure_directories(cls) -> None:
        """确保所有必要的目录都存在"""
        for directory in [cls.RESOURCES_DIR]:
            os.makedirs(directory, exist_ok=True)

class GoogleConfig:
    """Google 搜索相关配置"""
    SEARCH_URL: str = "https://www.google.com/search"
    DOMAINS: Dict[str, str] = {
        'us': 'google.com',
        'uk': 'google.co.uk',
        'in': 'google.co.in',
        'au': 'google.com.au',
        'gh': 'google.com.gh',
    }

class KeywordConfig:
    """关键词相关配置"""
    KEYWORDS_FILE = BaseConfig.RESOURCES_DIR / 'keywords.json'
    
    @classmethod
    def load_keywords(cls) -> List[str]:
        """从文件加载有效的关键词列表"""
        try:
            if not os.path.exists(cls.KEYWORDS_FILE):
                return []
            with open(cls.KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 收集所有启用的关键词
            enabled_keywords = []
            for category, category_data in data.items():
                if category_data.get('enabled', True):  # 如果分类被启用
                    for keyword in category_data.get('keywords', []):
                        if keyword.get('enabled', False):  # 如果关键词被启用
                            enabled_keywords.append(keyword['text'])
            return enabled_keywords
        except Exception as e:
            print(f"加载关键词文件失败: {e}")
            return []
    
    @classmethod
    def load_all_keywords(cls) -> Dict:
        """加载完整的关键词配置"""
        try:
            if not os.path.exists(cls.KEYWORDS_FILE):
                return {}
            with open(cls.KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载关键词文件失败: {e}")
            return {}
    
    @classmethod
    def save_keywords(cls, keywords_data: Dict) -> bool:
        """保存关键词配置到文件"""
        try:
            os.makedirs(os.path.dirname(cls.KEYWORDS_FILE), exist_ok=True)
            with open(cls.KEYWORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump(keywords_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存关键词失败: {e}")
            return False
    
    @classmethod
    def add_keyword(cls, category: str, keyword: str, enabled: bool = True) -> bool:
        """添加新关键词到指定分类"""
        try:
            keywords_data = cls.load_all_keywords()
            
            # 如果分类不存在，创建新分类
            if category not in keywords_data:
                keywords_data[category] = {
                    "keywords": [],
                    "enabled": True
                }
            
            # 检查关键词是否已存在
            for kw in keywords_data[category]["keywords"]:
                if kw["text"] == keyword:
                    return True
            
            # 添加新关键词
            keywords_data[category]["keywords"].append({
                "text": keyword,
                "enabled": enabled
            })
            
            return cls.save_keywords(keywords_data)
        except Exception as e:
            print(f"添加关键词失败: {e}")
            return False
    
    @classmethod
    def remove_keyword(cls, category: str, keyword: str) -> bool:
        """从指定分类中移除关键词"""
        try:
            keywords_data = cls.load_all_keywords()
            if category in keywords_data:
                keywords_data[category]["keywords"] = [
                    kw for kw in keywords_data[category]["keywords"]
                    if kw["text"] != keyword
                ]
                return cls.save_keywords(keywords_data)
            return True
        except Exception as e:
            print(f"移除关键词失败: {e}")
            return False
    
    @classmethod
    def toggle_keyword(cls, category: str, keyword: str) -> bool:
        """切换关键词的启用状态"""
        try:
            keywords_data = cls.load_all_keywords()
            if category in keywords_data:
                for kw in keywords_data[category]["keywords"]:
                    if kw["text"] == keyword:
                        kw["enabled"] = not kw["enabled"]
                        return cls.save_keywords(keywords_data)
            return False
        except Exception as e:
            print(f"切换关键词状态失败: {e}")
            return False

class MonitorConfig:
    """监控相关配置"""
    # 要监控的市场（国家/地区）
    MARKETS: List[str] = ['in', 'gh']
    
    # 排除的域名列表
    EXCLUDED_DOMAINS: Set[str] = {
        'in3.tinrh.com',
        'tinrh.com',
    }
    
    # 关键词列表（动态加载）
    @classmethod
    def get_keywords(cls) -> List[str]:
        return KeywordConfig.load_keywords()

class BrowserConfig:
    """浏览器配置"""
    
    # 浏览器启动参数
    LAUNCH_ARGS = [
        '--headless',  # 无头模式
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-software-rasterizer'
    ]
    
    # 截图配置
    SCREENSHOT_WIDTH = 1920
    SCREENSHOT_HEIGHT = 1080
    SCREENSHOTS_DIR = 'screenshots'  # 截图保存目录

    # 超时配置
    PAGE_LOAD_TIMEOUT = 30  # 页面加载超时时间(秒)
    SCRIPT_TIMEOUT = 30     # 脚本执行超时时间(秒)
    
    # 重试配置
    MAX_RETRIES = 3        # 最大重试次数
    RETRY_DELAY = 2        # 重试间隔(秒)

class StorageConfig:
    """存储相关配置"""
    # 目录配置
    RESULTS_DIR = BaseConfig.ROOT_DIR / 'results'
    SCREENSHOTS_DIR = BaseConfig.ROOT_DIR / 'screenshots'
    
    # 文件名格式
    RESULT_FILE_PREFIX: str = 'monitoring_results_'
    SCREENSHOT_FILE_PREFIX: str = ''
    
    @classmethod
    def ensure_directories(cls) -> None:
        """确保存储目录存在"""
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)
        os.makedirs(cls.SCREENSHOTS_DIR, exist_ok=True)

class TimeConfig:
    """时间相关配置"""
    # 延迟设置（秒）
    MIN_DELAY: int = 2
    MAX_DELAY: int = 5
    
    # 重试设置
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

# 初始化必要的目录
BaseConfig.ensure_directories()
StorageConfig.ensure_directories()

# 导出所有配置类
__all__ = [
    'BaseConfig',
    'GoogleConfig',
    'KeywordConfig',
    'MonitorConfig',
    'BrowserConfig',
    'StorageConfig',
    'TimeConfig'
] 