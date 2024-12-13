"""
更新 all_results.json 中的截图路径，移除时间戳前缀
示例: 20241211_160531_baiducom.png -> baiducom.png
"""
import json
import re
from pathlib import Path

def simplify_filename(filename: str) -> str:
    """
    简化文件名，移除时间戳前缀
    """
    if not filename:
        return filename
        
    # 匹配模式：时间戳_域名.png
    pattern = r'\d{8}_\d{6}_(.+\.png)'
    match = re.match(pattern, filename)
    if match:
        return match.group(1)
    return filename

def update_json_paths():
    """更新 all_results.json 中的截图路径"""
    json_path = Path('all_results.json')
    if not json_path.exists():
        print("all_results.json 文件不存在!")
        return
    
    print("开始处理 all_results.json...")
    
    # 读取 JSON 文件
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("JSON 文件格式错误!")
        return
    except Exception as e:
        print(f"读取文件失败: {str(e)}")
        return
    
    # 记录修改数量
    changes = 0
    
    # 更新每个记录的截图路径
    for item in data:
        if 'screenshot_path' in item:
            old_path = item['screenshot_path']
            new_path = simplify_filename(old_path)
            
            if old_path != new_path:
                item['screenshot_path'] = new_path
                changes += 1
                print(f"更新路径: {old_path} -> {new_path}")
    
    if changes == 0:
        print("没有需要更新的路径。")
        return
    
    # 保存更新后的文件
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n成功更新了 {changes} 个路径! ✨")
    except Exception as e:
        print(f"保存文件失败: {str(e)}")

if __name__ == "__main__":
    update_json_paths() 