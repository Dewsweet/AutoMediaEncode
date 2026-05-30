from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import PresetSwitchWidget, CLITextWidget
from .._helpers import _do_cli_encode

class EncoderX265Node(AMENodeBase):
    NODE_NAME = 'x265 编码'
    DESCRIPTION = 'x265 CLI 编码器'
    CATEGORY = '编码'; CATEGORY_COLOR = C['Red']
    INPUTS = [('input', P['video'])]
    OUTPUTS = [('video', P['video'])]
    MENU_KEY = 'encoder_x265'

    def _setup_widgets(self):
        self.add_custom_widget(PresetSwitchWidget(self.view, 'preset_cfg', 'x265'))
        self.add_custom_widget(CLITextWidget(self.view, 'custom_cli'))

    def execute(self, inputs, temp_dir):
        return _do_cli_encode(self, inputs, temp_dir, 'x265', '.h265')
