from NodeGraphQt import NodeGraph
from NodeGraphQt.constants import PipeLayoutEnum
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView

from qfluentwidgets import isDarkTheme, qconfig

from .nodes import ALL_NODE_CLASSES
from .ame_hotkeys import register as register_hotkeys


class AMEGraph:
    def __init__(self, parent=None):
        self.graph = NodeGraph(parent=parent)
        self.graph.set_pipe_style(PipeLayoutEnum.CURVED.value)

        for cls in ALL_NODE_CLASSES:
            self.graph.register_node(cls)

        w = self.graph.widget
        w.setParent(parent)
        w.show()
        w.setStyleSheet('QTabWidget,QTabWidget::pane,QTabBar,QTabBar::tab{border:none;}')

        self._viewer = None
        for child in w.findChildren(QGraphicsView):
            self._viewer = child
            break
        if self._viewer:
            self._viewer.setContextMenuPolicy(Qt.CustomContextMenu)
            self._viewer.setFrameShape(QGraphicsView.NoFrame)
            self._viewer.setStyleSheet('QGraphicsView{border:none;background:transparent;}')
            register_hotkeys(self._viewer, self.graph)

        qconfig.themeChanged.connect(self._apply_theme)
        self._apply_theme()
        self._create_default_nodes()

    def viewer(self):
        return self._viewer

    def widget(self):
        return self.graph.widget

    def create_node(self, type_, name=None, pos=None):
        node = self.graph.create_node(type_, name=name, pos=pos, push_undo=False)
        self._fix_node_view(node)
        if isDarkTheme():
            node.set_color(45, 45, 45)
        return node

    def _fix_node_view(self, node):
        if not hasattr(node, 'view') or node.view is None:
            return
        v = node.view
        v.setCursor(Qt.CrossCursor)
        if hasattr(v, 'text_item') and v.text_item:
            try:
                v.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
            except Exception:
                pass

    def selected_nodes(self):
        return self.graph.selected_nodes()

    def all_nodes(self):
        return self.graph.all_nodes()

    def save_session(self, path):
        self.graph.save_session(path)

    def load_session(self, path):
        self.graph.load_session(path)

    def delete_node(self, node):
        self.graph.delete_node(node)

    def get_node_by_id(self, nid):
        return self.graph.get_node_by_id(nid)

    def _create_default_nodes(self):
        ws_node = self.graph.create_node('ame.WorkspaceNode', pos=[100, 80], push_undo=False)
        inp_node = self.graph.create_node('ame.InputFileNode', pos=[100, 300], push_undo=False)
        out_node = self.graph.create_node('ame.OutputNode', pos=[1000, 220], push_undo=False)
        for n in (ws_node, inp_node, out_node):
            self._fix_node_view(n)
            if isDarkTheme():
                n.set_color(45, 45, 45)
        ws_node.set_output(0, inp_node.input(0))

    def _apply_theme(self):
        dark = isDarkTheme()
        if dark:
            self.graph.set_background_color(26, 26, 26)
            self.graph.set_grid_color(51, 51, 51)
            text_c = (220, 220, 220, 255)
            border_c = (85, 85, 85, 255)
        else:
            self.graph.set_background_color(240, 240, 240)
            self.graph.set_grid_color(221, 221, 221)
            text_c = (80, 80, 80, 255)
            border_c = (200, 200, 200, 255)

        for node in self.graph.all_nodes():
            node.model.text_color = text_c
            node.model.border_color = border_c
            if dark:
                node.set_color(45, 45, 45)
            elif hasattr(node, '_original_color'):
                node.set_color(*node._original_color)
