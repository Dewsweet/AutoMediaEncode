from .._base import AMENodeBase, C, P
from .._widgets import StapleAudioEncoderWidget

class EncoderOPUSNode(AMENodeBase):
    NODE_NAME = 'Opus 编码(ffmpeg)'
    DESCRIPTION = 'Opus 音频编码 (CBR 128k)'
    CATEGORY = '编码'; CATEGORY_COLOR = C['Blue']
    INPUTS = [('input', P['audio'])]
    OUTPUTS = [('audio', P['audio'])]
    MENU_KEY = 'encoder_opus'

    def _setup_widgets(self):
        self.add_custom_widget(StapleAudioEncoderWidget(self.view, 'OPUS_encoder', 'opus'))

    def execute(self, inputs, temp_dir):
        pass