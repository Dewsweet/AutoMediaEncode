from PySide6.QtCore import QCoreApplication, QT_TRANSLATE_NOOP
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import DirBrowseWidget

class WorkspaceNode(AMENodeBase):
    NODE_NAME = QT_TRANSLATE_NOOP("AMENodes", '工作区')
    DESCRIPTION = QT_TRANSLATE_NOOP("AMENodes", '设定中间文件存储目录，连接输入节点后所有中间文件写入该目录')
    CATEGORY = '系统'; CATEGORY_COLOR = C['Gray']
    INPUTS = []
    OUTPUTS = [('workspace', P['any'])]
    MENU_KEY = 'workspace'

    def _setup_widgets(self):
        self.add_custom_widget(DirBrowseWidget(self.view, 'workspace', QCoreApplication.translate('AMENodes', '选择工作区目录')))

    def execute(self, inputs, temp_dir):
        wd = self.property('workspace', '')
        return {'workspace': [wd]} if wd else None
