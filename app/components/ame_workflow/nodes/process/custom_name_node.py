import re
import shutil
from pathlib import Path
from datetime import datetime
import shutil
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CustomTextWidget, SwitchButtonWidget, CheckBoxWidget
from app.common.logger import logger

class CustomNameNode(AMENodeBase):
    NODE_NAME = '自定义文件名'
    DESCRIPTION = '重命名文件。{input_name} 替换为输入文件名(不含扩展名)，{datetime} 替换为当前时间'
    CATEGORY = '输出'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('input', P['any'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'custom_name'

    def _setup_widgets(self):
        placeholders = {
            '输入文件名': '{input_name}',
            '日期时间': '{datetime}',
            '序列化': '{index:00}',
            }
        self.add_custom_widget(CustomTextWidget(self.view, 'custom_name', placeholder=placeholders))
        self.add_custom_widget(CheckBoxWidget(self.view, 'copy2_temp', '复制文件到缓存目录'))

    def execute(self, inputs, temp_dir):
        logger.info('\n' * 2 + '=' * 40 + f' [{self.NODE_NAME}] ' + '=' * 40)
        
        raw_files = inputs.get('input', [])
        if not raw_files:
            return None
            
        files = sorted([Path(f) for f in raw_files])
        
        custom_text = self.property('custom_name', '')
        # 获取用户是否开启了复制选项
        is_copy = self.property('copy2_temp', False)

        if not custom_text:
            # 如果没有输入重命名规则，但选择了复制，也应该执行复制逻辑
            if not is_copy:
                return {'output': [str(f) for f in files]}
            else:
                custom_text = '{input_name}{ext}' # 赋予默认的占位符以便走后续复用逻辑

        now_text = datetime.now().strftime('%Y%m%d_%H%M%S')
        result = []

        for i, src in enumerate(files, start=1):
            name = custom_text
            
            # 1. 替换基础占位符
            name = name.replace('{input_name}', src.stem)
            name = name.replace('{datetime}', now_text)
            
            # 2. 动态解析 {index:00} 系列占位符
            def index_replacer(match):
                zeros = match.group(1)
                width = len(zeros) if zeros else 1
                return f"{i:0{width}d}"
            name = re.sub(r'\{index:?(0*)\}', index_replacer, name)

            # 3. 处理扩展名
            if '{ext}' in name:
                name = name.replace('{ext}', src.suffix.lstrip('.'))
            else:
                name = name + src.suffix

            # 4. 核心逻辑：确定目标所在的文件夹
            target_folder = Path(temp_dir) if is_copy else src.parent
            dst = target_folder / name

            # 5. 防冲突机制：如果在目标文件夹下已存在同名文件，自动追加编号
            original_dst = dst
            conflict_counter = 1
            while dst.exists() and dst.resolve() != src.resolve():
                dst = target_folder / f"{original_dst.stem}_{conflict_counter}{original_dst.suffix}"
                conflict_counter += 1

            # 6. 最终执行 IO 操作（复制 或 重命名移动）
            # 使用 resolve() 对比，防止覆盖自己，也完美兼容 Windows 大小写不敏感的问题
            if src.resolve() != dst.resolve():
                try:
                    if is_copy:
                        shutil.copy2(str(src), str(dst))
                        # logger.info(f'[{self.NODE_NAME}] 复制到缓存: {src.name} -> {dst.name}')
                    else:
                        shutil.move(str(src), str(dst))
                        # logger.info(f'[{self.NODE_NAME}] 重命名: {src.name} -> {dst.name}')
                except Exception as e:
                    action_name = "复制" if is_copy else "重命名"
                    logger.error(f'[{self.NODE_NAME}] {action_name}失败 {src.name}: {e}')
                    result.append(str(src))
                    continue
            
            result.append(str(dst))
            
        return {'output': result}
