"""
URL 处理模块
"""
from .handlers import (
    normalize_url,
    is_excluded_domain,
    extract_google_ad_url
)

__all__ = [
    'normalize_url',
    'is_excluded_domain',
    'extract_google_ad_url'
]
