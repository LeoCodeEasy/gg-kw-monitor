import json
from datetime import datetime
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_results():
    """处理现有结果，对每个落地页的每个关键词只保留最新记录"""
    try:
        # 读取现有结果
        with open('all_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
            logger.info(f"读取到 {len(results)} 条记录")
        
        # 处理每个落地页的记录
        for result in results:
            if 'keyword_records' not in result:
                continue
                
            # 创建一个字典来存储每个关键词的最新记录
            keyword_dict = {}
            
            # 处理每个关键词记录
            for record in result.get('keyword_records', []):
                key = (record.get('keyword', ''), record.get('market', ''))
                timestamp = record.get('timestamp', '')
                
                # 只保留最新的记录
                if key not in keyword_dict or timestamp > keyword_dict[key].get('timestamp', ''):
                    keyword_dict[key] = record
            
            # 更新关键词记录列表
            result['keyword_records'] = list(keyword_dict.values())
            
            # 更新最新时间戳
            timestamps = [r.get('timestamp', '') for r in result['keyword_records']]
            if timestamps:
                result['timestamp'] = max(timestamps)
        
        # 按时间戳倒序排序
        results.sort(
            key=lambda x: max(
                (r.get('timestamp', '') for r in x.get('keyword_records', [])), 
                default=''
            ),
            reverse=True
        )
        
        # 保存处理后的结果
        with open('all_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        logger.info("处理完成，已保存更新后的结果")
        
        # 统计处理结果
        total_records = sum(len(r.get('keyword_records', [])) for r in results)
        logger.info(f"处理后共有 {len(results)} 个落地页，{total_records} 条关键词记录")
        
    except Exception as e:
        logger.error(f"处理结果时出错: {str(e)}", exc_info=True)

if __name__ == '__main__':
    process_results() 