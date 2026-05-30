from pathlib import Path
from datetime import datetime
import shutil
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CustomNameWidget
from app.common.logger import logger

class CustomNameNode(AMENodeBase):
    NODE_NAME = '自定义文件名'
    DESCRIPTION = '重命名文件。{input_name} 替换为输入文件名(不含扩展名)，{datetime} 替换为当前时间'
    CATEGORY = '输出'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('input', P['any'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'custom_name'

    def _setup_widgets(self):
        self.add_custom_widget(CustomNameWidget(self.view, 'custom_name'))

    def execute(self, inputs, temp_dir):
        logger.info('\n' * 2 + '=' * 40 + f' [{self.NODE_NAME}] ' + '=' * 40)
        files = inputs.get('input', [])
        if not files:
            return None
        
        custom_text = self.property('custom_name', '')
        if not custom_text:
            return {'output': files}

        result = []
        for f in files:
            src = Path(f)
            now_text = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = (custom_text
                .replace('{input_name}', src.stem)
                .replace('{datetime}', now_text))
            # 如果用户没有在 custom_text 中指定扩展名，则默认保留原文件的扩展名
            if not any(name.endswith(e) for e in ['.mkv','.mp4','.m4a','.mka','.mks','.wav','.flac','.aac','.opus','.ac3','.ass','.srt','.h264','.h265']): 
                name = name + src.suffix
            dst = src.parent / name
            if src != dst:
                shutil.move(str(src), str(dst))
                logger.info(f'[CustomName] 重命名: {src} -> {dst}')
            result.append(str(dst))
        return {'output': result}
