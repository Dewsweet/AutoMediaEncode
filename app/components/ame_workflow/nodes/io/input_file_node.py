from PySide6.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FileBrowseWidget
from app.common.media_utils import VIDEO_EXTS, AUDIO_EXTS, IMAGE_EXTS, SUBTITLE_EXTS

class InputFileNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", '输入文件')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", '载入媒体文件')
    CATEGORY = '输入'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('workspace', P['any'])]
    OUTPUTS = [('file', P['any'])]
    MENU_KEY = 'input_file'

    def _setup_widgets(self):
        EXT = QCoreApplication.translate(
            'AMENodes', '视频文件 ({video});;音频文件 ({audio});;图片文件 ({image});;字幕文件 ({subtitle});;所有文件 (*.*)'
        ).format(video=' '.join(f'*{e}' for e in VIDEO_EXTS),
                 audio=' '.join(f'*{e}' for e in AUDIO_EXTS),
                 image=' '.join(f'*{e}' for e in IMAGE_EXTS),
                 subtitle=' '.join(f'*{e}' for e in SUBTITLE_EXTS))
        self.add_custom_widget(FileBrowseWidget(self.view, 'input_file', QCoreApplication.translate('AMENodes', '选择文件'), exts=EXT))
        self.create_property('file_type', 'auto', widget_type=HIDDEN, tab='')

    def execute(self, inputs, temp_dir):
        fp = self.property('input_file', '')
        return {'file': [fp]} if fp else None
