import shutil
from pathlib import Path
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import DirBrowseWidget, SwitchButtonWidget
from app.common.logger import logger

class OutputNode(AMENodeBase):
    NODE_NAME = '输出文件'
    DESCRIPTION = '最终输出文件路径。可开启运行后清理缓存'
    CATEGORY = '输出'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('input', P['any'])]
    OUTPUTS = []
    MENU_KEY = 'output'

    def _setup_widgets(self):
        self.add_custom_widget(DirBrowseWidget(self.view, 'output', '选择输出目录'))
        self.add_custom_widget(SwitchButtonWidget(self.view, 'clean_temp', '缓存清理'))

    def execute(self, inputs, temp_dir):
        logger.info('\n' * 2 + '=' * 40 + ' [OutputNode] ' + '=' * 40)

        src_files = inputs.get('input', [])
        if not src_files:
            return None
        output_dir = self.get_property('output')
        if not output_dir:
            return None

        for f in src_files:
            src_path = Path(f)
            dst_path = Path(output_dir) / src_path.name
            if dst_path.exists():
                stem = src_path.stem
                suffix = src_path.suffix
                counter = 1
                while dst_path.exists():
                    dst_path = Path(output_dir) / f"{stem} ({counter}){suffix}"
                    counter += 1
            try:
                shutil.move(str(src_path), str(dst_path))
                logger.info(f'[OutputNode] 移动文件: {src_path} -> {dst_path}')
            except Exception as e:
                logger.error(f'[OutputNode] 移动文件失败: {e}')
                continue

        logger.info(f'[OutputNode] 完成输出！')

        if self.property('clean_temp', False):
            if Path(temp_dir).is_dir():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f'[OutputNode] 已清理缓存: {temp_dir}')
                except Exception as e:
                    logger.error(f'[OutputNode] 清理缓存失败: {e}')

        return None
