from PySide6.QtCore import QT_TRANSLATE_NOOP
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import StapleAudioEncoderWidget
from .._helpers import _do_ffmpeg_audio

class EncoderFLACNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", 'FLAC 编码(ffmpeg)')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", 'FLAC 无损音频编码')
    CATEGORY = '编码'; CATEGORY_COLOR = C['Blue']
    INPUTS = [('file', P['audio'])]
    OUTPUTS = [('audio', P['audio'])]
    MENU_KEY = 'encoder_flac'

    def _setup_widgets(self):
        self.add_custom_widget(StapleAudioEncoderWidget(self.view, 'Audio_codec', 'flac'))

    def execute(self, inputs, temp_dir):
        return _do_ffmpeg_audio(self, inputs, temp_dir, 'flac', '.flac')
