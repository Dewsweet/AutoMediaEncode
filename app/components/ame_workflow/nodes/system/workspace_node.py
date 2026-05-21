from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import DirBrowseWidget

class WorkspaceNode(AMENodeBase):
    NODE_NAME = '工作区'
    DESCRIPTION = '设定中间文件存储目录，连接输入节点后所有中间文件写入该目录'
    CATEGORY = '系统'; CATEGORY_COLOR = C['系统']
    INPUTS = []
    OUTPUTS = [('path', P['any'])]
    MENU_KEY = 'workspace'

    def _setup_widgets(self):
        self.add_custom_widget(DirBrowseWidget(self.view, '选择工作区文件夹'))

    def execute(self, inputs, temp_dir):
        return None
