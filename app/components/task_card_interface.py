# coding: utf-8
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt

from qfluentwidgets import ExpandGroupSettingCard, SimpleExpandGroupSettingCard, ToolButton, ProgressBar, PushButton, BodyLabel, StrongBodyLabel, ScrollArea, TitleLabel, ToolTipFilter, CaptionLabel
from qfluentwidgets import FluentIcon as FIF

class SimpleProgressBarCard(QWidget):
    pass

class ProgressBarCard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)

        self.cardLayout = QHBoxLayout(self)
        self.cardLayout.setContentsMargins(45, 10, 55, 10)
        self.progessTextVLayout = QVBoxLayout()
        self.progessTimeVLayout = QVBoxLayout()

        self.processingTextLabel = BodyLabel('正在处理: ', self)
        self.fileNameLabel = BodyLabel('占位1.mp4', self)
        self.taskProcessTextLabel = CaptionLabel('任务进度: ', self)
        self.taskProcessingLabel = CaptionLabel('1 / 占位', self)

        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumWidth(200)

        self.ProgessTimeTextLabel = BodyLabel('预计剩余时间: ', self)
        self.progressTimeLabel = BodyLabel('00:00:00', self)

        self.progessTextVLayout.addWidget(self.taskProcessTextLabel)
        self.progessTextVLayout.addWidget(self.taskProcessingLabel)
        self.progessTextVLayout.addSpacing(10)
        self.progessTextVLayout.addWidget(self.processingTextLabel)
        self.progessTextVLayout.addWidget(self.fileNameLabel)

        self.progessTimeVLayout.addWidget(self.ProgessTimeTextLabel)
        self.progessTimeVLayout.addWidget(self.progressTimeLabel)

        self.cardLayout.addLayout(self.progessTextVLayout, stretch=1)
        # self.cardLayout.addSpacing(80)
        self.cardLayout.addWidget(self.progress_bar, stretch=0)
        # self.cardLayout.addSpacing(80)
        self.cardLayout.addLayout(self.progessTimeVLayout, stretch=1)


        self.setLayout(self.cardLayout)

    def update_progress(self, current_idx: int, total_files: int, filename: str, percent: float):
        self.taskProcessingLabel.setText(f'{current_idx} / {total_files}')
        self.fileNameLabel.setText(filename)
        self.progress_bar.setValue(int(percent))

    def update_time(self, time_str: str):
        self.progressTimeLabel.setText(time_str)


class TaskCardTemplate(ExpandGroupSettingCard):
    def __init__(self, ico, title: str, subtitle: str, parent=None):
        super().__init__(ico, title, subtitle, parent)


        self.title_stop_btn = ToolButton(FIF.PAUSE, self)
        self.title_stop_btn.setToolTip('终止当前任务')
        self.title_stop_btn.installEventFilter(ToolTipFilter(self.title_stop_btn))
        self.title_path_btn = ToolButton(FIF.FOLDER, self)
        self.title_path_btn.setToolTip('打开输出目录')
        self.title_path_btn.installEventFilter(ToolTipFilter(self.title_path_btn))

        self.addWidget(self.title_stop_btn)
        self.addWidget(self.title_path_btn)

        self.groupTaskTemplate = ProgressBarCard(self)
        self.addGroupWidget(self.groupTaskTemplate)




class TaskCard(QWidget):
    def __init__(self, functionName: str, fileList: list, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)


        Processing = str(f"任务进度 1 / {len(fileList)}")

        if functionName == 'Recondeing':
            self.task_card = TaskCardTemplate(FIF.VIDEO, '媒体重编码', '点击卡片查看进度', self)
        elif functionName == 'Demuxing':
            self.task_card = TaskCardTemplate(FIF.MOVIE, '媒体抽流', '点击卡片查看进度', self)
        elif functionName == 'Muxing':
            self.task_card = TaskCardTemplate(FIF.MEDIA, '媒体封装', '点击卡片查看进度', self)
        elif functionName == 'AutoEncoding':
            self.task_card = TaskCardTemplate(FIF.TRAIN, 'AME', '点击卡片查看进度', self)


        self.total_files = len(fileList)

        self.layout.addWidget(self.task_card)
        self.setLayout(self.layout)

    def update_task_progress(self, current_idx: int, filename: str, percent: float):
        """
        更新进度。
        :param current_idx: 当前正在处理第几个文件 (1-based)
        :param filename: 当前处理的文件名
        :param percent: 当前文件的处理进度 (0-100)
        """
        self.task_card.groupTaskTemplate.update_progress(current_idx, self.total_files, filename, percent)

        # 如果文件处理完了更新 Processing 的文本为 "任务完成"
        if current_idx >= self.total_files and percent >= 100:
            self.task_card.groupTaskTemplate.processingTextLabel.setText('任务已完成')
            self.task_card.groupTaskTemplate.taskProcessTextLabel.setText('处理结束')
        else:
            pass



