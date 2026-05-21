from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FileBrowseWidget
from app.common.media_utils import VIDEO_EXTS, AUDIO_EXTS, IMAGE_EXTS, SUBTITLE_EXTS

class InputFileNode(AMENodeBase):
    NODE_NAME = '输入文件'
    DESCRIPTION = '载入媒体文件，自动探测轨道后显示输出端口'
    CATEGORY = '系统'; CATEGORY_COLOR = C['系统']
    INPUTS = [('path', P['any'])]
    OUTPUTS = [('file', P['any'])]
    MENU_KEY = 'input_file'

    def _setup_widgets(self):
        EXT = "视频文件 (" + ' '.join(f'*{e}' for e in VIDEO_EXTS) + ');;' \
              "音频文件 (" + ' '.join(f'*{e}' for e in AUDIO_EXTS) + ');;' \
              "图片文件 (" + ' '.join(f'*{e}' for e in IMAGE_EXTS) + ');;' \
              "字幕文件 (" + ' '.join(f'*{e}' for e in SUBTITLE_EXTS) + ');;' \
              "所有文件 (*.*)"
        self.add_custom_widget(FileBrowseWidget(self.view, '选择输入文件', EXT))
        self.create_property('file_type', 'auto', widget_type=HIDDEN, tab='')

    def execute(self, inputs, temp_dir):
        return inputs['path'] 
