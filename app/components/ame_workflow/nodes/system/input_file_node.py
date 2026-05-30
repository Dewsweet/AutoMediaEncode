from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FileBrowseWidget
from app.common.media_utils import VIDEO_EXTS, AUDIO_EXTS, IMAGE_EXTS, SUBTITLE_EXTS

class InputFileNode(AMENodeBase):
    NODE_NAME = '输入文件'
    DESCRIPTION = '载入媒体文件'
    CATEGORY = '输入'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('path', P['any'])]
    OUTPUTS = [('file', P['any'])]
    MENU_KEY = 'input_file'

    def _setup_widgets(self):
        EXT = "视频文件 (" + ' '.join(f'*{e}' for e in VIDEO_EXTS) + ');;' \
              "音频文件 (" + ' '.join(f'*{e}' for e in AUDIO_EXTS) + ');;' \
              "图片文件 (" + ' '.join(f'*{e}' for e in IMAGE_EXTS) + ');;' \
              "字幕文件 (" + ' '.join(f'*{e}' for e in SUBTITLE_EXTS) + ');;' \
              "所有文件 (*.*)"
        self.add_custom_widget(FileBrowseWidget(self.view, 'input_file', '选择文件', exts=EXT))
        self.create_property('file_type', 'auto', widget_type=HIDDEN, tab='')

    def execute(self, inputs, temp_dir):
        fp = self.property('input_file', '')
        return {'file': [fp]} if fp else None
