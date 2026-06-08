"""AME 画布右键菜单 — 文件/编辑/节点/视图 四级结构"""
from PySide6.QtCore import Qt, QPointF, Signal

from qfluentwidgets import RoundMenu, Action

from .node_palette import NODE_PALETTE_STRUCTURE
from .nodes import MENU_KEY_MAP
from .ame_hotkeys import (undo, redo, copy_nodes, cut_nodes, paste_nodes,
                           delete_selected, select_all, duplicate_selected,
                           fit_selection, reset_zoom)
from NodeGraphQt.constants import ViewerEnum


class AMEConextMenu(RoundMenu):
    save_clicked = Signal()
    load_clicked = Signal()
    export_clicked = Signal()
    import_clicked = Signal()
    node_selected = Signal(str, QPointF)

    def __init__(self, graph, parent=None):
        super().__init__(parent=parent)
        self._graph = graph
        self._scene_pos = QPointF(0, 0)
        self._built = False
        self._displays = []
        self._pnode_add = None
        self._add_file_menu()
        self._add_edit_menu()
        self._add_node_menu()
        self._add_view_menu()

    def set_scene_pos(self, pos: QPointF):
        self._scene_pos = pos

    def _add_file_menu(self):
        m = RoundMenu("文件", self)
        m.addAction(Action("保存工作流", shortcut="Ctrl+S",
                            triggered=lambda: self.save_clicked.emit()))
        m.addAction(Action("返回加载页", shortcut="Ctrl+O",
                            triggered=lambda: self.load_clicked.emit()))
        m.addSeparator()
        m.addAction(Action("导出 JSON", triggered=lambda: self.export_clicked.emit()))
        m.addAction(Action("导入 JSON", triggered=lambda: self.import_clicked.emit()))
        self.addMenu(m)

    # ── 编辑 ──
    def _add_edit_menu(self):
        g = self._graph
        m = RoundMenu("编辑", self)

        m.addAction(Action("撤销", shortcut="Ctrl+Z", triggered=lambda: undo(g)))
        m.addAction(Action("重做", shortcut="Ctrl+Shift+Z", triggered=lambda: redo(g)))
        m.addSeparator()
        m.addAction(Action("复制", shortcut="Ctrl+C", triggered=lambda: copy_nodes(g)))
        m.addAction(Action("剪切", shortcut="Ctrl+X", triggered=lambda: cut_nodes(g)))
        m.addAction(Action("粘贴", shortcut="Ctrl+V", triggered=lambda: paste_nodes(g)))
        m.addAction(Action("删除", shortcut="Delete", triggered=lambda: delete_selected(g)))
        m.addSeparator()
        m.addAction(Action("全选", shortcut="Ctrl+A", triggered=lambda: select_all(g)))
        m.addAction(Action("复制选中", shortcut="Ctrl+D", triggered=lambda: duplicate_selected(g)))
        m.addAction(Action("适应选中", shortcut="F", triggered=lambda: fit_selection(g)))
        self.addMenu(m)

    # ── 节点 (复用 NodePaletteMenu 结构) ──
    def _add_node_menu(self):
        m = RoundMenu("节点", self)
        self._build_palette_tree(m, NODE_PALETTE_STRUCTURE)
        self.addMenu(m)

    def _build_palette_tree(self, parent_menu, items):
        SPECIAL_KEYS = {'vs_compound'}
        for item in items:
            if item is None:
                parent_menu.addSeparator()
                continue
            label, target = item
            if isinstance(target, list):
                sub = RoundMenu(label, parent_menu)
                self._build_palette_tree(sub, target)
                parent_menu.addMenu(sub)
            else:
                if target in MENU_KEY_MAP or target in SPECIAL_KEYS:
                    a = Action(label, parent_menu)
                    a.triggered.connect(
                        (lambda k: lambda: self.node_selected.emit(k, self._scene_pos))(target))
                    parent_menu.addAction(a)

    # ── 视图 ──
    def _add_view_menu(self):
        g = self._graph
        m = RoundMenu("视图", self)
        m.addAction(Action("重置缩放", shortcut="Ctrl+0", triggered=lambda: reset_zoom(g)))
        m.addSeparator()
        m.addAction(Action("背景: 网格线",
                            triggered=lambda: g.set_grid_mode(ViewerEnum.GRID_DISPLAY_LINES.value)))
        m.addAction(Action("背景: 点阵",
                            triggered=lambda: g.set_grid_mode(ViewerEnum.GRID_DISPLAY_DOTS.value)))
        m.addAction(Action("背景: 无",
                            triggered=lambda: g.set_grid_mode(ViewerEnum.GRID_DISPLAY_NONE.value)))
        self.addMenu(m)

    def exec(self, *args, **kwargs):
        super().exec(*args, **kwargs)
