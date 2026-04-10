# coding: utf-8
import os
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PySide6.QtCore import Qt

from qfluentwidgets import PushButton, ScrollArea, TitleLabel, FluentIcon as FIF
from qfluentwidgets import InfoBar, InfoBarPosition

from ..common.signal_bus import signalBus
from ..common.media_utils import classify_files
from ..common.style_sheet import StyleSheet
from ..components.task_card_interface import TaskCard
from ..services.recode.recode_worker import RecodeWorker


class TaskInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('TaskInterface')

        self.mainPage = QWidget()
        self.mainLayout = QVBoxLayout(self.mainPage)
        self.mainLayout.setContentsMargins(30, 30, 30, 20)
        self.mainLayout.setSpacing(0)

        self.task_cards = {}  # 存放所有任务卡片的字典 {task_id: TaskCard}
        self.workers = {}     # 保存后台工作线程 {task_id: RecodeWorker}

        self._hearderArea()
        self._progressArea()
        self._initLayout()
        self._initSignals()

    def _hearderArea(self):
        self.headerBox = QWidget(self)
        self.headerLayout = QVBoxLayout(self.headerBox)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)

        self.titleLabel = TitleLabel('任务进度', self)

        self.clearTaskBtn = PushButton(FIF.DELETE, '清除任务', self)

    def _progressArea(self):
        self.progressBox = QWidget(self)
        self.progressBox.setObjectName('ProgressBox')
        self.progressLayout = QVBoxLayout(self.progressBox)
        self.progressLayout.setContentsMargins(0, 0, 0, 0)

        self.progressArea = ScrollArea(self)
        self.progressArea.setWidget(self.progressBox)
        self.progressArea.setWidgetResizable(True)
        StyleSheet.TASK_INTERFACE.apply(self)

        self.progressLayout.addStretch(1)

    def _initLayout(self):
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addWidget(self.clearTaskBtn, alignment=Qt.AlignRight)

        # 进度区 Layout 由 progressLayout 完全接管，且添加了弹簧
        # self.progressBox.setLayout(self.progressLayout) 这一句不用重复写,上面 __init__(progressBox) 已经绑定

        self.mainLayout.addWidget(self.headerBox)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addWidget(self.progressArea)

        self.setLayout(self.mainLayout)

    def _initSignals(self):
        """ 绑定全局信号，监听来自其他页面或工作线程的消息 """
        signalBus.taskAdded.connect(self.on_task_added)
        signalBus.taskProgressUpdated.connect(self.on_task_progress_updated)
        signalBus.taskCompleted.connect(self.on_task_completed)
        signalBus.taskError.connect(self.on_task_error)
        signalBus.taskCancelled.connect(self.on_task_cancelled)
        
        self.clearTaskBtn.clicked.connect(self.clear_finished_tasks)

    def clear_finished_tasks(self):
        """清除已完成或抛错的废弃任务卡片, 避免挤占UI资源"""
        for task_id, card in list(self.task_cards.items()):
            if getattr(card, 'is_finished', False):
                # 从布局和视图树中卸载卡片并清空字典
                self.progressLayout.removeWidget(card)
                card.deleteLater()
                del self.task_cards[task_id]

    def on_task_added(self, payload: dict):
        """ 收到新任务包后实例化新的任务卡片 """
        task_id = payload.get("task_id")
        task_type = payload.get("type", "")
        files = payload.get("files", [])

        new_task_card = TaskCard(task_type, files, self)
        if files:
            file_category = classify_files([files[0]])
            if not file_category['video'] and not file_category['audio']:
                new_task_card.hide_fast_task_elements()

        new_task_card.stopTask.connect(lambda t_id=task_id: self.stop_running_task(t_id))
        new_task_card.openFolder.connect(lambda p=payload: self.open_output_folder(p))

        self.task_cards[task_id] = new_task_card # 先保管到字典里以便后续更新UI
        self.progressLayout.insertWidget(0, new_task_card) # 插入到最前面

        # 实例化后台任务线程 Worker，并将其保管，防止被垃圾回收
        # 注意：此处未来可做队列控制以限制同时并行的任务数，暂时直接 start 并行执行
        worker = RecodeWorker(payload, self)
        
        # 绑定的结束槽用于清理废弃资源
        worker.finished.connect(lambda t_id=task_id: self.on_worker_finished(t_id))
        
        self.workers[task_id] = worker
        worker.start() # start 后线程会执行 run() 方法，run() 内部会发出进度更新等信号被上面绑定的槽捕获并更新UI

    def stop_running_task(self, task_id: str):
        """中止具体后台进程"""
        if task_id in self.workers:
            self.workers[task_id].stop()
            # 用户选择立刻终止任务，发出全局中止信号
            signalBus.taskCancelled.emit(task_id)

    def on_task_cancelled(self, task_id: str):
        if task_id in self.task_cards:
            self.task_cards[task_id].mark_as_cancelled()
        
        InfoBar.warning(
            title='任务中止',
            content='你手动终止了正在执行的任务进程。',
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self.window()
        )

    def open_output_folder(self, payload: dict):
        """调用原生资源管理器打开设定的输出文件夹"""
        output_dir = payload.get("states", {}).get("output_state", {}).get("output_dir", "")
        files = payload.get("files", [])
        
        # 兜底：如果设置了“保存在源目录”未指定输出路径，解析第一个文件的目录
        try:
            if not output_dir and files:
                output_dir = str(Path(files[0]).parent)
            
            if output_dir and os.path.exists(output_dir):
                os.startfile(output_dir)
            else:
                InfoBar.warning('文件路径不存在', f'找不到输出路径: {output_dir}', parent=self.window())
        except Exception as e:
            print(f"打开文件夹失败: {e}")

    def on_worker_finished(self, task_id: str):
        """ 线程结束时自动回收其在内存中的资源 """
        if task_id in self.workers:
            del self.workers[task_id]

    def on_task_progress_updated(self, task_id: str, current_idx: int, total_files: int, filename: str, percent: float, time_left: str):
        """ 收到特定任务的进度更新并刷新对应卡片UI """
        if task_id in self.task_cards:
            self.task_cards[task_id].update_task_progress(current_idx, filename, percent, time_left)

    def on_task_completed(self, task_id: str):
        """ 任务完成后续处理 """
        if task_id in self.task_cards:
            card = self.task_cards[task_id]
            # 更新为 100% 并在UI展现完成状态
            # 修复 TypeError: current_idx 参数必须为 int，不能为 None
            card.update_task_progress(card.total_files, "全部完成", 100.0, "00:00:00")
            
        InfoBar.success(
            title='任务完成',
            content='你添加的任务已全部执行完毕！',
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=-1,
            parent=self.window()
        )

    def on_task_error(self, task_id: str, error_msg: str):
        """ 收到特定任务的异常报错 """
        if task_id in self.task_cards:
            self.task_cards[task_id].mark_as_error(error_msg)
        
        # 移除原先在此地的 InfoBar 弹窗逻辑，已统一交由 RecodeInterface 弹窗提醒。
                
        # 强制清理挂掉的 Worker 以阻断排队文件
        if task_id in self.workers:
            self.workers[task_id].stop()
