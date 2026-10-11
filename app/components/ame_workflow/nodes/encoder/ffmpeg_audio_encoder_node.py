from PySide6.QtCore import QT_TRANSLATE_NOOP
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FfmpegSimpleOptionsWidget
from .._helpers import _do_ffmpeg_audio

class EncoderFFmpegAudioNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", 'ffmpeg 音频编码')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", 'FFmpeg 音频编码器')
    CATEGORY = '编码'; CATEGORY_COLOR = C['Blue']
    INPUTS = [('file', P['audio'])]
    OUTPUTS = [('audio', P['audio'])]
    MENU_KEY = 'encoder_ffmpeg_audio'

    def _setup_widgets(self):
        items = ['pcm_s16le', 'pcm_s24le', 'flac', 'alac', 'aac', 'libmp3lame', 'libopus', 'libvorbis', 'ac3']
        self.add_custom_widget(FfmpegSimpleOptionsWidget(self.view, 'Audio_codec', items))

    def execute(self, inputs, temp_dir):
        return _do_ffmpeg_audio(self, inputs, temp_dir, 'aac', '.aac')
