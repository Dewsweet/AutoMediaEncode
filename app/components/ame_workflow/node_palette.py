from PySide6.QtCore import Qt, QPointF, Signal

from qfluentwidgets import RoundMenu, Action

from .nodes.node_registry import get_nodes_by_category
from . import CATEGORY_COLORS


class NodePaletteMenu(RoundMenu):
    node_selected = Signal(str, QPointF)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._scene_pos = QPointF(0, 0)
        self._build()

    def set_scene_pos(self, pos: QPointF):
        self._scene_pos = pos

    def _build(self):
        self.clear()
        nodes_by_cat = get_nodes_by_category()

        category_order = ["系统", "输入", "处理", "编码", "封装", "输出"]
        for cat in category_order:
            if cat in nodes_by_cat and nodes_by_cat[cat]:
                color = CATEGORY_COLORS.get(cat, "#607D8B")
                submenu = RoundMenu(cat, self)
                for meta in nodes_by_cat[cat]:
                    action = Action(meta['name'], submenu)
                    action.triggered.connect(
                        (lambda t: lambda: self._emit_node_type(t))(meta['type'])
                    )
                    submenu.addAction(action)
                self.addMenu(submenu)

    def _emit_node_type(self, node_type: str):
        self.node_selected.emit(node_type, self._scene_pos)
