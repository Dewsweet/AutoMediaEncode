# coding: utf-8
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt

from qfluentwidgets import ExpandGroupSettingCard, SimpleExpandGroupSettingCard, ToolButton, ProgressBar, PushButton, BodyLabel, StrongBodyLabel, ScrollArea, TitleLabel, ToolTipFilter, CaptionLabel
from qfluentwidgets import FluentIcon as FIF

class SimpleProgressBarCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(90)

        self.cardLayout = QVBoxLayout(self)
        self.cardLayout.setContentsMargins(45, 10, 55, 10)
        
        self.processFileHLayout = QHBoxLayout()
        self.processBarHLayout = QHBoxLayout()
        self.processInfoHLayout = QHBoxLayout()

        self.fileTextLabel = BodyLabel('正在处理: ', self)
        self.fileNameLabel = BodyLabel('占位1.mp4', self)

        self.barTextLabel = BodyLabel('当前进度: ', self)
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)

        self.processTextLabel = CaptionLabel('任务进度: ', self)
        self.processingLabel = CaptionLabel('1 / 占位', self)

        self._initLayout()

    def _initLayout(self):
        self.processFileHLayout.addWidget(self.fileTextLabel)
        self.processFileHLayout.addWidget(self.fileNameLabel)
        self.processFileHLayout.addStretch(1)

        self.processBarHLayout.addWidget(self.barTextLabel)
        self.processBarHLayout.addWidget(self.progress_bar)

        self.processInfoHLayout.addWidget(self.processTextLabel)
        self.processInfoHLayout.addWidget(self.processingLabel)
        self.processInfoHLayout.addStretch(1)


        self.cardLayout.addLayout(self.processFileHLayout)
        self.cardLayout.addLayout(self.processBarHLayout)
        self.cardLayout.addLayout(self.processInfoHLayout)
        self.cardLayout.addStretch(1)

        self.setLayout(self.cardLayout)

    def update_progress(self, current_idx: int, total_files: int, filename: str, percent: float):
        self.processingLabel.setText(f'{current_idx} / {total_files}')
        self.fileNameLabel.setText(filename)
        self.progress_bar.setValue(int(percent))

class logCard(QWidget):
    pass
class ProgressBarCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(90)

        self.cardLayout = QVBoxLayout(self)
        self.cardLayout.setContentsMargins(45, 10, 55, 10)
        
        self.processFileHLayout = QHBoxLayout()
        self.processBarHLayout = QHBoxLayout()
        self.processInfoHLayout = QHBoxLayout()
        self.processInfo1HLayout = QHBoxLayout()
        self.processInfo2HLayout = QHBoxLayout()


        self.fileTextLabel = BodyLabel('正在处理: ', self)
        self.fileNameLabel = BodyLabel('占位1.mp4', self)

        self.barTextLabel = BodyLabel('当前进度: ', self)
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)

        self.processTextLabel = CaptionLabel('任务进度: ', self)
        self.processingLabel = CaptionLabel('1 / 占位', self)
        self.TimeTextLabel = CaptionLabel('预计剩余时间: ', self)
        self.TimeLabel = CaptionLabel('00:00:00', self)

        self._initLayout()

    def _initLayout(self):
        self.processFileHLayout.addWidget(self.fileTextLabel)
        self.processFileHLayout.addWidget(self.fileNameLabel)
        self.processFileHLayout.addStretch(1)

        self.processBarHLayout.addWidget(self.barTextLabel)
        self.processBarHLayout.addWidget(self.progress_bar)

        self.processInfo1HLayout.addWidget(self.processTextLabel)
        self.processInfo1HLayout.addWidget(self.processingLabel)
        self.processInfo2HLayout.addWidget(self.TimeTextLabel)
        self.processInfo2HLayout.addWidget(self.TimeLabel)

        self.processInfoHLayout.addLayout(self.processInfo1HLayout)
        self.processInfoHLayout.addSpacing(20)
        self.processInfoHLayout.addLayout(self.processInfo2HLayout)
        self.processInfoHLayout.addStretch(1)


        self.cardLayout.addLayout(self.processFileHLayout)
        self.cardLayout.addLayout(self.processBarHLayout)
        self.cardLayout.addLayout(self.processInfoHLayout)
        self.cardLayout.addStretch(1)
        self.cardLayout.setSpacing(5)

        self.setLayout(self.cardLayout)

    def update_progress(self, current_idx: int, total_files: int, filename: str, percent: float):
        self.processingLabel.setText(f'{current_idx} / {total_files}')
        self.fileNameLabel.setText(filename)
        self.progress_bar.setValue(int(percent))

    def update_time(self, time_str: str):
        self.TimeLabel.setText(time_str)


class TaskCardTemplate(ExpandGroupSettingCard):
    def __init__(self, ico, title: str, parent=None):
        super().__init__(ico, title, '点击查看详细进度', parent)

        self.hearderHBox = QWidget(self)
        self.hearderHBoxLayout = QHBoxLayout(self.hearderHBox)
        self.hearderHBoxLayout.setContentsMargins(0, 0, 0, 0)


        self.progessStateLabel = StrongBodyLabel('运行中: 0%', self) # 显示总进度 %

        self.title_stop_btn = ToolButton(FIF.PAUSE, self)
        self.title_stop_btn.setMaximumSize(36, 36)
        self.title_stop_btn.setToolTip('终止当前任务')
        self.title_stop_btn.installEventFilter(ToolTipFilter(self.title_stop_btn))

        self.title_path_btn = ToolButton(FIF.FOLDER, self)
        self.title_path_btn.setMaximumSize(36, 36)
        self.title_path_btn.setToolTip('打开输出目录')
        self.title_path_btn.installEventFilter(ToolTipFilter(self.title_path_btn))


        self.hearderHBoxLayout.addStretch(1)
        self.hearderHBoxLayout.addWidget(self.progessStateLabel)
        self.hearderHBoxLayout.addWidget(self.title_stop_btn)
        self.hearderHBoxLayout.addWidget(self.title_path_btn)
        self.hearderHBoxLayout.setSpacing(10)  

        self.addWidget(self.hearderHBox)

        self.taskGroup = ProgressBarCard(self)
        self.addGroupWidget(self.taskGroup)


class TaskCard(QWidget):
    def __init__(self, functionName: str, fileList: list, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        if functionName == 'Recondeing':
            self.task_card = TaskCardTemplate(FIF.VIDEO, '媒体重编码', self)
        elif functionName == 'Demuxing':
            self.task_card = TaskCardTemplate(FIF.MOVIE, '媒体抽流', self)
        elif functionName == 'Muxing':
            self.task_card = TaskCardTemplate(FIF.MEDIA, '媒体封装', self)
        elif functionName == 'AutoEncoding':
            self.task_card = TaskCardTemplate(FIF.TRAIN, 'AME', self)


        self.total_files = len(fileList)

        self.layout.addWidget(self.task_card)
        self.setLayout(self.layout)

    def update_task_progress(self, current_idx: int, filename: str, percent: float, time_left: str = "00:00:00"):
        """
        更新进度。
        :param current_idx: 当前正在处理第几个文件 (1-based)
        :param filename: 当前处理的文件名
        :param percent: 当前文件的处理进度 (0-100)
        :param time_left: 剩余预期时间
        """
        self.task_card.taskGroup.update_progress(current_idx, self.total_files, filename, percent)
        if hasattr(self.task_card.taskGroup, 'update_time'):
            self.task_card.taskGroup.update_time(time_left)

        # 计算并更新顶部的整体任务进度槽
        if self.total_files > 0:
            total_percent = ((current_idx - 1) * 100.0 + percent) / self.total_files
            if total_percent > 100:
                total_percent = 100.0
            self.task_card.progessStateLabel.setText(f'运行中: {total_percent:.1f}%')

        # 如果文件处理完了更新 Processing 的文本为 "任务完成"
        if current_idx >= self.total_files and percent >= 100:
            self.task_card.progessStateLabel.setText('任务完成: 100.0%') 
        else:
            pass

    def mark_as_error(self, error_msg: str):
        """任务出错强制终止UI样式更改"""
        self.task_card.progessStateLabel.setText('运行错误')
        self.task_card.progessStateLabel.setStyleSheet("color: red;")
        if hasattr(self.task_card.taskGroup, 'update_time'):
            self.task_card.taskGroup.update_time("中止")
        self.task_card.taskGroup.processingLabel.setText('已中止')

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    demo_files = ['video1.mp4', 'video2.mp4', 'video3.mp4']
    demo_card = TaskCard('Recondeing', demo_files)
    demo_card.show()
    sys.exit(app.exec())



