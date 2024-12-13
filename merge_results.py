"""
结果合并模块：处理所有结果文件的合并
"""
import json
import glob
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from src.core.results.deduplication import deduplicate_results

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_results(results, market):
    """存监控结果到文件"""
    if not results:
        return []
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    current_time = datetime.now().isoformat()
    
    # 确保results目录存在
    results_dir = 'results'
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    # 创建文件名 - 只使用 in 市场
    filename = os.path.join(results_dir, f'monitoring_results_in_{timestamp}.json')
    
    try:
        # 读取现有的结果
        try:
            with open('all_results.json', 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_results = []
            
        # 创建一个以original_url为键的字典来存储现有结果
        results_dict = {}
        for result in existing_results:
            if result and isinstance(result, dict) and result.get('original_url'):
                key = result['original_url']  # 使用 original_url 作为键
                # 移除 landing_page 字段（如果存在）
                if 'landing_page' in result:
                    del result['landing_page']
                results_dict[key] = result
                
        # 合并新结果
        for new_result in results:
            if not new_result or not new_result.get('original_url'):
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
                    'market': 'in',  # 固定使用 'in'
                    'keyword': new_result.get('keyword_records', [{}])[0].get('keyword', ''),
                    'title': new_result.get('keyword_records', [{}])[0].get('title', '')
                }
                
                if 'keyword_records' not in existing:
                    existing['keyword_records'] = []
                existing['keyword_records'].append(keyword_record)
                
                # 更新其他字段，保持字段顺序
                existing.update({
                    'domain': new_result.get('domain', existing.get('domain', '')),
                    'original_url': new_result.get('original_url', existing.get('original_url', '')),
                    'final_url': new_result.get('final_url', existing.get('final_url', '')),
                    'screenshot_path': new_result.get('screenshot_path', existing.get('screenshot_path', '')),
                    'timestamp': current_time,
                    'keyword_records': existing['keyword_records']
                })
            else:
                # 添加新记录，按照指定顺序
                formatted_result = {
                    'domain': new_result.get('domain', ''),
                    'original_url': new_result.get('original_url', ''),
                    'final_url': new_result.get('final_url', ''),
                    'screenshot_path': new_result.get('screenshot_path', ''),
                    'timestamp': current_time,
                    'keyword_records': [{
                        'timestamp': current_time,
                        'market': 'in',  # 固定使用 'in'
                        'keyword': new_result.get('keyword_records', [{}])[0].get('keyword', ''),
                        'title': new_result.get('keyword_records', [{}])[0].get('title', '')
                    }]
                }
                results_dict[key] = formatted_result
        
        # 转换回列表并按时间戳排序
        final_results = list(results_dict.values())
        final_results.sort(
            key=lambda x: max((r.get('timestamp', '') for r in x.get('keyword_records', [])), default=''),
            reverse=True
        )
        
        # 保存结果
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        with open('all_results.json', 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
            
        return final_results
        
    except Exception as e:
        logging.getLogger(__name__).error(f"保存结果失败: {str(e)}")
        return []

def merge_results():
    """合并所有结果文件"""
    try:
        all_results = []
        
        # 首先读取已有的 all_results.json
        if os.path.exists('all_results.json'):
            logger.info("读取现有的 all_results.json...")
            try:
                with open('all_results.json', 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                    if isinstance(existing_results, list):
                        all_results.extend(existing_results)
                        logger.info(f"从 all_results.json 读取了 {len(existing_results)} 条记录")
            except Exception as e:
                logger.error(f"读取 all_results.json 失败: {str(e)}")
        
        # 获取所有新的结果文件
        results_files = glob.glob('monitoring_results_*.json')
        if results_files:
            logger.info(f"找到 {len(results_files)} 个新的结果文件需要合并")
            
            # 读取并合并所有新结果
            for file_path in results_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                        if isinstance(results, list):
                            all_results.extend(results)
                            logger.info(f"从 {file_path} 读取了 {len(results)} 条记录")
                        else:
                            logger.warning(f"文件格式错误 {file_path}: 不是列表格式")
                            
                except Exception as e:
                    logger.error(f"处理结果文件时出错 {file_path}: {str(e)}")
                    continue
        
        if not all_results:
            logger.info("没有���到需要处理的数据")
            return
            
        # 统计原始数据
        original_count = len(all_results)
        original_records = sum(len(r.get('keyword_records', [])) for r in all_results)
        logger.info(f"原始数据: {original_count} 个URL, {original_records} 条关键词记录")
        
        # # 备份原始的 all_results.json
        # if os.path.exists('all_results.json'):
        #     backup_file = f'all_results_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        #     with open(backup_file, 'w', encoding='utf-8') as f:
        #         json.dump(all_results, f, ensure_ascii=False, indent=2)
        #     logger.info(f"已创建备份文件: {backup_file}")
        
        # 使用去重模块处理结果
        logger.info("开始去重...")
        merged_results = deduplicate_results(all_results)
        
        # 统计去重结果
        deduped_count = len(merged_results)
        deduped_records = sum(len(r.get('keyword_records', [])) for r in merged_results)
        
        # 保存合并后的结果
        with open('all_results.json', 'w', encoding='utf-8') as f:
            json.dump(merged_results, f, ensure_ascii=False, indent=2)
            
        # 清理旧的结果文件
        if results_files:
            for file_path in results_files:
                try:
                    os.remove(file_path)
                    logger.info(f"已删除文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除结果文件失败 {file_path}: {str(e)}")
        
        # 输出统计信息
        logger.info("处理完成!")
        logger.info(f"URL数量: {original_count} -> {deduped_count} (减少 {original_count - deduped_count})")
        logger.info(f"关键词记录: {original_records} -> {deduped_records} (减少 {original_records - deduped_records})")
        
    except Exception as e:
        logger.error(f"合并结果时出错: {str(e)}")
        raise

if __name__ == "__main__":
    merge_results()