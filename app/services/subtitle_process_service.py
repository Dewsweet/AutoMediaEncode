import re

class SubtitleProcessService:
    """
    字幕处理服务，主要用于去除ASS字幕的字体子集化前缀，还原原始字体名称。
    """
    
    @staticmethod
    def desubset_ass_content(content: str) -> str:
        """
        核心处理逻辑：从ASS文本中提取映射表并替换乱码哈希为原字体名。
        """
        font_map = {}
        
        # 模式1: [Assfonts Rename Info] 生成的格式
        # 例如: Dream Han Sans TC W20 ---- NHPJWNLL
        pattern1 = re.compile(r'^(.+?)\s+----\s+([A-Za-z0-9]{6,12})$', re.MULTILINE)
        for match in pattern1.finditer(content):
            original, hash_name = match.groups()
            font_map[hash_name] = original.strip()

        # 模式2: Aegisub 等挂载插件的注释格式
        # 例如: ; Font Subset: YNKIS8GG - 黑体
        pattern2 = re.compile(r'^;\s*Font Subset:\s*([A-Za-z0-9]{6,12})\s*-\s*(.+)$', re.MULTILINE)
        for match in pattern2.finditer(content):
            hash_name, original = match.groups()
            font_map[hash_name] = original.strip()

        if not font_map:
            return content
        
        content = re.sub(r'\[Assfonts Rename Info\]\r?\n(?:.+?\s+----\s+[A-Za-z0-9]{6,12}\r?\n)*\r?\n?', '', content)
        content = re.sub(r'^;\s*Font Subset:\s*[A-Za-z0-9]{6,12}\s*-\s*.+\r?\n?', '', content, flags=re.MULTILINE)
        new_content = content
        for hash_name, original in font_map.items():
            new_content = new_content.replace(hash_name, original)
        
        return new_content

    @staticmethod
    def process_file(input_path: str, output_path: str = None) -> bool:
        """
        处理实体文件，如果不提供输出路径，则默认覆盖原文件。
        """
        if not output_path:
            output_path = input_path
        
        try:
            with open(input_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            new_content = SubtitleProcessService.desubset_ass_content(content)
            
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                f.write(new_content)
                
            return True
        except Exception as e:
            return False
