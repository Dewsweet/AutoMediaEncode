from PySide6.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
import subprocess
from pathlib import Path
from app.services.ame_workflow.process_runner import run_process
from .._base import AMENodeBase, C, P
from .._widgets import NodeComboBoxWidget
from app.services.tool_service import ToolService
from app.common.logger import logger
from app.services.error_service import ErrorService

class MuxerFFmpegNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", '封装 (FFmpeg)')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", 'FFmpeg 封装 MP4/MOV，接收单视频单音频')
    CATEGORY = '封装'; CATEGORY_COLOR = C['Green']
    INPUTS = [('video', P['video']), ('audio', P['audio'])]
    OUTPUTS = [('file', P['any'])]
    MENU_KEY = 'muxer_ffmpeg'

    def _setup_widgets(self):
        items = ['MP4', 'MOV', 'MKV', 'AVI', 'FLV', 'WebM']
        self.add_custom_widget(NodeComboBoxWidget(self.view, 'container', items))

    def execute(self, inputs, temp_dir):
        logger.info('\n' *2 + '=' * 30 + f' 执行节点: {self.NODE_NAME} ' + '=' * 30)
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff:
            logger.error(f'[MuxerFFmpeg] 未找到 ffmpeg 可执行文件')
            return None
        vf = inputs.get('video') or []
        af = inputs.get('audio') or []
        if not vf and not af:
            self._last_error = QCoreApplication.translate('AMENodes', '封装节点未接收到视频或音频')
            return None
        container = self.property('container', 'mp4').lower()
        dst = Path(temp_dir) / f'muxed_{self.id}.{container}'
        cmd = [ff]
        for s in vf:
            cmd.extend(['-i', s])
        for s in af:
            cmd.extend(['-i', s])
        si = 0
        for _ in vf:
            cmd.extend(['-map', str(si)]); si += 1
        for _ in af:
            cmd.extend(['-map', str(si)]); si += 1
        cmd.extend(['-c', 'copy', dst, '-y'])
        if dst.exists():
            dst.unlink()
        result = run_process(cmd, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, timeout=14400)
        if result.returncode != 0:
            self._last_error = ErrorService.ffmpeg_error((result.stderr or b'').decode('utf-8', errors='replace'))
            return None
        if not dst.is_file() or dst.stat().st_size == 0:
            self._last_error = QCoreApplication.translate('AMENodes', 'FFmpeg 未生成有效的封装文件')
            return None
        return {'file': [dst]}
