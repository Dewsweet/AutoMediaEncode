from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import (ProgressBar, InfoBar, InfoBarPosition)

from app.components.ame_workflow.ame_graph import AMEGraph
from app.components.ame_workflow.floating_toolbar import FloatingToolbar
from app.components.ame_workflow.nodes import MENU_KEY_MAP
from app.components.ame_workflow.node_palette import NodePaletteMenu
from app.common.style_sheet import StyleSheet


class AMEWorkflowInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AMEWorkflowInterface')

        self._ame_graph = AMEGraph(self)
        self._toolbar = FloatingToolbar(self)
        self._progress = ProgressBar(self)
        self._palette = NodePaletteMenu(self)

        self._executor = None
        self._running = False

        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(6)

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.addWidget(self._ame_graph.widget())

        self._setup_signals()
        StyleSheet.AME_WORKFLOW_INTERFACE.apply(self)

    def _setup_signals(self):
        g = self._ame_graph.graph
        g.node_selected.connect(lambda n: None)

        viewer = self._ame_graph.viewer()
        if viewer:
            viewer.customContextMenuRequested.connect(self._on_viewer_menu)

        self._toolbar.start_clicked.connect(self._on_start)
        self._toolbar.cancel_clicked.connect(self._on_cancel)
        self._palette.node_selected.connect(self._on_palette_node)

    def _on_viewer_menu(self, pos):
        self._palette.exec(self._ame_graph.viewer().mapToGlobal(pos))

    def _on_palette_node(self, menu_key, _):
        cls = MENU_KEY_MAP.get(menu_key)
        if not cls:
            return
        tn = f'ame.{cls.__name__}'
        cur = self._ame_graph.graph.cursor_pos()
        self._ame_graph.create_node(tn, pos=[cur[0], cur[1]])

    def _on_start(self):
        out_cls = self._find_output_class()
        nodes = self._ame_graph.all_nodes()
        if not any(isinstance(n, out_cls) for n in nodes):
            InfoBar.warning(title='工作流不完整', content='请至少添加一个输出节点',
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=3000, parent=self)
            return
        self._running = True
        self._toolbar.set_state('running')
        self._progress.setVisible(True)
        self._progress.setValue(0)
        edges = []
        for n in nodes:
            for pn, port_model in n.model.outputs.items():
                conn = port_model.connected_ports if hasattr(port_model, 'connected_ports') else {}
                for cid, cps in conn.items():
                    for cp in cps:
                        edges.append((n, pn, cid, cp))
        from app.services.ame_workflow.workflow_executor import AMEWorkflowExecutor
        self._executor = AMEWorkflowExecutor(nodes, edges)
        self._executor.progress_updated.connect(lambda v: self._progress.setValue(v))
        self._executor.node_status_changed.connect(lambda nid, s: None)
        self._executor.finished.connect(self._on_finished)
        self._executor.error_occurred.connect(self._on_error)
        self._executor.start()

    def _on_cancel(self):
        if self._executor:
            self._executor.cancel()
        self._reset_ui()

    def _reset_ui(self):
        self._running = False
        self._toolbar.set_state('idle')
        self._progress.setVisible(False)
        self._progress.setValue(0)

    def _on_finished(self):
        self._running = False
        self._toolbar.set_state('idle')
        if self._progress.value() >= 100:
            InfoBar.success(title='处理完成', content='AME 工作流已执行完毕',
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=5000, parent=self)

    def _on_error(self, msg):
        self._running = False
        self._toolbar.set_state('idle')
        self._progress.setVisible(False)
        InfoBar.error(title='工作流执行失败', content=msg,
                      orient=Qt.Horizontal, isClosable=True,
                      position=InfoBarPosition.TOP, duration=8000, parent=self)

    def _find_output_class(self):
        from app.components.ame_workflow.nodes.system.output_node import OutputNode
        return OutputNode

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._toolbar.setGeometry(20, 12, 220, 42)
        self._progress.setGeometry(0, h - 6, w, 6)
        self._toolbar.raise_()
