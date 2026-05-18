from NodeGraphQt import NodeGraph
from NodeGraphQt.constants import PipeLayoutEnum
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView

from qfluentwidgets import isDarkTheme, qconfig

from .ame_nodes import NODE_CLASSES


class AMEGraph:
    def __init__(self, parent=None):
        self.graph = NodeGraph(parent=parent)
        self.graph.set_pipe_style(PipeLayoutEnum.CURVED.value)

        for cls in NODE_CLASSES:
            self.graph.register_node(cls)

        w = self.graph.widget
        w.setParent(parent)
        w.show()
        w.setStyleSheet("QTabWidget { border: none; } QTabWidget::pane { border: none; } QTabBar::tab { border: none; } QTabBar { border: none; }")

        self._viewer = self._find_viewer(w)
        if self._viewer:
            self._viewer.setContextMenuPolicy(Qt.CustomContextMenu)
            self._viewer.setFrameShape(QGraphicsView.NoFrame)
            self._viewer.setStyleSheet("QGraphicsView { border: none; background: transparent; }")

        self._apply_theme()
        qconfig.themeChanged.connect(self._apply_theme)

    def _find_viewer(self, widget):
        for child in widget.findChildren(QGraphicsView):
            return child
        return None

    def viewer(self):
        return self._viewer

    def widget(self):
        return self.graph.widget

    def create_node(self, type_, name=None, pos=None):
        return self.graph.create_node(type_, name=name, pos=pos, push_undo=False)

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
