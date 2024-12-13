"""
重命名截图文件，将带时间戳的文件名简化为纯域名形式
示例: 20241211_160531_baiducom.png -> baiducom.png
"""
import os
import re
from pathlib import Path
from datetime import datetime

def simplify_filename(filename: str) -> str:
    """
    简化文件名，提取域名部分
    """
    # 匹配模式：时间戳_域名.png
    pattern = r'\d{8}_\d{6}_(.+)\.png'
    match = re.match(pattern, filename)
    if match:
        return f"{match.group(1)}.png"
    return filename

def get_file_timestamp(file_path: Path) -> float:
    """获取文件的修改时间"""
    return os.path.getmtime(file_path)

def main():
    # 获取截图目录
    screenshots_dir = Path('screenshots')
    if not screenshots_dir.exists():
        print("截图目录不存在!")
        return

    # 收集所有需要重命名的文件
    files_to_rename = {}  # 新文件名 -> [(旧文件路径, 时间戳)]
    
    print("开始扫描文件...")
    
    # 遍历所有png文件
    for file_path in screenshots_dir.glob('*.png'):
        old_name = file_path.name
        new_name = simplify_filename(old_name)
        
        if old_name != new_name:  # 只处理需要重命名的文件
            timestamp = get_file_timestamp(file_path)
            
            if new_name not in files_to_rename:
                files_to_rename[new_name] = []
            files_to_rename[new_name].append((file_path, timestamp))
    
    if not files_to_rename:
        print("没有找到需要重命名的文件。")
        return
    
    print(f"\n找到 {len(files_to_rename)} 组需要处理的文件:")
    
    # 处理每组文件
    for new_name, file_list in files_to_rename.items():
        print(f"\n处理文件组: {new_name}")
        
        # 按时间戳排序，保留最新的
        file_list.sort(key=lambda x: x[1], reverse=True)
        
        # 打印所有文件及其时间
        for file_path, timestamp in file_list:
            time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            print(f"  {file_path.name} ({time_str})")
        
        # 获取最新的文件
        newest_file = file_list[0][0]
        
        # 重命名最新的文件
        new_path = newest_file.parent / new_name
        if new_path.exists():
            os.remove(new_path)  # 如果目标文件已存在，先删除
        newest_file.rename(new_path)
        print(f"  ✓ 保留最新文件并重命名为: {new_name}")
        
        # 删除其他旧文件
        for file_path, _ in file_list[1:]:
            file_path.unlink()
            print(f"  ✓ 删除旧文件: {file_path.name}")
    
    print("\n重命名完成! ✨")

if __name__ == "__main__":
    main() 