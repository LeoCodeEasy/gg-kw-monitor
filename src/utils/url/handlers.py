"""
URL 处理模块：处理所有与 URL 相关的操作
"""
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Optional
import logging

from src.config import MonitorConfig

logger = logging.getLogger(__name__)

def normalize_url(url: str) -> str:
    """
    标准化 URL，处理 Google 广告链接和其他特殊情况
    
    Args:
        url: 原始 URL
        
    Returns:
        str: 标准化后的 URL
    """
    if not url:
        return ''
    
    try:
        # 处理 Google 广告链接
        if 'google.com/aclk' in url or 'google.com/url' in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # 尝试从 Google 广告链接中提取目标 URL
            for param in ['adurl', 'dest', 'url', 'q']:
                if param in params:
                    target_url = params[param][0]
                    # 递归处理提取出的 URL
                    return normalize_url(target_url)
        
        # 处理最终的目标 URL
        parsed = urlparse(url)
        
        # 确保 scheme 存在
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
        
        domain = parsed.netloc.lower()
        
        # 特殊处理 getpaidtoreadb.com
        if 'getpaidtoreadb.com' in domain:
            path = parsed.path
            if not path or path == '/':
                path = ''
            return f"https://getpaidtoreadb.com{path}"
        
        # 提取主域名（合并子域名）
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            if domain_parts[-2] not in ['com', 'org', 'net', 'edu', 'gov']:
                domain = '.'.join(domain_parts[-2:])
            else:
                domain = '.'.join(domain_parts[-3:])
        
        # 重建规范化的 URL
        path = parsed.path
        if not path:
            path = '/'
        
        normalized = f"https://{domain}{path}"
        
        # 移除所有跟踪参数
        if parsed.query:
            params = parse_qs(parsed.query)
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 
                'utm_content', 'utm_term', 'fbclid', 'gclid', 
                '_ga', 'gbraid', 'gad_source'
            }
            filtered_params = {
                k: v for k, v in params.items() 
                if k not in tracking_params
            }
            if filtered_params:
                normalized += '?' + urlencode(filtered_params, doseq=True)
        
        return normalized.rstrip('/')
        
    except Exception as e:
        logger.error(f"URL 标准化失败: {url}, 错误: {str(e)}")
        return url

def is_excluded_domain(url: str) -> bool:
    """
    检查 URL 是否属于被排除的域名
    
    Args:
        url: 要检查的 URL
        
    Returns:
        bool: 如果域名在排除列表中返回 True，否则返回 False
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # 检查完整域名
        if domain in MonitorConfig.EXCLUDED_DOMAINS:
            return True
            
        # 检查子域名
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            main_domain = '.'.join(domain_parts[-2:])
            if main_domain in MonitorConfig.EXCLUDED_DOMAINS:
                return True
                
        return False
    except Exception as e:
        logger.error(f"检查排除域名失败: {url}, 错误: {str(e)}")
        return False

def extract_google_ad_url(url: str) -> Optional[str]:
    """
    从 Google 广告链接中提取目标 URL
    
    Args:
        url: Google 广告链接
        
    Returns:
        Optional[str]: 提取出的目标 URL，如果提取失败则返回 None
    """
    try:
        if 'google.com/aclk' in url or 'google.com/url' in url:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            for param in ['adurl', 'dest', 'url', 'q']:
                if param in params:
                    return params[param][0]
        return None
    except Exception as e:
        logger.error(f"提取 Google 广告 URL 失败: {url}, 错误: {str(e)}")
        return None 