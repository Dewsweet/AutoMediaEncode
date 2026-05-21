from .._base import AMENodeBase, C, P, HIDDEN
from app.common.media_utils import VIDEO_EXTS, AUDIO_EXTS, IMAGE_EXTS, SUBTITLE_EXTS
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget, QFileDialog
from qfluentwidgets import PushButton, LineEdit

class NodeWidget(NodeBaseWidget):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.name = name
        mainbox = QWidget()
        mainLayout = QVBoxLayout(mainbox)

        self._btn = PushButton(self.name, mainbox)
        
        self._line = LineEdit(mainbox)
        self._line.setPlaceholderText('选择路径...')

        mainLayout.addWidget(self._btn)
        mainLayout.addWidget(self._line)
        self.set_custom_widget(mainbox)

        self._signal_connect()

    def _signal_connect(self):
        self._btn.clicked.connect(self._browse)
        self._line.textChanged.connect(lambda t: self.on_value_changed(t))

    def _browse(self):
        EXT = "视频文件 (" + ' '.join(f'*{e}' for e in VIDEO_EXTS) + ');;' \
              "音频文件 (" + ' '.join(f'*{e}' for e in AUDIO_EXTS) + ');;' \
              "图片文件 (" + ' '.join(f'*{e}' for e in IMAGE_EXTS) + ');;' \
              "字幕文件 (" + ' '.join(f'*{e}' for e in SUBTITLE_EXTS) + ');;' \
              "所有文件 (*.*)"
        ps, _ = QFileDialog.getOpenFileNames(None, '选择文件', '', EXT)
        if ps:
            self._line.setText('\n'.join(ps))
            
    def get_value(self):
        return self._line.text()
    def set_value(self, value):
        if value:
            self._line.setText(str(value))
    

class InputFilesNode(AMENodeBase):
    NODE_NAME = '多文件输入'
    DESCRIPTION = '批量载入多个文件'
    CATEGORY = '系统'; CATEGORY_COLOR = C['系统']
    INPUTS = [('path', P['any'])]
    OUTPUTS = [('files', P['any'])]
    MENU_KEY = 'input_multi'

    def _setup_widgets(self):
        node_widget = NodeWidget(self.view, '选择输入文件')
        self.add_custom_widget(node_widget)
        self.create_property('file_list', '', widget_type=HIDDEN, tab='')

    def execute(self, inputs, temp_dir):
        return inputs['path']