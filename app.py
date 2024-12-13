from flask import Flask, render_template, jsonify, request, send_from_directory
from google_monitor import GoogleAdMonitor
import json
import glob
import os
from datetime import datetime
import requests
from urllib.parse import urlencode, urljoin, urlparse
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from src.config import KeywordConfig
from src.core.results.deduplication import deduplicate_keyword_records, deduplicate_results, merge_and_deduplicate
from src.utils.screenshot import create_driver, wait_for_page_load, update_results_json, capture_screenshot, save_screenshot

app = Flask(__name__)

def normalize_url(url):
    """标准化 URL，去除 Google Ads 的点击参数"""
    if not url:
        return ''
    
    # 如果是 Google Ads 的点击链接
    if url.startswith('https://www.google.com') and '/aclk?' in url:
        # 只保留基本参数
        base_parts = []
        for param in url.split('&'):
            # 保留主要标识参数
            if param.startswith(('sa=', 'ai=')):
                base_parts.append(param)
        if base_parts:
            return 'https://www.google.com/aclk?' + '&'.join(base_parts)
    
    return url

def load_all_results():
    """加载所有监控结果"""
    try:
        with open('all_results.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading results: {str(e)}")
        return []

def save_results(new_results, market):
    """保存新的监控结果，避免重复"""
    all_results = load_all_results()
    
    # 处理新结果
    for result in new_results:
        # 获取最新的 keyword_records
        if 'keyword_records' in result and result['keyword_records']:
            latest_record = result['keyword_records'][-1]
            keyword = latest_record.get('keyword', '')
            title = latest_record.get('title', '')
        else:
            # 如果没有历史记录，则从当前结果中获取
            keyword = result.get('keyword', '') or result.get('search_term', '')
            title = result.get('ad_title', '') or result.get('title', '')
        
        # 只有当 keyword 和 title 都不为空时才添加记录
        if keyword and title:
            # 创建关键词记录
            keyword_record = {
                'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
                'market': market,
                'keyword': keyword,
                'title': title
            }
            
            # 添加关键词记录
            if 'keyword_records' not in result:
                result['keyword_records'] = []
            result['keyword_records'].append(keyword_record)
    
    # 使用去重模块处理结果
    merged_results = merge_and_deduplicate(all_results, new_results)
    deduped_results = deduplicate_results(merged_results)
    
    # 保存结果
    with open('all_results.json', 'w', encoding='utf-8') as f:
        json.dump(deduped_results, f, ensure_ascii=False, indent=2)
    
    return deduped_results

def get_screenshot_filename(url):
    """根据URL获取对应的截图文件名"""
    from urllib.parse import urlparse
    import glob
    import os
    
    domain = urlparse(url).netloc.replace('.', '')
    pattern = os.path.join('screenshots', f'*{domain}.png')
    matches = glob.glob(pattern)
    
    return os.path.basename(matches[0]) if matches else None

@app.route('/')
def index():
    """渲染主页"""
    try:
        keywords = KeywordConfig.load_keywords()
        return render_template('index.html', keywords=keywords)
    except Exception as e:
        return render_template('index.html', keywords=[], error=str(e))

@app.route('/latest')
def get_latest_results():
    """获取最新的监控结果"""
    results = load_all_results()
    # 更新每个结果的screenshot字段
    for result in results:
        if 'final_url' in result:
            screenshot = get_screenshot_filename(result['final_url'])
            if screenshot:
                result['screenshot'] = screenshot
    return jsonify(results)

@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    """获取完整的关键词配置"""
    try:
        keywords = KeywordConfig.load_all_keywords()
        return jsonify({'keywords': keywords})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords', methods=['POST'])
def save_keywords():
    """保存关键词配置"""
    try:
        keywords_data = request.json.get('keywords', {})
        if not isinstance(keywords_data, dict):
            return jsonify({'error': '无效的关键词配置格式'}), 400
            
        success = KeywordConfig.save_keywords(keywords_data)
        if not success:
            return jsonify({'error': '保存关键词失败'}), 500
            
        return jsonify({'message': '关键词保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords', methods=['PUT'])
def add_keyword():
    """添加新关键词"""
    try:
        data = request.json
        category = data.get('category', '').strip()
        keyword = data.get('keyword', '').strip()
        enabled = data.get('enabled', True)
        
        if not category or not keyword:
            return jsonify({'error': '分类和关键词不能为空'}), 400
            
        success = KeywordConfig.add_keyword(category, keyword, enabled)
        if not success:
            return jsonify({'error': '添加关键词失败'}), 500
            
        return jsonify({'message': '关键词添加成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/<category>/<keyword>', methods=['DELETE'])
def remove_keyword(category, keyword):
    """移除关键词"""
    try:
        success = KeywordConfig.remove_keyword(category, keyword)
        if not success:
            return jsonify({'error': '移除关键词失败'}), 500
            
        return jsonify({'message': '关键词移除成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/keywords/toggle/<category>/<keyword>', methods=['POST'])
def toggle_keyword(category, keyword):
    """切换关键词启用状态"""
    try:
        success = KeywordConfig.toggle_keyword(category, keyword)
        if not success:
            return jsonify({'error': '切换关键词状态失败'}), 500
            
        return jsonify({'message': '关键词状态已更新'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crawl', methods=['POST'])
def crawl():
    """爬取指定关键词的广告"""
    try:
        # 直接使用已启用的关键词
        keywords = KeywordConfig.load_keywords()  # 这个方法现在只返回启用的关键词
        if not keywords:
            return jsonify({'error': '没有启用的关键词'}), 400
            
        # 备份现有结果
        try:
            with open('all_results.json', 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        except:
            existing_results = []
            
        # 创建临时文件来存储新结果
        if os.path.exists('temp_results.json'):
            os.remove('temp_results.json')
            
        # 直接调用google_monitor.py的main函数，但使用临时文件
        from google_monitor import main
        main(output_file='temp_results.json')
        
        # 读取新爬取的结果
        try:
            with open('temp_results.json', 'r', encoding='utf-8') as f:
                new_results = json.load(f)
                
            # 使用去重函数处理结果
            from src.core.results.deduplication import merge_and_deduplicate
            merged_results = merge_and_deduplicate(existing_results, new_results)
            
            # 保存去重后的结果
            with open('all_results.json', 'w', encoding='utf-8') as f:
                json.dump(merged_results, f, ensure_ascii=False, indent=2)
                
            # 清理临时文件
            if os.path.exists('temp_results.json'):
                os.remove('temp_results.json')
                
            return jsonify({
                'message': '爬取完成',
                'results': merged_results
            })
        except FileNotFoundError:
            # 如果文件不存在但有备份，恢复备份
            if existing_results:
                with open('all_results.json', 'w', encoding='utf-8') as f:
                    json.dump(existing_results, f, ensure_ascii=False, indent=2)
                return jsonify({
                    'message': '爬取失败，已恢复备份',
                    'results': existing_results
                })
            return jsonify({'error': '爬取失败且无法恢复备份'}), 500
    except Exception as e:
        return jsonify({'error': f'爬取失败: {str(e)}'}), 500

@app.route('/expand_keywords', methods=['POST'])
def expand_keywords():
    """扩展关键词"""
    data = request.json
    category = data.get('category')
    
    if not category:
        return jsonify({'error': 'Missing category'}), 400
        
    try:
        if category == 'all':
            keywords = get_all_keywords()
        else:
            keywords = get_keywords_by_category(category)
            
        return jsonify(keywords)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/proxy')
def proxy():
    """代理请求以避免跨域和问限制"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
        
    try:
        # 添加更多的请求头，模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Cache-Control': 'max-age=0',
        }
        
        # 发送请求
        response = requests.get(
            url, 
            headers=headers, 
            timeout=15,
            allow_redirects=True,
            verify=False  # 忽略SSL证书验证
        )
        
        # 获取响应内容类型
        content_type = response.headers.get('Content-Type', 'text/html')
        
        # 设置响应头
        response_headers = {
            'Content-Type': content_type,
            'Access-Control-Allow-Origin': '*',  # 允许跨域访问
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'X-Frame-Options': 'SAMEORIGIN',  # 允许在同源iframe中显示
        }
        
        # 如果是HTML内容，处理相对路径
        if 'text/html' in content_type.lower():
            content = response.text
            # 在这里可以添加HTML理逻辑
            
            return content, response.status_code, response_headers
        else:
            # 对于其他类型的内容（图片、CSS、JS等）直接返回
            return response.content, response.status_code, response_headers
            
    except requests.Timeout:
        return jsonify({'error': '请求超时，请稍后重试'}), 504
    except requests.ConnectionError:
        return jsonify({'error': '无法连接到目标服务器'}), 502
    except requests.RequestException as e:
        return jsonify({'error': f'请求错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

@app.route('/preview')
def preview():
    """预览广告页面"""
    url = request.args.get('url')
    if not url:
        return "Missing URL parameter", 400
        
    try:
        # 添加请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 通过后端请求目标页面
        response = requests.get(url, headers=headers, timeout=10)
        
        # 设置响应头
        response_headers = {
            'Content-Type': response.headers.get('Content-Type', 'text/html'),
            'X-Frame-Options': 'SAMEORIGIN'  # 允许在同源iframe中显示
        }
        
        return response.content, response.status_code, response_headers
    except Exception as e:
        return f"Error loading preview: {str(e)}", 500

@app.route('/mobile_preview')
def mobile_preview():
    """移动端预览页面"""
    url = request.args.get('url')
    if not url:
        return "Missing URL parameter", 400
    return render_template('mobile_preview.html', url=url)

@app.route('/mobile_proxy')
def mobile_proxy():
    """移动端代理请求"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
        
    try:
        # 添加移动端的请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        }
        
        # 发送请求
        session = requests.Session()
        response = session.get(
            url, 
            headers=headers, 
            timeout=15,
            allow_redirects=True,
            verify=False
        )
        
        # 获取响应内容类型
        content_type = response.headers.get('Content-Type', 'text/html')
        
        # 设置响应头，移除限制性的安全头部
        response_headers = {
            'Content-Type': content_type,
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Credentials': 'true',
            'X-Frame-Options': 'ALLOWALL',  # 允许在任何页面中嵌入
            'Content-Security-Policy': "frame-ancestors *; default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;",  # 允许所有来源
        }
        
        # 如果是HTML内容，处理相对路径和安全策略
        if 'text/html' in content_type.lower():
            content = response.text
            
            # 移除原有的安全头部meta标签
            content = re.sub(r'<meta[^>]*http-equiv=["\']Content-Security-Policy["\'][^>]*>', '', content)
            content = re.sub(r'<meta[^>]*http-equiv=["\']X-Frame-Options["\'][^>]*>', '', content)
            
            # 注入新的meta标签
            meta_tags = '''
                <meta http-equiv="Content-Security-Policy" content="frame-ancestors *; default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;">
                <meta http-equiv="X-Frame-Options" content="ALLOWALL">
                <base href="{}">
            '''.format(response.url)
            
            # 注入meta标签到head
            if '<head>' in content:
                content = content.replace('<head>', f'<head>{meta_tags}')
            else:
                content = f'<head>{meta_tags}</head>{content}'
            
            # 注入脚本以禁用框架检测
            script = '''
                <script>
                    // 禁用框架检测
                    if (window.top !== window.self) {
                        try {
                            // 阻止框架检测
                            Object.defineProperty(window, 'top', {
                                get: function() { return window.self; }
                            });
                            Object.defineProperty(window, 'parent', {
                                get: function() { return window.self; }
                            });
                            Object.defineProperty(window, 'frameElement', {
                                get: function() { return null; }
                            });
                        } catch(e) {}
                    }
                </script>
            '''
            
            # 在body开始标签后注入脚本
            if '<body>' in content:
                content = content.replace('<body>', f'<body>{script}')
            else:
                content = f'{script}{content}'
            
            return content, response.status_code, response_headers
        else:
            # 对于非HTML内容，直接返回
            return response.content, response.status_code, response_headers
            
    except requests.Timeout:
        return jsonify({'error': '请求超时，请稍后重试'}), 504
    except requests.ConnectionError:
        return jsonify({'error': '无法连接到目标服务器'}), 502
    except requests.RequestException as e:
        return jsonify({'error': f'请求错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    finally:
        if 'session' in locals():
            session.close()

@app.route('/resource_proxy')
def resource_proxy():
    """代理资源请求"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
        
    try:
        # 添加请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': urlparse(url).scheme + '://' + urlparse(url).netloc,
            'Origin': urlparse(url).scheme + '://' + urlparse(url).netloc,
        }
        
        session = requests.Session()
        response = session.get(
            url, 
            headers=headers, 
            timeout=15,
            verify=False,
            stream=True
        )
        
        # 设置响应头
        response_headers = {
            'Content-Type': response.headers.get('Content-Type', 'application/octet-stream'),
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-Requested-With',
            'Access-Control-Allow-Credentials': 'true',
            'Cache-Control': 'public, max-age=31536000',
        }
        
        return response.content, response.status_code, response_headers
        
    except Exception as e:
        return jsonify({'error': f'资源加载失败: {str(e)}'}), 500
    finally:
        if 'session' in locals():
            session.close()

@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    return send_from_directory('screenshots', filename)

@app.route('/delete_record', methods=['POST'])
def delete_record():
    try:
        data = request.get_json()
        if not data:
            print("未收到有效的 JSON 数据")
            return jsonify({
                'status': 'error',
                'message': '未收到有效的请求数据'
            }), 400
            
        final_url = data.get('final_url')
        print(f"收到删除请求，final_url: {final_url}")
        
        if not final_url:
            print("缺少 final_url 参数")
            return jsonify({
                'status': 'error',
                'message': '缺少 final_url 参数'
            }), 400
            
        # 读取现有数据
        try:
            with open('all_results.json', 'r', encoding='utf-8') as f:
                results = json.load(f)
                print(f"成功读取数据文件，当前记录数: {len(results)}")
                
                # 打印所有的 final_url，帮助调试
                print("\n当前所有的 final_url:")
                for r in results:
                    print(f"- {r.get('final_url')}")
                print("\n")
                
        except FileNotFoundError:
            print("数据文件不存在")
            return jsonify({
                'status': 'error',
                'message': '数据文件不存在'
            }), 404
            
        # 在删除前记录当前数量
        original_count = len(results)
        print(f"当前记录数: {original_count}")
        
        # 查找并删除记录
        new_results = []
        found = False
        for r in results:
            current_url = r.get('final_url')
            if current_url == final_url:
                found = True
                print(f"找到要删除的记录: {final_url}")
                continue
            new_results.append(r)
            
        # 检查是否有记录被删除
        if not found:
            print(f"未找到要删除的记录: {final_url}")
            print("URL 比对结果:")
            for r in results:
                print(f"数据库中: {r.get('final_url')}")
                print(f"请求URL: {final_url}")
                print(f"是否匹配: {r.get('final_url') == final_url}\n")
            return jsonify({
                'status': 'error',
                'message': f'未找到要删除的记录: {final_url}'
            }), 404
            
        # 保存更新后的数据
        try:
            with open('all_results.json', 'w', encoding='utf-8') as f:
                json.dump(new_results, f, ensure_ascii=False, indent=2)
            print(f"成功保存更新后的数据，剩余记录数: {len(new_results)}")
        except Exception as e:
            print(f"保存数据时出错: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'保存数据时出错: {str(e)}'
            }), 500
            
        return jsonify({
            'status': 'success',
            'message': '记录已删除',
            'deleted_url': final_url,
            'remaining_count': len(new_results)
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"删除记录时出错:\n{error_details}")
        return jsonify({
            'status': 'error',
            'message': f'删除失败: {str(e)}',
            'details': error_details
        }), 500

@app.route('/capture-landing-page', methods=['POST'])
def capture_landing_page():
    """捕获落地页截图"""
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # 使用统一的截图模块
        success, screenshot_filename, error = capture_screenshot(
            url=url,
            mobile=True,  # 使用移动端模式
            update_results=True  # 更新 all_results.json
        )

        if not success:
            return jsonify({'error': error or '截图失败'}), 500

        return jsonify({
            'success': True,
            'screenshot_path': screenshot_filename
        })

    except Exception as e:
        print(f"Error capturing landing page: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-thumbnail', methods=['POST'])
def generate_thumbnail():
    """生成网页缩略图"""
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        print(f"开始生成缩略图: {url}")  # 添加日志

        # 使用统一的截图模块
        success, screenshot_filename, error = capture_screenshot(
            url=url,
            mobile=True,  # 使用移动端模式
            update_results=True,  # 更新 all_results.json
            force_refresh=True  # 强制刷新截图
        )

        if not success:
            print(f"生成缩略图失败: {error}")  # 添加失败日志
            return jsonify({'error': error or '截图失败'}), 500

        print(f"缩略图生成成功: {screenshot_filename}")  # 添加成功日志
        return jsonify({
            'success': True,
            'screenshot_path': screenshot_filename
        })

    except Exception as e:
        error_msg = f"生成缩略图时发生错误: {str(e)}"
        print(error_msg)  # 添加异常日志
        return jsonify({'error': error_msg}), 500

@app.route('/api/keywords/file', methods=['GET', 'POST'])
def handle_keywords():
    keywords_file = os.path.join(app.root_path, 'resources', 'keywords.json')
    
    if request.method == 'GET':
        try:
            with open(keywords_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except FileNotFoundError:
            return jsonify({"error": "Keywords file not found"}), 404
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            with open(keywords_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"message": "Keywords saved successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/resources/keywords.json', methods=['GET', 'POST'])
def get_keywords_json():
    if request.method == 'GET':
        try:
            with open('resources/keywords.json', 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        except FileNotFoundError:
            return jsonify({}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:  # POST
        try:
            data = request.get_json()
            with open('resources/keywords.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.after_request
def after_request(response):
    """添加跨域支持"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

@app.route('/merge_results', methods=['POST'])
def merge_results():
    try:
        # 读取现有的 all_results.json
        with open('all_results.json', 'r', encoding='utf-8') as f:
            all_results = json.load(f)
            
        # 获取 results 目录下的所有 json 文件
        results_dir = 'results'
        json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
        
        for json_file in json_files:
            with open(os.path.join(results_dir, json_file), 'r', encoding='utf-8') as f:
                new_results = json.load(f)
                
            # 合并数据时需要确保字段名一致
            for result in new_results:
                # 检查是否已存在相同的 landing_page
                existing_result = next((r for r in all_results if r['landing_page'] == result['landing_page']), None)
                
                if existing_result:
                    # 更新现有记录
                    if 'screenshot_path' in result:  # 这里需要确保使用 screenshot_path
                        existing_result['screenshot_path'] = result['screenshot_path']
                    # 更新其他字段...
                else:
                    # 添加新记录
                    all_results.append(result)
                    
        # 保存更新后的数据
        with open('all_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
            
        return jsonify({'status': 'success', 'message': '数据合并成功'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # 设置服务器配置
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True  # 格式化JSON输出
    app.config['SCREENSHOT_FOLDER'] = 'screenshots'  # 截图文件夹
    
    # 确保截图目录存在
    os.makedirs(app.config['SCREENSHOT_FOLDER'], exist_ok=True)
    
    # 启动服务器
    app.run(debug=True, port=9090, host='0.0.0.0')
