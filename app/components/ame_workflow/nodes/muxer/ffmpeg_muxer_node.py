import subprocess
from pathlib import Path
from .._base import AMENodeBase, C, P
from .._widgets import NodeComboBoxWidget
from app.services.tool_service import ToolService
from app.common.logger import logger

class MuxerFFmpegNode(AMENodeBase):
    NODE_NAME = '封装 (FFmpeg)'
    DESCRIPTION = 'FFmpeg 封装 MP4/MOV，接收单视频单音频'
    CATEGORY = '封装'; CATEGORY_COLOR = C['Green']
    INPUTS = [('video', P['video']), ('audio', P['audio'])]
    OUTPUTS = [('output', P['any'])]
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
        subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, timeout=14400)
        return {'output': [dst]} if dst.is_file() else None
