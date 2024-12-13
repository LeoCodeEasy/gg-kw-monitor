"""
清理重复数据脚本：处理现有的 all_results.json 文件
"""
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def deduplicate_keyword_records(records):
    """去除重复的关键词记录,只保留每个关键词的最新记录"""
    if not records:
        return []
    
    # 用字典记录每个关键词的最新记录
    unique_records = {}
    for record in records:
        keyword = record.get('keyword', '')
        # 跳过空的关键词
        if not keyword:
            continue
        # 如果是新关键词或比现有记录更新,则更新
        if keyword not in unique_records or record.get('timestamp', '') > unique_records[keyword].get('timestamp', ''):
            unique_records[keyword] = record
    
    # 返回去重后的记录列表,按时间戳降序排序
    return sorted(
        unique_records.values(),
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )

def clean_duplicates():
    """清理 all_results.json 中的重复数据"""
    try:
        # 读取现有数据
        logger.info("开始读取现有数据...")
        with open('all_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        original_count = len(results)
        original_records = sum(len(r.get('keyword_records', [])) for r in results)
        logger.info(f"原始数据: {original_count} 个URL, {original_records} 条关键词记录")
        
        # 备份原始文件
        backup_file = f'all_results_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"已创建备份文件: {backup_file}")
        
        # 对每个URL的关键词记录进行去重
        logger.info("开始去重...")
        for result in results:
            result['keyword_records'] = deduplicate_keyword_records(result.get('keyword_records', []))
            # 如果有关键词记录，更新时间戳为最新记录的时间戳
            if result.get('keyword_records'):
                result['timestamp'] = result['keyword_records'][0]['timestamp']
        
        # 移除空记录
        results = [r for r in results if r.get('keyword_records')]
        
        # 统计去重结果
        deduped_count = len(results)
        deduped_records = sum(len(r.get('keyword_records', [])) for r in results)
        
        # 保存去重后的结果
        with open('all_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 输出统计信息
        logger.info("去重完成!")
        logger.info(f"URL数量: {original_count} -> {deduped_count} (减少 {original_count - deduped_count})")
        logger.info(f"关键词记录: {original_records} -> {deduped_records} (减少 {original_records - deduped_records})")
        logger.info(f"原始文件已备份为: {backup_file}")
        
    except Exception as e:
        logger.error(f"去重过程出错: {str(e)}")
        raise

if __name__ == "__main__":
    clean_duplicates()