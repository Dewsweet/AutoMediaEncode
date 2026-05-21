from NodeGraphQt import NodeGraph
from NodeGraphQt.constants import PipeLayoutEnum
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView

from qfluentwidgets import isDarkTheme, qconfig

from .nodes import ALL_NODE_CLASSES


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

        qconfig.themeChanged.connect(self._apply_theme)
        self._apply_theme()

    def viewer(self):
        return self._viewer

    def widget(self):
        return self.graph.widget

    def create_node(self, type_, name=None, pos=None):
        node = self.graph.create_node(type_, name=name, pos=pos, push_undo=False)
        self._fix_node_view(node)
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

    def _apply_theme(self):
        dark = isDarkTheme()
        if dark:
            self.graph.set_background_color(26, 26, 26)
            self.graph.set_grid_color(51, 51, 51)
            text_c = (220, 220, 220, 255)
            border_c = (85, 85, 85, 255)
            node_bg = (45, 45, 45)
        else:
            self.graph.set_background_color(240, 240, 240)
            self.graph.set_grid_color(221, 221, 221)
            text_c = (80, 80, 80, 255)
            border_c = (200, 200, 200, 255)
            node_bg = (245, 245, 245)
        for node in self.graph.all_nodes():
            node.model.text_color = text_c
            node.model.border_color = border_c
            if hasattr(node, 'set_color'):
                node.set_color(*node_bg)
