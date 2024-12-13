"""
截图工具模块：处理所有与截图相关的操作
"""
import os
import time
import random
from datetime import datetime
from urllib.parse import urlparse
import re
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
from PIL import Image
import io

from src.config import BrowserConfig

logger = logging.getLogger(__name__)

# 移动设备列表
MOBILE_DEVICES = [
    {
        "name": "iPhone 12 Pro",
        "width": 390,
        "height": 844,
        "pixelRatio": 3.0,
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
    },
    {
        "name": "iPhone 13",
        "width": 390,
        "height": 844,
        "pixelRatio": 3.0,
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    },
    {
        "name": "Pixel 5",
        "width": 393,
        "height": 851,
        "pixelRatio": 2.75,
        "userAgent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"
    },
    {
        "name": "Samsung Galaxy S21",
        "width": 360,
        "height": 800,
        "pixelRatio": 3.0,
        "userAgent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36"
    }
]

# 语言和地区列表
LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-CA,en;q=0.9",
    "en-AU,en;q=0.9",
    "zh-CN,zh;q=0.9,en;q=0.8",
    "zh-TW,zh;q=0.9,en;q=0.8",
    "ja-JP,ja;q=0.9,en;q=0.8",
    "ko-KR,ko;q=0.9,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8"
]

# 时区列表
TIMEZONES = [
    "America/New_York",
    "Europe/London",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Australia/Sydney",
    "Europe/Paris",
    "Asia/Singapore",
    "America/Los_Angeles"
]

def get_random_device():
    """随机选择一个移动设备配置"""
    return random.choice(MOBILE_DEVICES)

def generate_random_viewport_size():
    """生成随机的视口大小"""
    base_width = random.randint(360, 400)
    base_height = random.randint(800, 900)
    return base_width + random.randint(-10, 10), base_height + random.randint(-10, 10)

def create_driver(mobile_emulation=False):
    """
    创建浏览器驱动
    
    Args:
        mobile_emulation: 是否启用移动端模拟
        
    Returns:
        webdriver.Chrome: 浏览器驱动实例
    """
    try:
        options = Options()
        
        # 添加基本配置
        for arg in BrowserConfig.LAUNCH_ARGS:
            options.add_argument(arg)

        # 随机选择语言和地区
        options.add_argument(f'--lang={random.choice(LANGUAGES)}')
        
        # 随机选择时区
        options.add_argument(f'--timezone={random.choice(TIMEZONES)}')
        
        if mobile_emulation:
            # 随机选择设备配置
            device = get_random_device()
            width, height = generate_random_viewport_size()
            
            # 设置移动端模拟
            mobile_emulation = {
                "deviceMetrics": {
                    "width": width,
                    "height": height,
                    "pixelRatio": device["pixelRatio"]
                },
                "userAgent": device["userAgent"]
            }
            options.add_experimental_option("mobileEmulation", mobile_emulation)
            
            # 添加随机的 User-Agent
            options.add_argument(f'user-agent={device["userAgent"]}')
        
        # 添加随机的 WebGL 指纹
        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--use-fake-device-for-media-stream')
        
        # 禁用自动化标志
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 添加随机的 WebGL 和 Canvas 指纹
        prefs = {
            'webrtc.ip_handling_policy': 'disable_non_proxied_udp',
            'webrtc.multiple_routes_enabled': False,
            'webrtc.nonproxied_udp_enabled': False
        }
        options.add_experimental_option('prefs', prefs)
        
        driver = webdriver.Chrome(options=options)
        
        # 执行反自动化检测的JavaScript代码
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                // 覆盖 navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 随机化 Canvas 指纹
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(type) {
                    const context = originalGetContext.apply(this, arguments);
                    if (type === '2d') {
                        const originalFillText = context.fillText;
                        context.fillText = function() {
                            context.shadowColor = `rgb(${Math.random()*255},${Math.random()*255},${Math.random()*255})`;
                            context.shadowBlur = Math.random() * 3;
                            context.shadowOffsetX = Math.random() * 2;
                            context.shadowOffsetY = Math.random() * 2;
                            return originalFillText.apply(this, arguments);
                        }
                    }
                    return context;
                };
                
                // 随机化 AudioContext 指纹
                const originalOfflineAudioContext = window.OfflineAudioContext;
                window.OfflineAudioContext = class extends originalOfflineAudioContext {
                    constructor() {
                        super(...arguments);
                        const originalCreateOscillator = this.createOscillator;
                        this.createOscillator = function() {
                            const oscillator = originalCreateOscillator.apply(this, arguments);
                            const originalStart = oscillator.start;
                            oscillator.start = function() {
                                oscillator.detune.value = Math.random() * 10;
                                return originalStart.apply(this, arguments);
                            };
                            return oscillator;
                        };
                    }
                };
            '''
        })
        
        # 随机化屏幕分辨率
        if mobile_emulation:
            driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'mobile': True,
                'width': width,
                'height': height,
                'deviceScaleFactor': device["pixelRatio"],
                'screenOrientation': {'type': 'portraitPrimary', 'angle': 0}
            })
        
        return driver
    except Exception as e:
        logger.error(f"创建浏览器驱动失败: {str(e)}")
        return None

def wait_for_indeed_page(driver, timeout=30):
    """
    专门处理 Indeed 页面的加载等待
    """
    try:
        wait = WebDriverWait(driver, timeout)
        
        # 等待页面基本元素加载
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 等待工作列表容器加载
        wait.until(EC.presence_of_element_located((By.ID, "mosaic-provider-jobcards")))
        
        # 等待页面完全加载
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        # 额外等待，确保所有内容都加载完成
        time.sleep(random.uniform(2, 4))
        
        return True
        
    except Exception as e:
        logger.error(f"等待 Indeed 页面加载失败: {str(e)}")
        return False

# 添加 App Store 特定的等待函数
def wait_for_appstore_page(driver, timeout=45):
    """
    专门处理 Apple App Store 页面的加载等待
    
    Args:
        driver: 浏览器驱动实例
        timeout: 超时时间（秒）
        
    Returns:
        bool: 是否加载成功
    """
    try:
        wait = WebDriverWait(driver, timeout)
        
        # 等待页面基本元素加载
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # 等待 App Store 页面特定元素
        selectors = [
            'h1.product-header__title',  # App 标题
            '.product-hero__media',      # App 图标
            '.animation-wrapper'         # 加载动画容器
        ]
        
        for selector in selectors:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            except:
                logger.warning(f"App Store 元素未找到: {selector}")
                continue
        
        # 等待页面完全加载
        wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        # 额外等待，确保所有内容都加载完成
        time.sleep(random.uniform(1, 5))
        
        # 尝试等待加载动画消失
        try:
            wait.until_not(EC.presence_of_element_located((By.CLASS_NAME, 'loading-spinner')))
        except:
            logger.warning("加载动画元素未找到或未消失")
        
        # 最后再等待一段时间，确保页面完全渲染
        time.sleep(random.uniform(2, 3))
        
        return True
        
    except Exception as e:
        logger.error(f"等待 App Store 页面加载失败: {str(e)}")
        return False

def wait_for_page_load(driver, timeout=30):  # 增加默认超时时间
    """
    等待页面完全加载
    
    Args:
        driver: 浏览器驱动实例
        timeout: 超时时间（秒）
        
    Returns:
        bool: 是否加载成功
    """
    try:
        # 添加随机延迟
        time.sleep(random.uniform(1, 3))
        
        current_url = driver.current_url.lower()
        
        # 检查是否是特定类型的页面
        if 'apps.apple.com' in current_url:
            return wait_for_appstore_page(driver, timeout=45)
        elif 'indeed.com' in current_url:
            return wait_for_indeed_page(driver, timeout)
        elif any(domain in current_url for domain in ['plus500.com', 'moomoo.com', 'talentcorenet.com']):
            # 这些网站需要更长的加载时间
            timeout = 40
            
        wait = WebDriverWait(driver, timeout)
        
        # 等待 body 元素出现
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception as e:
            logger.warning(f"等待body元素超时: {str(e)}")
            # 继续执行，因为有些网站可能不会触发这个条件
            
        # 随机滚动页面
        try:
            driver.execute_script(f'window.scrollTo(0, {random.randint(1, 1)});')
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.warning(f"页面滚动失败: {str(e)}")
            
        # 等待页面 ready state 为 complete
        try:
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        except Exception as e:
            logger.warning(f"等待页面readyState超时: {str(e)}")
            # 某些网站可能永远不会达到complete状态，继续执行
            
        # 等待所有图片加载完成
        try:
            wait.until(lambda d: d.execute_script('''
                return Array.from(document.images).every((img) => {
                    return img.complete && img.naturalHeight !== 0
                });
            '''))
        except Exception as e:
            logger.warning(f"等待图片加载超时: {str(e)}")
            
        # 等待 AJAX 请求完成
        try:
            wait.until(lambda d: d.execute_script('''
                return window.jQuery ? jQuery.active === 0 : true;
            '''))
        except Exception as e:
            logger.warning(f"等待AJAX请求超时: {str(e)}")
            
        # 额外的等待时间，根据网站类型调整
        if 'plus500.com' in current_url or 'moomoo.com' in current_url:
            time.sleep(random.uniform(3, 5))  # 这些网站需要更长的等待时间
        else:
            time.sleep(random.uniform(2, 4))
            
        return True
        
    except Exception as e:
        logger.error(f"等待页面加载失败: {str(e)}")
        # 即使有错误也尝试截图
        return True

def save_screenshot(driver, url, save_path=None, domain=None):
    """
    统一的截图保存函数
    :param driver: WebDriver实例
    :param url: 网页URL
    :param save_path: 保存路径，如果为None则自动生成
    :param domain: 域名，用于生成文件名，如果为None则从URL中提取
    :return: 保存的文件路径
    """
    try:
        if domain is None:
            domain = extract_domain(url)
        
        if save_path is None:
            # 生成文件名
            filename = domain.replace('.', '').replace('/', '') + '.jpg'
            save_path = os.path.join(os.getcwd(), filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        
        # 等待页面加载
        time.sleep(2)
        
        # 获取页面高度
        height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
        
        # 设置窗口大小
        driver.set_window_size(1920, height)
        
        # 创建临时PNG文件路径
        temp_png = save_path.rsplit('.', 1)[0] + '_temp.png'
        
        # 截图为PNG
        driver.save_screenshot(temp_png)
        
        try:
            # 转换为JPG并压缩
            with Image.open(temp_png) as img:
                # 如果图片太大，进行等比例缩放
                if img.height > 4000:
                    ratio = 4000 / img.height
                    new_size = (int(img.width * ratio), 4000)
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # 保存为JPG格式，质量为85
                img.convert('RGB').save(save_path, 'JPEG', quality=85, optimize=True)
        finally:
            # 删除临时PNG文件
            if os.path.exists(temp_png):
                os.remove(temp_png)
        
        return save_path
        
    except Exception as e:
        print(f"截图保存失败: {str(e)}")
        return None

def extract_domain(url):
    """
    从URL中提取域名
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not domain:
            # 如果无法获取域名，使用URL的一部分作为文件名
            domain = re.sub(r'[^\w\-_]', '', url[:50])
        
        # 移除特殊字符
        domain = re.sub(r'[^\w\-_]', '', domain)
        
        return domain
    except Exception as e:
        print(f"域名提取失败: {str(e)}")
        return 'unknown'

def capture_screenshot(
    url: str,
    driver=None,
    mobile: bool = False,
    update_results: bool = True,
    force_refresh: bool = False
) -> str:
    """
    捕获网页截图
    
    Args:
        url (str): 要截图的网页URL
        driver: 可选的现有WebDriver实例
        mobile (bool): 是否使用移动端模式
        update_results (bool): 是否更新结果文件，只在复用已有截图时有效
        force_refresh (bool): 是否强制刷新截图，即使已存在也重新截图
    
    Returns:
        str: 截图文件名，如果失败则返回空字符串
    """
    try:
        # 生成文件名和路径
        screenshot_filename = extract_domain(url) + '.jpg'
        screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'screenshots')
        screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
        
        # 如果截图已存在且不需要强制刷新
        if os.path.exists(screenshot_path) and not force_refresh:
            logger.info(f"使用已有截图: {screenshot_filename}")
            if update_results:
                update_results_json(url, screenshot_filename)
            return screenshot_filename
        
        # 确保目录存在
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # 如果没有提供driver，创建一个新的
        should_quit = False
        if driver is None:
            driver = create_driver(mobile_emulation=mobile)
            should_quit = True
            
        try:
            # 访问页面
            driver.get(url)
            
            # 等待页面加载
            _wait_for_page_by_url(driver, url)
            
            # 保存截图
            save_screenshot(driver, url, screenshot_path)
            
            if update_results:
                update_results_json(url, screenshot_filename)
                
            return screenshot_filename
            
        finally:
            if should_quit:
                driver.quit()
                
    except Exception as e:
        logger.error(f"截图失败: {str(e)}")
        return ""

def _wait_for_page_by_url(driver, url: str):
    """根据URL选择合适的等待策略"""
    if "indeed.com" in url.lower():
        wait_for_indeed_page(driver)
    elif "apps.apple.com" in url.lower():
        wait_for_appstore_page(driver)
    else:
        wait_for_page_load(driver)

def update_results_json(url: str, screenshot_filename: str) -> bool:
    """
    更新 all_results.json 中的截图路径
    
    Args:
        url: 网页URL
        screenshot_filename: 新的截图文件名
        
    Returns:
        bool: 是否更新成功
    """
    try:
        # 读取现有数据
        with open('all_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # 获取当前URL的域名
        current_domain = extract_domain(url)
        
        # 如果 screenshot_filename 是元组，只取文件名部分
        if isinstance(screenshot_filename, (list, tuple)):
            screenshot_filename = screenshot_filename[1]
        
        # 更新截图路径
        updated = False
        for result in results:
            # 使用域名匹配而不是完整URL匹配
            if extract_domain(result.get('final_url', '')) == current_domain:
                result['screenshot_path'] = screenshot_filename
                updated = True
        
        if updated:
            # 保存更新后的数据
            with open('all_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"已更新 all_results.json 中的截图路径: {screenshot_filename}")
            return True
            
        logger.warning(f"未找到匹配的域名记录: {current_domain}")
        return False
        
    except Exception as e:
        logger.error(f"更新 all_results.json 失败: {str(e)}")
        return False