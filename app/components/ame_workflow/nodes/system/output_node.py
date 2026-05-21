from .._base import AMENodeBase, C, P, HIDDEN


class OutputNode(AMENodeBase):
    NODE_NAME = '输出文件'
    DESCRIPTION = '最终输出文件路径'
    CATEGORY = '输出'; CATEGORY_COLOR = C['输出']
    INPUTS = [('input', P['any'])]
    OUTPUTS = []
    MENU_KEY = 'output'

    def _setup_widgets(self):
        EXT = 'MKV (*.mkv);;MP4 (*.mp4);;All (*)'
        from .._widgets import SaveBrowseWidget
        self.add_custom_widget(SaveBrowseWidget(self.view, 'output_path', EXT))

    def execute(self, inputs, temp_dir):
        return None
