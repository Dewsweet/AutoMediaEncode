from PySide6.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import CLITextWidget

class TextWidget(CLITextWidget):
    def __init__(self, parent, name, placeholder=None):
        super().__init__(parent, name)
        self._edit.setPlaceholderText(placeholder if placeholder is not None else QCoreApplication.translate('AMENodes', '输入文本内容...'))
        self._edit.setFixedHeight(200)


class TextNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", '纯文本')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", '输入文本内容，纯文本提示节点')
    CATEGORY = '系统'; CATEGORY_COLOR = C['Gray']
    INPUTS = []
    OUTPUTS = []
    MENU_KEY = 'text'

    def _setup_widgets(self):
        self.add_custom_widget(TextWidget(self.view, 'text', QCoreApplication.translate('AMENodes', '输入文本内容')))

    def execute(self, inputs, temp_dir):
        pass