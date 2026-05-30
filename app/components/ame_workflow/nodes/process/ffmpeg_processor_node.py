from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CLITextWidget

class FFmpegProcessorNode(AMENodeBase):
    NODE_NAME = 'ffmpeg'
    DESCRIPTION = '自定义 FFmpeg 命令行处理'
    CATEGORY = '工具'; CATEGORY_COLOR = C['Orange']
    INPUTS = [('input', P['any'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'ffmpeg_processor'

    def _setup_widgets(self):
        self.add_custom_widget(CLITextWidget(self.view, 'ffmpeg_processor'))

    def execute(self, inputs, temp_dir):
        import os, subprocess, shlex
        src = (inputs.get('input') or [''])[0]
        if not src:
            return None
        ff = __import__('app.services.tool_service', fromlist=['ToolService']).ToolService.get_tool_path('ffmpeg')
        if not ff:
            return None
        cli = self.property('ffmpeg_processor', '')
        try:
            extra = shlex.split(cli) if cli else []
        except ValueError:
            extra = cli.split() if cli else []
        dst = os.path.join(temp_dir, f'processed_{self.id}.mkv')
        cmd = [ff, '-i', src] + extra + [dst, '-y']
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=3600)
        return {'output': [dst]} if os.path.isfile(dst) else None
