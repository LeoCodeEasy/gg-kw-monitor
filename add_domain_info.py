"""
为 all_results.json 添加域名信息的临时脚本
"""
import json
from urllib.parse import urlparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_domain(url: str) -> str:
    """从URL中提取完整域名"""
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ''

def add_domain_info():
    """为所有记录添加域名信息"""
    try:
        # 读取现有数据
        logger.info("读取 all_results.json...")
        with open('all_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
            
        if not isinstance(results, list):
            logger.error("数据格式错误：不是列表格式")
            return
            
        # 记录原始数量
        original_count = len(results)
        logger.info(f"找到 {original_count} 条记录")
        
        # 添加域名信息
        for result in results:
            if not isinstance(result, dict):
                continue
                
            final_url = result.get('final_url', '')
            if final_url:
                domain = extract_domain(final_url)
                result['domain'] = domain
                logger.debug(f"URL: {final_url} -> Domain: {domain}")
        
        # 保存更新后的数据
        logger.info("保存更新后的数据...")
        with open('all_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        logger.info("处理完成！")
        logger.info(f"已为 {original_count} 条记录添加域名信息")
        
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}")
        raise

if __name__ == "__main__":
    add_domain_info() 