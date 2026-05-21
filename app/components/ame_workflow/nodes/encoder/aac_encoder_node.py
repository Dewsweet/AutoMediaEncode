from .._base import AMENodeBase, C, P
from .._widgets import StapleAudioEncoderWidget

class EncoderAACNode(AMENodeBase):
    NODE_NAME = 'AAC 编码(qaac)'
    DESCRIPTION = 'AAC 音频编码 (CBR 192k)'
    CATEGORY = '编码'; CATEGORY_COLOR = C['编码']
    INPUTS = [('input', P['audio'])]
    OUTPUTS = [('audio', P['audio'])]
    MENU_KEY = 'encoder_aac'

    def _setup_widgets(self):
        self.add_custom_widget(StapleAudioEncoderWidget(self.view, 'AAC 编码设置', 'aac'))

    def execute(self, inputs, temp_dir):
        pass


