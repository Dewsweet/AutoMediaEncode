# coding: utf-8
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt

from qfluentwidgets import ExpandGroupSettingCard, SimpleExpandGroupSettingCard, ToolButton, ProgressBar, PushButton, BodyLabel, StrongBodyLabel, ScrollArea, TitleLabel
from qfluentwidgets import FluentIcon as FIF

from ..components.task_card_interface import TaskCard
from ..common.signal_bus import signalBus
from ..services.recode.recode_worker import RecodeWorker

class TaskInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('TaskInterface')

        self.mainPage = QWidget()
        self.mainLayout = QVBoxLayout(self.mainPage)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)
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
        self.progressBox.setStyleSheet("""background: transparent;""")
        self.progressLayout = QVBoxLayout(self.progressBox)
        self.progressLayout.setContentsMargins(0, 0, 0, 0)

        self.progressArea = ScrollArea(self)
        self.progressArea.setWidget(self.progressBox)
        self.progressArea.setWidgetResizable(True)
        self.progressArea.setStyleSheet("""QScrollArea { border: none; background: transparent; }""")

        # 为了保证任务卡片都在上方而不会自动平分撑开间距，添加一个弹簧在布局底部
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

    def on_task_added(self, payload: dict):
        """ 收到新任务包后实例化新的任务卡片 """
        task_id = payload.get("task_id")
        task_type = payload.get("type", "Recondeing")
        files = payload.get("files", [])

        # 创建新任务卡片并记录引用
        new_task_card = TaskCard(task_type, files, self)
        self.task_cards[task_id] = new_task_card

        # 插入到布局的最上方 (index=0), 将下面原有的卡片及底部占位弹簧往下挤
        self.progressLayout.insertWidget(0, new_task_card)

        # 实例化后台任务线程 Worker，并将其保管，防止被垃圾回收
        # 注意：此处未来可做队列控制以限制同时并行的任务数，暂时直接 start 并行执行
        worker = RecodeWorker(payload, self)
        
        # 绑定的结束槽用于清理废弃资源
        worker.finished.connect(lambda t_id=task_id: self.on_worker_finished(t_id))
        
        self.workers[task_id] = worker
        worker.start()

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
        pass

    def on_task_error(self, task_id: str, error_msg: str):
        """ 收到特定任务的异常报错 """
        if task_id in self.task_cards:
            self.task_cards[task_id].mark_as_error(error_msg)
        
        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.error(
            title='转换任务出错',
            content=error_msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=-1,  # 错误信息不要自动消失，-1 代表除非手动关闭
            parent=self
        )
