from .._base import AMENodeBase, C, P, HIDDEN
from app.services.tool_service import ToolService


class VSPipeNode(AMENodeBase):
    NODE_NAME = 'vspipe'
    DESCRIPTION = 'VapourSynth 管道输出，连接编码器'
    CATEGORY = '工具'; CATEGORY_COLOR = C['Purple']
    INPUTS = [('script', P['script'])]
    OUTPUTS = [('video', P['video'])]
    MENU_KEY = 'vspipe'

    def execute(self, inputs, temp_dir):
        scr = (inputs.get('script') or [''])[0]
        vspipe_path = ToolService.get_tool_path('vspipe')
        vspipe = f'"{vspipe_path}" --y4m "{scr}"' if vspipe else None
        return {'video': [vspipe]} if scr else None
