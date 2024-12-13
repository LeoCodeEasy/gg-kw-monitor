from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import json
import logging
import requests
import urllib3
from urllib.parse import unquote, urlparse, parse_qs
import os
import glob
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import ssl
from src.config import KeywordConfig
from src.utils.screenshot import save_screenshot, capture_screenshot
from src.core.results.deduplication import deduplicate_results

# 配置SSL
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# 禁用SSL警告
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings()

# 添加线程锁用于保存结果
save_lock = threading.Lock()

class GoogleAdMonitor:
    def __init__(self, target_market="in"):
        self.target_market = target_market
        self.setup_logging()
        self.driver = None  # 初始化时不创建driver
        
        # 创建保存目录
        self.screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
        
        # 配置requests会话
        self.session = requests.Session()
        self.session.verify = False  # 禁用SSL验证
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,  # 将日志级别改为 INFO
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('google_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_driver(self):
        """为每个线程创建独立的driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 添加实验性功能
        chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'en-US,en',
            'profile.default_content_setting_values.geolocation': 2,
            'profile.managed_default_content_settings.geolocation': 2,
            'profile.default_content_settings.geolocation': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'translate_blocked_languages': ['zh-CN', 'zh-TW'],
            'translate.enabled': False
        })
        
        # 设置移动端User-Agent
        mobile_user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        chrome_options.add_argument(f'user-agent={mobile_user_agent}')
        
        # 启用移动端模拟
        mobile_emulation = {
            "deviceMetrics": { "width": 390, "height": 844, "pixelRatio": 3.0 },
            "userAgent": mobile_user_agent
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 使用本地ChromeDriver
        service = Service('/opt/homebrew/bin/chromedriver')
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        # 执行反自动化检测的JavaScript代码
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        return driver

    def get_final_url(self, url, max_retries=3, timeout=10, backoff_factor=0.3):
        """获取最终的重定向URL，包含重试机制和错误处理"""
        if not url:
            return None
        
        # 特殊处理 Google Ads URL
        if 'google.com/aclk' in url:
            try:
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                
                # 检查是否存在目标URL参数
                target_url = None
                for param in ['adurl', 'dest', 'url']:
                    if param in params:
                        target_url = params[param][0]
                        break
                    
                if target_url:
                    # 递归调用以获取目标URL的最终重定向
                    return self.get_final_url(target_url)
            except Exception as e:
                self.logger.error(f"处理 Google Ads URL 时出错: {str(e)}")
        
        # 处理 App Store URLs
        if 'apps.apple.com' in url:
            try:
                parsed = urlparse(url)
                if parsed.scheme == 'itms-apps':
                    return url.replace('itms-apps://', 'https://')
                return url
            except Exception as e:
                self.logger.error(f"处理 App Store URL 时出错: {str(e)}")
                return url
            
        # 原有的重定向处理逻辑...
        session = requests.Session()
        session.max_redirects = 5
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            response = session.get(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers=headers,
                verify=False
            )
            
            if response.status_code == 200:
                return response.url
        except Exception as e:
            self.logger.error(f"获取最终URL失败: {url}, 错误: {str(e)}")
        
        return url

    def get_google_ads(self, keyword, driver):
        """获取Google广告结果"""
        ad_results = []
        raw_ads = []  # 用于暂存原始广告信息
        seen_links = set()  # 用于存储已见过的链接
        
        try:
            # 根据目标市场构建Google搜索URL
            market_params = {
                "in": {"gl": "in", "hl": "en-IN", "country": "india"},
            }
            
            params = market_params.get(self.target_market.lower(), {"gl": "us", "hl": "en"})
            base_url = (
                f"https://www.google.com/search?"
                f"gl={params['gl']}&"
                f"hl={params['hl']}&"
                f"source=mobile&"
                f"v=mobile&"
                f"mobile=1&"
                f"device=mobile&"
                f"nfpr=1&"
                f"gws_rd=cr&"
                f"pws=0"
            )
            
            self.logger.info(f"Searching in {params['gl'].upper()} market (mobile): {keyword}")
            
            search_url = f"{base_url}&q={keyword}"
            self.logger.info(f"访问URL: {search_url}")
            driver.get(search_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 尝试滚动页面以触发广告加载
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 移动端广告选择器
            ad_selectors = [
                "div.uEierd",  # 通用广告容器
            ]
            
            # 第一步：收集所有广告的基本信息
            total_ads = 0
            for selector in ad_selectors:
                ads = driver.find_elements(By.CSS_SELECTOR, selector)
                if ads:
                    total_ads = len(ads)
                    self.logger.info(f"关键词 '{keyword}' 找到 {total_ads} 个广告 (选择器: {selector})")
                    
                    for index, ad in enumerate(ads, 1):
                        try:
                            # 获取标题和链接
                            title = None
                            link = None
                            
                            # 获取标题
                            title_selectors = [
                                "div.CCgQ5", "div.v9i61e", "a[data-text-ad] div",
                                "div.BmP5tf", "div[role='heading']", "h3"
                            ]
                            for title_selector in title_selectors:
                                try:
                                    title_element = ad.find_element(By.CSS_SELECTOR, title_selector)
                                    title = title_element.text.strip()
                                    if title:
                                        break
                                except:
                                    continue
                            
                            if not title:
                                continue
                            
                            # 获取链接
                            link_selectors = [
                                "a[data-rw]", "a.sVXRqc", "a[ping]",
                                "a[data-pcu]", "a"
                            ]
                            for link_selector in link_selectors:
                                try:
                                    link_element = ad.find_element(By.CSS_SELECTOR, link_selector)
                                    link = link_element.get_attribute("href")
                                    if link:
                                        break
                                except:
                                    continue
                            
                            if not link:
                                continue
                                
                            # 检查链接是否已经存在
                            if link not in seen_links:
                                seen_links.add(link)
                                raw_ads.append({
                                    "title": title,
                                    "link": link,
                                    "position": len(raw_ads) + 1  # 使用实际位置
                                })
                                self.logger.info(f"关键词 '{keyword}' - 广告 {index}/{total_ads}: {title}")
                            
                        except Exception as e:
                            self.logger.error(f"处理关键词 '{keyword}' 的广告 {index} 时出错: {str(e)}")
                            continue
            
            self.logger.info(f"关键词 '{keyword}' 成功收集 {len(raw_ads)} 个有效广告")
            
            # 第二步：处理每个广告的落地页
            # 读取现有结果
            try:
                with open('all_results.json', 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_results = []
            
            # 处理每个广告
            new_ads = []
            for ad_info in raw_ads:
                try:
                    # 获取最终URL
                    final_url = self.get_final_url(ad_info["link"])
                    if not final_url:
                        continue
                    
                    # 解析域名
                    parsed_url = urlparse(final_url)
                    domain = parsed_url.netloc
                    
                    # 在现有结果中查找匹配的域名记录
                    existing_record = None
                    for record in existing_results:
                        if record.get('domain') == domain:
                            existing_record = record
                            break
                    
                    if existing_record:
                        # 使用现有截图
                        self.logger.info(f"使用现有截图: {existing_record['screenshot_path']}")
                        screenshot_filename = existing_record['screenshot_path']
                        
                        # 添加新的关键词记录（只在关键词和标题都不为空时）
                        if keyword and ad_info["title"]:
                            # 检查是否已存在相同关键词的记录
                            has_same_keyword = False
                            for record in existing_record["keyword_records"]:
                                if record.get("keyword") == keyword:
                                    # 如果新记录时间戳更新，则替换旧记录
                                    new_timestamp = datetime.now().isoformat()
                                    if new_timestamp > record["timestamp"]:
                                        record.update({
                                            "timestamp": new_timestamp,
                                            "market": self.target_market,
                                            "keyword": keyword,
                                            "title": ad_info["title"]
                                        })
                                    has_same_keyword = True
                                    break
                            
                            # 如果不存在相同关键词的记录，则添加新记录
                            if not has_same_keyword:
                                keyword_record = {
                                    "timestamp": datetime.now().isoformat(),
                                    "market": self.target_market,
                                    "keyword": keyword,
                                    "title": ad_info["title"]
                                }
                                existing_record["keyword_records"].insert(0, keyword_record)
                            
                            # 更新时间戳为最新记录的时间戳
                            existing_record["timestamp"] = existing_record["keyword_records"][0]["timestamp"]
                    else:
                        # 创建新的截图
                        self.logger.info(f"为新域名创建截图: {domain}")
                        screenshot_filename = capture_screenshot(final_url, driver)
                        
                        # 只在关键词和标题都不为空时创建新记录
                        if keyword and ad_info["title"]:
                            keyword_record = {
                                "timestamp": datetime.now().isoformat(),
                                "market": self.target_market,
                                "keyword": keyword,
                                "title": ad_info["title"]
                            }
                            # 创建新记录
                            new_record = {
                                "domain": domain,
                                "original_url": ad_info["link"],
                                "final_url": final_url,
                                "screenshot_path": screenshot_filename,
                                "timestamp": datetime.now().isoformat(),
                                "keyword_records": [keyword_record]
                            }
                            ad_results.append(new_record)
                            new_ads.append(new_record)
                    
                except Exception as e:
                    self.logger.error(f"处理广告落地页时出错: {str(e)}")
                    continue
            
            # 保存更新后的结果
            with open('all_results.json', 'w', encoding='utf-8') as f:
                json.dump(existing_results, f, ensure_ascii=False, indent=2)
                
            if not ad_results:
                self.logger.info(f"关键词 '{keyword}' 找到 {len(raw_ads)} 个广告，0 个新广告。")
            else:
                self.logger.info(f"关键词 '{keyword}' 找到 {len(raw_ads)} 个广告，{len(new_ads)} 个新广告。")
            
            return ad_results
            
        except Exception as e:
            self.logger.error(f"获取广告时出错: {str(e)}")
            return []

    def capture_landing_page(self, url, driver=None):
        """捕获落地页截图"""
        if not url:
            return None
        
        try:
            # 获取最终URL
            final_url = self.get_final_url(url)
            if not final_url:
                final_url = url
            
            # 使用统一的截图模块
            success, screenshot_filename, error = capture_screenshot(
                url=final_url,
                driver=driver,
                mobile=True,
                update_results=True,
                force_refresh=True  # 强制刷新，因为这是新的广告
            )
            
            if not success:
                self.logger.error(f"截图失败: {error}")
                return None
            
            return screenshot_filename
            
        except Exception as e:
            self.logger.error(f"截图过程出错: {str(e)}")
            return None

    def process_keyword(self, keyword, total_keywords, current_index):
        """处理单个关键词的方法"""
        driver = None
        try:
            driver = self.create_driver()  # 为每个线程创建新的driver
            self.logger.info(f"正在爬取第 {current_index}/{total_keywords} 个关键词: {keyword}")
            
            results = self.get_google_ads(keyword, driver)
            
            if results:
                # 对结果进行去重
                deduped_results = []
                seen_links = set()
                
                for result in results:
                    link = result.get('link')
                    if link not in seen_links:
                        seen_links.add(link)
                        deduped_results.append(result)
                
                # 保存去重后的结果
                with open('all_results.json', 'w', encoding='utf-8') as f:
                    json.dump(deduped_results, f, ensure_ascii=False, indent=2)
                return results
            
            return []
                
        except Exception as e:
            self.logger.error(f"爬取关键词 '{keyword}' 时出错: {str(e)}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            return []
        finally:
            if driver:
                try:
                    driver.quit()
                    time.sleep(1)  # 等待浏览器完全关闭
                except:
                    pass

    def monitor_keywords(self, keywords, max_workers=3):
        """并行监控关键词列表"""
        all_results = []
        total_keywords = len(keywords)
        
        # 创建线程池
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_keyword = {
                executor.submit(
                    self.process_keyword, 
                    keyword, 
                    total_keywords, 
                    i + 1
                ): 
                keyword 
                for i, keyword in enumerate(keywords)
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_keyword):
                keyword = future_to_keyword[future]
                try:
                    results = future.result()
                    if results:
                        # 为每个结果添加市场信息
                        for ad in results:
                            ad['market'] = self.target_market
                        all_results.extend(results)
                        
                        # 实时保存部分结果
                        with save_lock:
                            try:
                                with open('partial_results.json', 'w', encoding='utf-8') as f:
                                    json.dump(all_results, f, ensure_ascii=False, indent=2)
                            except Exception as save_error:
                                print(f"部分结果保存失败: {save_error}")
                            
                except Exception as e:
                    print(f"处理关键词 '{keyword}' 的任务失败: {e}")
        
        return all_results

def save_results(results, market, output_file='all_results.json'):
    """存监控结果到文件"""
    if not results:
        return []
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    current_time = datetime.now().isoformat()
    
    # 确保results目录存在
    results_dir = 'results'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    try:
        # 读取现有的结果（如果存在）
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_results = []
            
        # 创建一个以original_url为键的字典来存储现有结果
        results_dict = {}
        for result in existing_results:
            if result and isinstance(result, dict) and result.get('original_url'):
                key = result['original_url']
                if 'landing_page' in result:
                    del result['landing_page']
                results_dict[key] = result
                
        # 合并新结果
        for new_result in results:
            if not new_result or not isinstance(new_result, dict) or not new_result.get('original_url'):
                continue
                
            key = new_result['original_url']
            
            if key in results_dict:
                # 更新现有记录
                existing = results_dict[key]
                
                # 更新截图
                if new_result.get('screenshot_path'):
                    existing['screenshot_path'] = new_result['screenshot_path']
                
                # 添加新的关键词记录
                keyword_record = {
                    'timestamp': current_time,
                    'market': market,
                    'keyword': new_result.get('keyword_records', [{}])[0].get('keyword', ''),
                    'title': new_result.get('keyword_records', [{}])[0].get('title', '')
                }
                
                if 'keyword_records' not in existing:
                    existing['keyword_records'] = []
                    
                # 检查是否已存在相同的记录
                record_exists = False
                for record in existing['keyword_records']:
                    if (record.get('keyword') == keyword_record['keyword'] and 
                        record.get('title') == keyword_record['title']):
                        record_exists = True
                        break
                        
                if not record_exists:
                    existing['keyword_records'].append(keyword_record)
                
                # 更新其他字段
                existing['final_url'] = new_result.get('final_url', existing.get('final_url', ''))
                
            else:
                # 添加新记录
                formatted_result = {
                    'domain': new_result.get('domain', ''),
                    'original_url': new_result.get('original_url', ''),
                    'final_url': new_result.get('final_url', ''),
                    'screenshot_path': new_result.get('screenshot_path', ''),
                    'timestamp': current_time,
                    'keyword_records': [{
                        'timestamp': current_time,
                        'market': market,
                        'keyword': new_result.get('keyword_records', [{}])[0].get('keyword', ''),
                        'title': new_result.get('keyword_records', [{}])[0].get('title', '')
                    }]
                }
                results_dict[key] = formatted_result
        
        # 转换回列表并保存
        final_results = list(results_dict.values())
        
        # 保存到指定的输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
            
        return final_results
        
    except Exception as e:
        print(f"保存结果时出错: {str(e)}")
        return []

def main(output_file='all_results.json'):
    """主函数"""
    try:
        # 加载关键词
        keywords = load_keywords()
        if not keywords:
            print("没有找到关键词配置")
            return
            
        # 创建监控器实例并开始监控
        monitor = GoogleAdMonitor()
        results = monitor.monitor_keywords(keywords)
        
        # 保存结果到指定的输出文件
        if results:
            save_results(results, monitor.target_market, output_file)
            print(f"结果已保存到 {output_file}")
        else:
            print("没有找到新的广告结果")
            
    except Exception as e:
        print(f"运行出错: {str(e)}")

def load_keywords():
    """加载关键词列表"""
    try:
        return KeywordConfig.load_keywords()
    except Exception as e:
        print(f"Error loading keywords: {e}")
        return []

if __name__ == "__main__":
    main()
