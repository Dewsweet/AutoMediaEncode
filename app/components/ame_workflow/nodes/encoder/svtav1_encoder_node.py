from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import PresetSwitchWidget, CLITextWidget
from .._helpers import _do_cli_encode

class EncoderSvtAv1Node(AMENodeBase):
    NODE_NAME = 'SVT-AV1 编码 (ffmpeg)'
    DESCRIPTION = 'SVT-AV1 编码器, 需要 ffmpeg 内置 SVT-AV1 支持'
    CATEGORY = '编码'; CATEGORY_COLOR = C['Red']
    INPUTS = [('input', P['video'])]
    OUTPUTS = [('video', P['video'])]
    MENU_KEY = 'encoder_svtav1'

    def _setup_widgets(self):
        self.add_custom_widget(PresetSwitchWidget(self.view, 'preset_cfg', 'svtav1'))
        self.add_custom_widget(CLITextWidget(self.view, 'custom_cli'))

    def execute(self, inputs, temp_dir):
        return _do_cli_encode(self, inputs, temp_dir, 'SVTAV1', '.ivf')
