import uuid
import time
import json
from pathlib import Path

from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (TitleLabel, PrimaryPushButton, PushButton,
                            ProgressBar, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, BodyLabel)

from app.components.ame_workflow.node_canvas import AMENodeCanvas
from app.components.ame_workflow.node_palette import NodePaletteMenu
from app.components.ame_workflow.node_edit_dialog import AMENodeEditDialog
from app.components.ame_workflow.nodes.node_registry import create_node_data
from app.common.style_sheet import StyleSheet


class AMEWorkflowInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AMEWorkflowInterface")

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self._setup_header()
        self._setup_canvas()
        self._setup_progress_bar()
        self._setup_palette()

        self._executor = None
        self._running = False

        StyleSheet.AME_WORKFLOW_INTERFACE.apply(self)

        self.canvas.context_menu_requested.connect(self._on_canvas_context_menu)

    def _setup_header(self):
        header_widget = QWidget(self)
        header_widget.setFixedHeight(44)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 6, 16, 6)

        title = TitleLabel("AME", self)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self._start_btn = PrimaryPushButton(FIF.PLAY, "开始", self)
        self._cancel_btn = PushButton(FIF.CANCEL, "取消", self)
        self._cancel_btn.setVisible(False)

        header_layout.addWidget(self._cancel_btn)
        header_layout.addWidget(self._start_btn)
        self.mainLayout.addWidget(header_widget)

        self._start_btn.clicked.connect(self._on_start)
        self._cancel_btn.clicked.connect(self._on_cancel)

    def _setup_canvas(self):
        self.canvas = AMENodeCanvas(self)
        self.mainLayout.addWidget(self.canvas, 1)

    def _setup_progress_bar(self):
        self._progress_bar = ProgressBar(self)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(6)
        self.mainLayout.addWidget(self._progress_bar)

    def _setup_palette(self):
        self._palette = NodePaletteMenu(self)
        self._palette.node_selected.connect(self._on_node_type_selected)

    def _on_canvas_context_menu(self, scene_pos: QPointF):
        self._palette.set_scene_pos(scene_pos)
        self._palette.exec(self.canvas.mapToGlobal(self.canvas.mapFromScene(scene_pos)))

    def _on_node_type_selected(self, node_type: str, scene_pos: QPointF):
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        node_data = create_node_data(node_type, node_id=node_id, x=scene_pos.x(), y=scene_pos.y())
        if node_data:
            node = self.canvas.add_node(node_data, x=scene_pos.x(), y=scene_pos.y())
            node.double_clicked.connect(self._on_node_edit)

    def _on_node_edit(self, node):
        dlg = AMENodeEditDialog(node, self.window())
        dlg.params_changed.connect(self._on_params_changed)
        dlg.exec()

    def _on_params_changed(self, node_id, params):
        pass

    def _on_start(self):
        nodes = self.canvas.get_nodes()
        edges = self.canvas.get_edges()

        output_nodes = [n for n in nodes if n.node_type() == 'output']
        if not output_nodes:
            InfoBar.warning(
                title="工作流不完整",
                content="请至少添加一个「输出」节点",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self,
            )
            return

        self._running = True
        self._start_btn.setEnabled(False)
        self._cancel_btn.setVisible(True)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)

        self._run_workflow(nodes, edges)

    def _on_cancel(self):
        if self._executor:
            self._executor.cancel()
        self._on_reset()

    def _on_reset(self):
        self._running = False
        self._start_btn.setEnabled(True)
        self._cancel_btn.setVisible(False)
        self._progress_bar.setVisible(False)
        self._progress_bar.setValue(0)
        for node in list(self.canvas.get_nodes()):
            node.set_status("idle")

    def _run_workflow(self, nodes, edges):
        from app.services.ame_workflow.workflow_executor import AMEWorkflowExecutor
        self._executor = AMEWorkflowExecutor(nodes, edges)
        self._executor.progress_updated.connect(self._on_executor_progress)
        self._executor.node_status_changed.connect(self._on_node_status_changed)
        self._executor.finished.connect(self._on_workflow_finished)
        self._executor.error_occurred.connect(self._on_workflow_error)
        self._executor.start()

    def _on_executor_progress(self, value: int):
        self._progress_bar.setValue(value)

    def _on_node_status_changed(self, node_id: str, status: str):
        for node in self.canvas.get_nodes():
            if node.node_id() == node_id:
                node.set_status(status)
                break

    def _on_workflow_finished(self):
        self._running = False
        self._start_btn.setEnabled(True)
        self._cancel_btn.setVisible(False)
        if self._progress_bar.value() >= 100:
            InfoBar.success(
                title="处理完成",
                content="AME 工作流已执行完毕",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self,
            )

    def _on_workflow_error(self, error_msg: str):
        self._running = False
        self._start_btn.setEnabled(True)
        self._cancel_btn.setVisible(False)
        self._progress_bar.setVisible(False)
        InfoBar.error(
            title="工作流执行失败",
            content=error_msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=8000,
            parent=self,
        )
