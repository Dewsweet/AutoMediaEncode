from .._base import AMENodeBase, C, P
from .._widgets import StapleAudioEncoderWidget
from .._helpers import _do_qaac_encode
from app.services.tool_service import ToolService

class EncoderAACNode(AMENodeBase):
    NODE_NAME = 'AAC 编码 (qaac)'
    DESCRIPTION = 'AAC 音频编码, 使用 qaac 编码器的 CVBR 模式'
    CATEGORY = '编码'; CATEGORY_COLOR = C['Blue']
    INPUTS = [('input', P['audio'])]
    OUTPUTS = [('audio', P['audio'])]
    MENU_KEY = 'encoder_aac'

    def _setup_widgets(self):
        self.add_custom_widget(StapleAudioEncoderWidget(self.view, 'Audio_codec', 'aac'))

    def execute(self, inputs, temp_dir):
        return _do_qaac_encode(self, inputs, temp_dir, '.m4a')
