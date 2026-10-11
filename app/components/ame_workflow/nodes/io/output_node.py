from PySide6.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
import shutil
from pathlib import Path
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import DirBrowseWidget, SwitchButtonWidget
from app.common.logger import logger
from app.services.ame_workflow.process_runner import check_cancelled, ProcessCancelled

class OutputNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", '输出文件')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", '最终输出文件路径。可开启运行后清理缓存')
    CATEGORY = '输出'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('file', P['any'])]
    OUTPUTS = []
    MENU_KEY = 'output'

    def _setup_widgets(self):
        self.add_custom_widget(DirBrowseWidget(self.view, 'output', QCoreApplication.translate('AMENodes', '选择输出目录')))
        self.add_custom_widget(SwitchButtonWidget(self.view, 'clean_temp', QCoreApplication.translate('AMENodes', '运行后清理缓存文件夹')))

    def execute(self, inputs, temp_dir):
        logger.info('\n' * 2 + '=' * 40 + ' [OutputNode] ' + '=' * 40)

        src_files = inputs.get('file', [])
        if not src_files:
            self._last_error = QCoreApplication.translate('AMENodes', '输出节点未接收到文件，请连接上游节点')
            return None
        output_dir = self.get_property('output')
        if not output_dir or not Path(output_dir).is_dir():
            self._last_error = QCoreApplication.translate('AMENodes', '请选择有效的输出目录')
            return None

        try:
            sources = [Path(f) for f in src_files]
            for source in sources:
                if not source.is_file() or source.stat().st_size == 0:
                    raise ValueError(QCoreApplication.translate('AMENodes', '输出源文件不存在或为空: {path}').format(path=source))
            temp_path = None
            if self.property('clean_temp', False):
                if not temp_dir:
                    raise ValueError(QCoreApplication.translate('AMENodes', '未设置有效的缓存目录'))
                temp_path = Path(temp_dir).absolute()
                # 只允许清理工作区中的真实 temp 目录，最终输出不能位于待清理目录内。
                if (temp_path.name.lower() != 'temp'
                        or temp_path.resolve() != temp_path.parent.resolve() / temp_path.name
                        or Path(output_dir).resolve().is_relative_to(temp_path.resolve())):
                    raise ValueError(QCoreApplication.translate('AMENodes', '缓存清理路径无效，或输出目录位于缓存目录内'))

            for src_path in sources:
                check_cancelled()
                source_size = src_path.stat().st_size
                dst_path = Path(output_dir) / src_path.name
                stem, suffix = src_path.stem, src_path.suffix
                counter = 1
                while dst_path.exists() or dst_path.is_symlink():
                    dst_path = Path(output_dir) / f"{stem} ({counter}){suffix}"
                    counter += 1
                shutil.move(str(src_path), str(dst_path))
                if not dst_path.is_file() or dst_path.stat().st_size != source_size:
                    raise ValueError(QCoreApplication.translate('AMENodes', '输出文件写入不完整: {path}').format(path=dst_path))
                logger.info(f'[OutputNode] 移动文件: {src_path} -> {dst_path}')
            check_cancelled()
            if temp_path is not None and temp_path.is_dir():
                shutil.rmtree(temp_path)
                logger.info(f'[OutputNode] 已清理缓存: {temp_path}')
        except ProcessCancelled:
            raise
        except Exception as error:
            self._last_error = str(error)
            logger.error(f'[OutputNode] 输出失败: {error}')
            return None
        logger.info('[OutputNode] 完成输出！')
        return {}
