"""AME 画布快捷键模块
每个操作定义为独立函数，快捷键和未来右键菜单共用这些函数引用。
"""

from PySide6.QtGui import QShortcut, QKeySequence


def delete_selected(graph):
    for node in graph.selected_nodes():
        graph.delete_node(node)


def select_all(graph):
    graph.select_all()


def duplicate_selected(graph):
    nodes = graph.selected_nodes()
    if nodes:
        graph.duplicate_nodes(nodes)


def undo(graph):
    graph.undo_stack().undo()


def redo(graph):
    graph.undo_stack().redo()


def fit_selection(graph):
    graph.fit_to_selection()


def reset_zoom(graph):
    graph.reset_zoom()


def save_session(graph):
    current = graph.current_session()
    if current:
        graph.save_session(current)
    else:
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(None, "保存工作流", "",
                                               "AME Workflow (*.json)")
        if path:
            graph.save_session(path)


def load_session(graph):
    from PySide6.QtWidgets import QFileDialog
    path, _ = QFileDialog.getOpenFileName(None, "加载工作流", "",
                                           "AME Workflow (*.json)")
    if path:
        graph.load_session(path)


def copy_nodes(graph):
    graph.copy_nodes()


def cut_nodes(graph):
    graph.cut_nodes()


def paste_nodes(graph):
    graph.paste_nodes()


# ═══════════ 快捷键映射 ═══════════

SHORTCUT_MAP = {
    'Delete':         delete_selected,
    'Ctrl+A':         select_all,
    'Ctrl+D':         duplicate_selected,
    'Ctrl+C':         copy_nodes,
    'Ctrl+X':         cut_nodes,
    'Ctrl+V':         paste_nodes,
    'Ctrl+Z':         undo,
    'Ctrl+Shift+Z':   redo,
    'F':              fit_selection,
    'Ctrl+0':         reset_zoom,
    'H':              reset_zoom,
}


def register(viewer, graph):
    """安装 QShortcut 到 viewer。在 AMEGraph.__init__ 中调用。"""
    for key, callback in SHORTCUT_MAP.items():
        sc = QShortcut(QKeySequence(key), viewer)
        sc.activated.connect(lambda cb=callback: cb(graph))
