from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FileBrowseWidget

class VPYLoaderNode(AMENodeBase):
    NODE_NAME = 'vpy加载器'
    DESCRIPTION = '载入 VapourSynth 脚本'
    CATEGORY = '处理'; CATEGORY_COLOR = P['script']
    INPUTS = [('input', P['video'])]
    OUTPUTS = [('script', P['script'])]
    MENU_KEY = 'vpy_loader'

    def _setup_widgets(self):
        EXT = 'VPY 脚本 (*.vpy);;All (*)'
        self.add_custom_widget(FileBrowseWidget(self.view, 'vpy_path', EXT))

    def execute(self, inputs, temp_dir):
        vpy = self.property('vpy_path', '')
        src = (inputs.get('input') or [''])[0]
        return {'script': [vpy]} if vpy else None
