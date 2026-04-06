# coding: utf-8
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt

from qfluentwidgets import ExpandGroupSettingCard, SimpleExpandGroupSettingCard, ToolButton, ProgressBar, PushButton, BodyLabel, StrongBodyLabel, ScrollArea, TitleLabel
from qfluentwidgets import FluentIcon as FIF

from ..components.task_card_interface import TaskCard

class TaskInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('TaskInterface')

        self.mainPage = QWidget()
        self.mainLayout = QVBoxLayout(self.mainPage)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)
        self.mainLayout.setSpacing(0)

        self._hearderArea()
        self._progressArea()
        self._initLayout()

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


        fileList_test = ['文件1.mp4', '文件2.mp4', '文件3.mp4', '文件4.mp4', '文件5.mp4, 文件6.mp4']

        self.task = TaskCard('Recondeing', fileList_test, self)

        # 模拟正在处理第2个文件，进度到达 45.6%
        self.task.update_task_progress(current_idx=2, filename=fileList_test[1], percent=45.6)


    def _initLayout(self):
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addWidget(self.clearTaskBtn, alignment=Qt.AlignRight)

        self.progressLayout.addWidget(self.task)
        self.progressBox.setLayout(self.progressLayout)

        self.mainLayout.addWidget(self.headerBox)
        self.mainLayout.addSpacing(20)
        self.mainLayout.addWidget(self.progressArea)

        self.setLayout(self.mainLayout)
