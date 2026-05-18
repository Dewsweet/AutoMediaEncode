from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import (ProgressBar, InfoBar, InfoBarPosition)

from app.components.ame_workflow.ame_graph import AMEGraph
from app.components.ame_workflow.ame_inspector import FloatingInspector
from app.components.ame_workflow.floating_toolbar import FloatingToolbar
from app.components.ame_workflow.ame_nodes import registry_key_to_type_name
from app.components.ame_workflow.node_palette import NodePaletteMenu
from app.common.style_sheet import StyleSheet


class AMEWorkflowInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AMEWorkflowInterface")

        self._ame_graph = AMEGraph(self)
        self._toolbar = FloatingToolbar(self)
        self._inspector = FloatingInspector(self)
        self._progress = ProgressBar(self)
        self._palette = NodePaletteMenu(self)

        self._executor = None
        self._running = False

        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(6)

        # graph widget fills the page via layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addWidget(self._ame_graph.widget())

        self._setup_signals()
        StyleSheet.AME_WORKFLOW_INTERFACE.apply(self)

    def _setup_signals(self):
        g = self._ame_graph.graph
        g.node_selected.connect(self._on_node_selected)
        g.node_selection_changed.connect(self._on_selection_changed)
        g.node_double_clicked.connect(self._on_node_double_clicked)

        viewer = self._ame_graph.viewer()
        if viewer:
            viewer.customContextMenuRequested.connect(self._on_viewer_context_menu)

        self._toolbar.start_clicked.connect(self._on_start)
        self._toolbar.pause_clicked.connect(self._on_pause)
        self._toolbar.cancel_clicked.connect(self._on_cancel)

        self._palette.node_selected.connect(self._on_palette_node)

    def _on_node_selected(self, node):
        self._inspector.set_node(node)

    def _on_selection_changed(self, sel, desel):
        if not sel:
            self._inspector.set_node(None)

    def _on_node_double_clicked(self, node):
        self._inspector.set_node(node)

    def _on_viewer_context_menu(self, pos):
        self._palette.exec(self._ame_graph.viewer().mapToGlobal(pos))

    def _on_palette_node(self, reg_key: str, _):
        type_name = registry_key_to_type_name(reg_key)
        g = self._ame_graph.graph
        pos = g.cursor_pos()
        node = self._ame_graph.create_node(type_name, pos=[pos[0], pos[1]])
        if node:
            self._inspector.set_node(node)

    def _on_start(self):
        nodes = self._ame_graph.all_nodes()
        output_nodes = [n for n in nodes if isinstance(n, self._get_output_class())]
        if not output_nodes:
            InfoBar.warning(
                title="工作流不完整",
                content="请至少添加一个「输出」节点",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=3000, parent=self,
            )
            return

        self._running = True
        self._toolbar.set_state('running')
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._run_workflow()

    def _on_pause(self):
        if self._executor:
            self._toolbar.set_state('paused')

    def _on_cancel(self):
        if self._executor:
            self._executor.cancel()
        self._reset_ui()

    def _reset_ui(self):
        self._running = False
        self._toolbar.set_state('idle')
        self._progress.setVisible(False)
        self._progress.setValue(0)

    def _run_workflow(self):
        from app.services.ame_workflow.workflow_executor import AMEWorkflowExecutor
        nodes = self._ame_graph.all_nodes()
        edges = []
        for node in nodes:
            for port_name, conn_dict in node.model.outputs.items():
                for conn_id, conn_ports in conn_dict.items():
                    for cp in conn_ports:
                        edges.append((node, port_name, conn_id, cp))
        self._executor = AMEWorkflowExecutor(nodes, edges)
        self._executor.progress_updated.connect(self._on_executor_progress)
        self._executor.node_status_changed.connect(self._on_node_status)
        self._executor.finished.connect(self._on_workflow_finished)
        self._executor.error_occurred.connect(self._on_workflow_error)
        self._executor.start()

    def _on_executor_progress(self, value: int):
        self._progress.setValue(value)

    def _on_node_status(self, node_id: str, status: str):
        pass

    def _on_workflow_finished(self):
        self._running = False
        self._toolbar.set_state('idle')
        if self._progress.value() >= 100:
            InfoBar.success(
                title="处理完成", content="AME 工作流已执行完毕",
                orient=Qt.Horizontal, isClosable=True,
                position=InfoBarPosition.TOP, duration=5000, parent=self,
            )

    def _on_workflow_error(self, error_msg: str):
        self._running = False
        self._toolbar.set_state('idle')
        self._progress.setVisible(False)
        InfoBar.error(
            title="工作流执行失败", content=error_msg,
            orient=Qt.Horizontal, isClosable=True,
            position=InfoBarPosition.TOP, duration=8000, parent=self,
        )

    def _get_output_class(self):
        from app.components.ame_workflow.ame_nodes import OutputNode
        return OutputNode

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._toolbar.setGeometry(20, 12, 220, 42)
        self._inspector.reposition(w, h)
        self._progress.setGeometry(0, h - 6, w, 6)
        self._toolbar.raise_()
        self._inspector.raise_()
