import asyncio
from datetime import datetime
from urllib.parse import urlparse
import re
import os
from src.utils.screenshot import capture_screenshot

async def process_search_result(page, result, keyword, market):
    """处理单个搜索结果"""
    try:
        # 提取广告链接
        google_ad_url = await page.evaluate('(element) => element.querySelector("a")?.href', result)
        if not google_ad_url:
            return None
            
        # 检查是否是排除的域名
        parsed_url = urlparse(google_ad_url)
        domain = parsed_url.netloc.lower()
        
        # 检查完整域名和主域名
        if domain in config.EXCLUDED_DOMAINS:
            logger.info(f"跳过排除的域名: {google_ad_url}")
            return None
            
        # 检查子域名
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            main_domain = '.'.join(domain_parts[-2:])
            if main_domain in config.EXCLUDED_DOMAINS:
                logger.info(f"跳过排除的域名: {google_ad_url}")
                return None

        # 提取标题
        title = await page.evaluate('(element) => element.querySelector("div[role=\'heading\']")?.textContent', result)
        if not title:
            return None

        # 获取当前时间戳
        timestamp = datetime.now().isoformat()

        # 访问广告链接并获取最终 URL
        try:
            async with page.expect_navigation(timeout=30000):
                await result.click()
            final_url = page.url

            # 等待页面加载
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)

            # 使用通用截图模块
            success, screenshot_filename, error = capture_screenshot(final_url)
            if not success:
                logger.error(f"截图失败: {error}")
                screenshot_filename = None

            return {
                'original_url': google_ad_url,  # 保存原始的 Google 广告链接
                'final_url': final_url,  # 保存最终重定向后的 URL
                'screenshot_path': screenshot_filename,
                'keyword_records': [{
                    'timestamp': timestamp,
                    'keyword': keyword,
                    'market': market,
                    'title': title
                }]
            }

        except Exception as e:
            logger.error(f"处理URL时出错: {google_ad_url}, 错误: {str(e)}")
            return None

    except Exception as e:
        logger.error(f"处理搜索结果时出错: {str(e)}")
        return None 