from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CLITextWidget

class TextWidget(CLITextWidget):
    def __init__(self, parent, name, placeholder='输入文本内容...'):
        super().__init__(parent, name)
        self._edit.setPlaceholderText(placeholder)
        self._edit.setFixedHeight(200)


class TextNode(AMENodeBase):
    NODE_NAME = '纯文本'
    DESCRIPTION = '输入文本内容，纯文本提示节点'
    CATEGORY = '系统'; CATEGORY_COLOR = C['Gray']
    INPUTS = []
    OUTPUTS = []
    MENU_KEY = 'text'

    def _setup_widgets(self):
        self.add_custom_widget(TextWidget(self.view, 'text', '输入文本内容'))

    def execute(self, inputs, temp_dir):
        pass