from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QFileDialog
from PySide6.QtGui import QShortcut, QKeySequence

from qfluentwidgets import (ProgressBar, InfoBar, InfoBarPosition)

from NodeGraphQt.qgraphics.node_abstract import AbstractNodeItem

from app.components.ame_workflow.ame_graph import AMEGraph
from app.components.ame_workflow.floating_toolbar import FloatingToolbar
from app.components.ame_workflow.nodes import MENU_KEY_MAP
from app.components.ame_workflow.ame_context_menu import AMEConextMenu, AMENodeContextMenu
from app.components.ame_workflow.ame_loader_page import AMELoaderPage, NameInputDialog
from app.services.ame_workflow.ame_preset_service import preset_service
from app.common.signal_bus import signalBus
from app.common.style_sheet import StyleSheet


class AMEWorkflowInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AMEWorkflowInterface')

        self._ame_graph = AMEGraph(self)
        self._toolbar = FloatingToolbar(self)
        self._progress = ProgressBar(self)
        self._palette = AMEConextMenu(self._ame_graph.graph, self)
        self._node_menu = AMENodeContextMenu(self._ame_graph.graph, self)
        self._loader = AMELoaderPage(self)

        self._executor = None
        self._running = False
        self._cancelling = False
        self._shutting_down = False
        self._workflow_error = ''
        self._other_tasks = set()
        self._current_workflow_name = None
        self._current_workflow_saved = False
        self._suggested_workflow_name = ''

        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(6)

        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._loader)
        self._stack.addWidget(self._ame_graph.widget())
        self._stack.setCurrentIndex(0)

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.addWidget(self._stack)

        self._toolbar.setVisible(False)

        self._setup_signals()
        StyleSheet.AME_WORKFLOW_INTERFACE.apply(self)
        self._loader.load()

    def _setup_signals(self):
        g = self._ame_graph.graph
        g.node_selected.connect(lambda n: None)

        viewer = self._ame_graph.viewer()
        if viewer:
            viewer.customContextMenuRequested.connect(self._on_viewer_menu)
            self._save_shortcut = QShortcut(QKeySequence('Ctrl+S'), self, activated=self._on_save)
            self._save_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
            # QShortcut(QKeySequence('Ctrl+O'), viewer, activated=self._on_back_to_loader)

        self._toolbar.start_clicked.connect(self._on_start)
        self._toolbar.pause_clicked.connect(self._on_pause)
        self._toolbar.cancel_clicked.connect(self._on_cancel)
        self._toolbar.save_clicked.connect(self._on_export_json)
        self._toolbar.load_clicked.connect(self._on_import_json)
        self._toolbar.back_clicked.connect(self._on_back_to_loader)

        self._palette.save_clicked.connect(self._on_save)
        # self._palette.load_clicked.connect(self._on_back_to_loader)
        self._palette.node_selected.connect(self._on_palette_node)
        self._palette.export_clicked.connect(self._on_export_json)
        self._palette.import_clicked.connect(self._on_import_json)
        self._palette.add_group_clicked.connect(self._on_add_group)

        self._loader.workflow_selected.connect(self._on_load_workflow)
        self._loader.new_requested.connect(self._on_new_workflow)

        # 全局任务互斥: 其他界面任务运行时锁定/解锁自家开始按钮
        signalBus.taskExecutionStarted.connect(self._on_global_task_started)
        signalBus.taskExecutionEnded.connect(self._on_global_task_ended)

    # ── 页面切换 ──
    def _switch_to_canvas(self):
        self._stack.setCurrentIndex(1)
        self._toolbar.setVisible(True)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._toolbar.raise_()
        self._progress.raise_()
        self._reposition_overlays()

    def _switch_to_loader(self):
        self._stack.setCurrentIndex(0)
        self._toolbar.setVisible(False)
        self._toolbar.close_expand()
        self._progress.setVisible(False)
        self._loader.load()

    def _on_back_to_loader(self):
        self._switch_to_loader()

    def _file_error(self, title, error):
        InfoBar.error(title=title, content=str(error), orient=Qt.Horizontal,
                      isClosable=True, position=InfoBarPosition.TOP,
                      duration=8000, parent=self)

    def _can_replace_canvas(self):
        if self._running or (self._executor and self._executor.isRunning()):
            InfoBar.warning(title=self.tr('任务正在运行'),
                            content=self.tr('请等待任务结束后再替换工作流'),
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=3000, parent=self)
            return False
        return True

    # ── 新建 ──
    def _on_new_workflow(self):
        if not self._can_replace_canvas():
            return
        dlg = NameInputDialog(self.tr('新建工作流'), self.tr('输入工作流名称:'), self.window())
        if dlg.exec():
            name = dlg.get_text().strip()
            if name:
                try:
                    preset_service.validate_name(name)
                    if preset_service.exists(name):
                        raise FileExistsError(self.tr('同名工作流已存在，请使用其他名称'))
                except Exception as error:
                    self._file_error(self.tr('新建失败'), error)
                    return
                self._current_workflow_name = name
                self._current_workflow_saved = False
                self._suggested_workflow_name = ''
                self._ame_graph.graph.clear_session()
                self._ame_graph.setup_default_nodes()
                self._switch_to_canvas()

    # ── 加载 ──
    def _on_load_workflow(self, name: str):
        if not self._can_replace_canvas():
            return
        try:
            if not preset_service.load(name, self._ame_graph.graph):
                raise FileNotFoundError(self.tr('工作流文件不存在'))
            self._current_workflow_name = name
            self._current_workflow_saved = True
            self._suggested_workflow_name = ''
            self._ame_graph._fix_all_node_views()
            self._switch_to_canvas()
        except Exception as error:
            self._file_error(self.tr('加载失败'), error)

    # ── 保存 ──
    def _on_save(self):
        """保存当前工作流，如果之前已保存过则覆盖，否则提示输入名称"""
        if self._stack.currentIndex() != 1:
            return
        name = self._current_workflow_name
        if not name:
            dlg = NameInputDialog(self.tr('保存工作流'), self.tr('输入名称:'), self.window())
            dlg._edit.setText(self._suggested_workflow_name)
            if not dlg.exec():
                return
            name = dlg.get_text().strip()
        try:
            preset_service.save_with_thumbnail(
                name, self._ame_graph.graph, overwrite=self._current_workflow_saved)
        except Exception as error:
            self._file_error(self.tr('保存失败'), error)
            return
        self._current_workflow_name = name
        self._current_workflow_saved = True
        self._suggested_workflow_name = ''
        InfoBar.success(title=self.tr('已保存'), content=self.tr('保存到: {name}').format(name=name),
                        orient=Qt.Horizontal, isClosable=True,
                        position=InfoBarPosition.TOP, duration=2000, parent=self)

    # ── 导入/导出 JSON ──
    def _on_import_json(self):
        if not self._can_replace_canvas():
            return
        path, _ = QFileDialog.getOpenFileName(self, self.tr('导入 JSON'), "", "JSON (*.json)")
        if path:
            try:
                self._ame_graph.load_session(path)
            except Exception as error:
                self._file_error(self.tr('导入失败'), error)
                return
            self._current_workflow_name = None
            self._current_workflow_saved = False
            self._suggested_workflow_name = Path(path).stem
            self._ame_graph.graph.model.session = ''
            self._switch_to_canvas()
            InfoBar.success(title=self.tr('已导入'), content=self.tr('导入完成'),
                                orient=Qt.Horizontal, isClosable=False,
                                position=InfoBarPosition.TOP, duration=2000, parent=self)

    def _on_export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, self.tr('导出 JSON'), "", "JSON (*.json)")
        if path:
            try:
                self._ame_graph.save_session(path)
            except Exception as error:
                self._file_error(self.tr('导出失败'), error)
                return
            InfoBar.success(title=self.tr('已导出'), content=self.tr('导出完成'),
                            orient=Qt.Horizontal, isClosable=False,
                            position=InfoBarPosition.TOP, duration=2000, parent=self)

    # ── 右键菜单 ──
    def _find_node_at(self, scene_pos):
        """检测场景位置下是否有节点，返回 NodeObject 或 None"""
        rect = QRectF(scene_pos.x() - 10, scene_pos.y() - 10, 20, 20)
        viewer = self._ame_graph.viewer()
        if not viewer:
            return None
        for item in viewer.scene().items(rect):
            if isinstance(item, AbstractNodeItem):
                return self._ame_graph.graph.get_node_by_id(item.id)
        return None

    def _on_viewer_menu(self, pos):
        viewer = self._ame_graph.viewer()
        scene_pos = viewer.mapToScene(pos)
        global_pos = viewer.mapToGlobal(pos)

        node = self._find_node_at(scene_pos)
        if node:
            self._ame_graph.graph.clear_selection()
            node.set_selected(True)
            self._node_menu.exec(global_pos)
        else:
            self._palette.set_scene_pos(scene_pos)
            self._palette.exec(global_pos)

    def _on_add_group(self):
        g = self._ame_graph.graph
        cur = g.cursor_pos()
        backdrop = g.create_node('nodeGraphQt.nodes.BackdropNode',
                                 name=self.tr('组'), pos=[cur[0], cur[1]], push_undo=False)
        selected = g.selected_nodes()
        if selected:
            backdrop.wrap_nodes(selected)

    def _on_palette_node(self, menu_key, _):
        if menu_key == 'vs_compound':
            cur = self._ame_graph.graph.cursor_pos()
            vpy = self._ame_graph.create_node('ame.VPYLoaderNode', pos=[cur[0], cur[1]])
            vsp = self._ame_graph.create_node('ame.VSPipeNode', pos=[cur[0] + 25, cur[1] + 200])
            vpy.set_output(0, vsp.input(0))
            return
        cls = MENU_KEY_MAP.get(menu_key)
        if not cls:
            return
        tn = f'ame.{cls.__name__}'
        cur = self._ame_graph.graph.cursor_pos()
        self._ame_graph.create_node(tn, pos=[cur[0], cur[1]])

    def _on_start(self):
        if self._shutting_down or self._other_tasks:
            return
        if self._executor:
            if self._running and not self._cancelling and self._executor.isRunning():
                self._executor.resume()
                self._toolbar.set_state('running')
            return
        out_cls = self._find_output_class()
        nodes = self._ame_graph.all_nodes()
        output_count = sum(isinstance(node, out_cls) for node in nodes)
        if output_count > 1:
            InfoBar.warning(title=self.tr('输出节点过多'),
                            content=self.tr('工作流仅支持一个输出节点，请仅保留一个输出节点'),
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=5000, parent=self)
            return
        if any(getattr(node, '_probe_threads', []) for node in nodes):
            InfoBar.warning(title=self.tr('输入文件正在探测'),
                            content=self.tr('请等待轨道探测完成后再开始任务'),
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=3000, parent=self)
            return
        if output_count == 0:
            InfoBar.warning(title=self.tr('工作流不完整'), content=self.tr('请至少添加一个输出节点'),
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=3000, parent=self)
            return
        self._running = True
        self._cancelling = False
        self._workflow_error = ''
        self._ame_graph.viewer().setEnabled(False)
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
        self._executor = AMEWorkflowExecutor(nodes, edges, self)
        self._executor.progress_updated.connect(self._on_progress)
        self._executor.node_status_changed.connect(self._on_node_status)
        self._executor.finished.connect(self._on_finished)
        self._executor.error_occurred.connect(self._on_error)
        # 通知所有界面: 工作流任务进入执行状态, 其他界面的开始按钮需禁用
        signalBus.taskExecutionStarted.emit('ame_workflow')
        self._executor.start()

    def _on_cancel(self):
        if self._executor and self._running and not self._cancelling:
            self._cancelling = True
            self._toolbar.set_state('cancelling')
            self._executor.cancel()

    def _on_pause(self):
        if self._executor and self._running and not self._cancelling:
            self._executor.pause()
            self._toolbar.set_state('paused')

    def _reset_ui(self):
        self._running = False
        self._cancelling = False
        self._toolbar.set_state('idle')
        self._toolbar.set_locked(bool(self._other_tasks))
        self._ame_graph.viewer().setEnabled(True)
        self._progress.setVisible(False)
        self._progress.setValue(0)

    def _on_progress(self, value):
        if self.sender() is self._executor and not self._cancelling:
            self._progress.setValue(value)

    def _on_node_status(self, node_id: str, status: str):
        if self.sender() is not self._executor or self._shutting_down:
            return
        node = self._ame_graph.get_node_by_id(node_id)
        if node and hasattr(node, 'set_status'):
            node.set_status(status)

    def _on_finished(self):
        self._finish_executor(self.sender())

    def _finish_executor(self, executor):
        if executor is None or executor is not self._executor:
            return
        cancelled = self._cancelling or executor._cancelled
        succeeded = executor.succeeded and not cancelled and not self._workflow_error
        error = self._workflow_error
        self._executor = None
        self._reset_ui()
        executor.deleteLater()
        signalBus.taskExecutionEnded.emit('ame_workflow')
        if self._shutting_down:
            return
        if error and not cancelled:
            InfoBar.error(title=self.tr('工作流执行失败'), content=error,
                          orient=Qt.Horizontal, isClosable=True,
                          position=InfoBarPosition.TOP, duration=15000, parent=self)
        elif succeeded:
            self._progress.setValue(100)
            self._progress.setVisible(True)
            InfoBar.success(title=self.tr('处理完成'), content=self.tr('AME 工作流已执行完毕'),
                            orient=Qt.Horizontal, isClosable=True,
                            position=InfoBarPosition.TOP, duration=5000, parent=self)

    def _on_error(self, msg):
        if self.sender() is self._executor:
            self._workflow_error = msg

    def _on_global_task_started(self, task_id: str):
        """其他界面的任务开始执行时, 锁定工作流工具栏开始按钮(全局任务互斥)"""
        if task_id != 'ame_workflow':
            self._other_tasks.add(task_id)
            self._toolbar.set_locked(True)

    def _on_global_task_ended(self, task_id: str):
        """全局任务结束后解锁工作流工具栏开始按钮(按当前状态恢复, 幂等)"""
        self._other_tasks.discard(task_id)
        self._toolbar.set_locked(bool(self._other_tasks))

    def shutdown(self):
        if self._shutting_down:
            return
        self._shutting_down = True
        executor = self._executor
        if executor:
            self._on_cancel()
        from app.components.ame_workflow.nodes.io.input_bd_normalizer_node import shutdown_probes
        shutdown_probes()
        if executor:
            executor.wait()
            self._finish_executor(executor)

    def _find_output_class(self):
        from app.components.ame_workflow.nodes.io.output_node import OutputNode
        return OutputNode

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_overlays()

    def _reposition_overlays(self):
        if self._stack.currentIndex() == 1:
            w, h = self.width(), self.height()
            self._toolbar.move(20, 12)
            self._progress.setGeometry(0, h - 6, w, 6)
            self._toolbar.raise_()
            self._progress.raise_()
