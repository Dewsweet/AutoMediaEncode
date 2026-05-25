from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CustomNameWidget

class CustomNameNode(AMENodeBase):
    NODE_NAME = '自定义文件名'
    DESCRIPTION = '自定义文件名'
    CATEGORY = '系统'; CATEGORY_COLOR = C['Gray']
    INPUTS = [('input', P['any'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'custom_name'

    def _setup_widgets(self):
        self.add_custom_widget(CustomNameWidget(self.view, 'custom_name'))

    def execute(self, inputs, temp_dir):
        return inputs['input']