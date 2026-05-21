from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import PresetSwitchWidget, CLITextWidget

class EncoderX264Node(AMENodeBase):
    NODE_NAME = 'x264 编码'
    DESCRIPTION = 'x264 CLI 编码器'
    CATEGORY = '编码'; CATEGORY_COLOR = C['编码']
    INPUTS = [('input', P['video'])]
    OUTPUTS = [('video', P['video'])]
    MENU_KEY = 'encoder_x264'

    def _setup_widgets(self):
        self.add_custom_widget(PresetSwitchWidget(self.view, 'preset_cfg', 'x264'))
        self.add_custom_widget(CLITextWidget(self.view, 'custom_cli'))

    def execute(self, inputs, temp_dir):
        return _do_cli_encode(self, inputs, temp_dir, 'x264', '.h264')
