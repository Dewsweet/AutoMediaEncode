from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import DirBrowseWidget

class OutputNode(AMENodeBase):
    NODE_NAME = '输出文件'
    DESCRIPTION = '最终输出文件路径'
    CATEGORY = '输出'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('input', P['any'])]
    OUTPUTS = []
    MENU_KEY = 'output'

    def _setup_widgets(self):
        self.add_custom_widget(DirBrowseWidget(self.view, 'output', btn_text='选择输出目录'))

    def execute(self, inputs, temp_dir):
        return None
