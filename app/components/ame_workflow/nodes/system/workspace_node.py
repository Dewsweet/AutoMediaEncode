from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import DirBrowseWidget

class WorkspaceNode(AMENodeBase):
    NODE_NAME = '工作区'
    DESCRIPTION = '设定中间文件存储目录，连接输入节点后所有中间文件写入该目录'
    CATEGORY = '系统'; CATEGORY_COLOR = C['Gray']
    INPUTS = []
    OUTPUTS = [('path', P['any'])]
    MENU_KEY = 'workspace'

    def _setup_widgets(self):
        self.add_custom_widget(DirBrowseWidget(self.view, 'workspace', '选择工作区目录'))

    def execute(self, inputs, temp_dir):
        wd = self.property('workspace', '')
        return {'path': [wd]} if wd else None
