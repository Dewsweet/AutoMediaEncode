import re
import os
import shutil

class SubtitleProcessService:
    """
    字幕处理服务，主要用于去除ASS字幕的字体子集化前缀，还原原始字体名称。
    为了防止大文件（>100MB）卡顿UI，采用了流存取(Line-by-line)与正则一次性替换。
    """
    
    @staticmethod
    def process_file(input_path: str, output_path: str = None) -> bool:
        if not output_path:
            output_path = input_path
            
        temp_path = input_path + ".tmp"
        font_map = {}
        
        try:
            # 1. 快速扫描头部，建立哈希->原名映射表（避免全读入内存导致卡顿与爆内存）
            pattern1 = re.compile(r'^(.+?)\s+----\s+([A-Za-z0-9]{6,12})$')
            pattern2 = re.compile(r'^;\s*Font Subset:\s*([A-Za-z0-9]{6,12})\s*-\s*(.+)$')
            
            with open(input_path, 'r', encoding='utf-8-sig') as f:
                for line_num, line in enumerate(f):
                    # 假定字体表通常在文件头部（比如 Aegisub 属性区下方），扫到 [Events] 或者 1000 行后可不再强制找
                    if line.startswith("[Events]"):
                        break
                    
                    m1 = pattern1.match(line)
                    if m1:
                        font_map[m1.group(2)] = m1.group(1).strip()
                        continue
                    m2 = pattern2.match(line)
                    if m2:
                        font_map[m2.group(1)] = m2.group(2).strip()

            if not font_map:
                return True
                
            # 建立正则引擎，一次扫描同行内的多处子集化哈希提升性能
            keys_sorted = sorted(font_map.keys(), key=len, reverse=True)
            pattern_str = "|".join(map(re.escape, keys_sorted))
            replace_pattern = re.compile(pattern_str)
            
            def replacer(match):
                return font_map[match.group(0)]

            # 2. 使用逐行读取流写入临时文件 (IO密集自动释放GIL确保界面流畅)
            in_assfonts_section = False
            with open(input_path, 'r', encoding='utf-8-sig') as fin, \
                 open(temp_path, 'w', encoding='utf-8-sig') as fout:
                 
                for line in fin:
                    # 跳过 [Assfonts Rename Info] 块
                    if line.startswith("[Assfonts Rename Info]"):
                        in_assfonts_section = True
                        continue
                    if in_assfonts_section:
                        if line.strip() == "" or "----" in line:
                            continue
                        else:
                            in_assfonts_section = False
                            continue
                            
                    # 跳过注释行
                    if line.startswith("; Font Subset:"):
                        continue
                    
                    # 匹配并替换，降低CPU损耗
                    if replace_pattern.search(line):
                        line = replace_pattern.sub(replacer, line)
                        
                    fout.write(line)

            # 3. 替换完成，覆盖原文件
            shutil.move(temp_path, output_path)
            return True
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"Subtitle desubsetting exception: {e}")
            return False
