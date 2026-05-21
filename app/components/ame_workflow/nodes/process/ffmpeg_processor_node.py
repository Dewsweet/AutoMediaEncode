import os, subprocess, uuid
import shlex
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CLITextWidget

class FFmpegProcessorNode(AMENodeBase):
    NODE_NAME = 'ffmpeg'
    DESCRIPTION = '自定义 FFmpeg 命令行处理'
    CATEGORY = '处理'; CATEGORY_COLOR = C['处理']
    INPUTS = [('input', P['any'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'ffmpeg_processor'

    def _setup_widgets(self):
        self.add_custom_widget(CLITextWidget(self.view, 'cli_args'))

    def execute(self, inputs, temp_dir):
        src = (inputs.get('input') or [''])[0]
        if not src: return None
        
        from app.services.tool_service import ToolService
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff: return None
        cli = self.property('cli_args', '')
        
        try: extra = shlex.split(cli) if cli else []
        except ValueError: extra = cli.split() if cli else []
        dst = os.path.join(temp_dir, f'processed_{self.id}.mkv')
        cf = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        subprocess.run([ff,'-i',src]+extra+[dst,'-y'], creationflags=cf, capture_output=True, timeout=3600)
        return {'output': [dst]} if os.path.isfile(dst) else None
