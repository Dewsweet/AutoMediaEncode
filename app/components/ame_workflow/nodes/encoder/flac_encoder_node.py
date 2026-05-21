from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import StapleAudioEncoderWidget

class EncoderFLACNode(AMENodeBase):
    NODE_NAME = 'FLAC 编码(ffmpeg)'
    DESCRIPTION = 'FLAC 无损音频编码'
    CATEGORY = '编码'; CATEGORY_COLOR = C['编码']
    INPUTS = [('input', P['audio'])]
    OUTPUTS = [('audio', P['audio'])]
    MENU_KEY = 'encoder_flac'

    def _setup_widgets(self):
        self.add_custom_widget(StapleAudioEncoderWidget(self.view, 'FLAC 编码设置', 'flac'))


    def execute(self, inputs, temp_dir):
        pass
