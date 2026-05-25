from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FilesBrowseWidget
from app.common.media_utils import VIDEO_EXTS, AUDIO_EXTS, IMAGE_EXTS, SUBTITLE_EXTS

class InputFilesNode(AMENodeBase):
    NODE_NAME = '多文件输入'
    DESCRIPTION = '批量载入多个文件'
    CATEGORY = '系统'; CATEGORY_COLOR = C['系统']
    INPUTS = [('path', P['any'])]
    OUTPUTS = [('files', P['any'])]
    MENU_KEY = 'input_multi'

    def _setup_widgets(self):
        EXT = "视频文件 (" + ' '.join(f'*{e}' for e in VIDEO_EXTS) + ');;' \
              "音频文件 (" + ' '.join(f'*{e}' for e in AUDIO_EXTS) + ');;' \
              "图片文件 (" + ' '.join(f'*{e}' for e in IMAGE_EXTS) + ');;' \
              "字幕文件 (" + ' '.join(f'*{e}' for e in SUBTITLE_EXTS) + ');;' \
              "所有文件 (*.*)"
        self.add_custom_widget(FilesBrowseWidget(self.view, 'input_multi', exts=EXT))
        self.create_property('file_list', '', widget_type=HIDDEN, tab='')

    def execute(self, inputs, temp_dir):
        return inputs['path']