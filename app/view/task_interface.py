from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt

from qfluentwidgets import ExpandGroupSettingCard, SimpleExpandGroupSettingCard, ToolButton, ProgressBar, PushButton, BodyLabel, StrongBodyLabel, ScrollArea, TitleLabel
from qfluentwidgets import FluentIcon as FIF


class GroupTaskTemplate(QWidget):
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(60)
        self.templateLayout = QHBoxLayout(self)
        self.templateLayout.setContentsMargins(50, 10, 55, 10)

        self.handNameLabel = BodyLabel(filename, self)

        self.hand_progress_bar = ProgressBar(self)
        self.hand_progress_bar.setRange(0, 100)
        self.hand_progress_bar.setValue(0)
        self.hand_progress_bar.setMinimumWidth(200)

        self.hand_progress_label = BodyLabel('0%', self)
        # hand_State_Label = BodyLabel('正在运行', self)

        self.templateLayout.addWidget(self.handNameLabel)
        self.templateLayout.addSpacing(80)
        self.templateLayout.addWidget(self.hand_progress_bar)
        self.templateLayout.addSpacing(80)
        self.templateLayout.addWidget(self.hand_progress_label)

        self.setLayout(self.templateLayout)

class TaskCardTemplate(SimpleExpandGroupSettingCard):
    def __init__(self, ico, title: str, subtitle: str, parent=None):
        super().__init__(ico, title, subtitle, parent)


        self.title_stop_btn = ToolButton(FIF.PAUSE, self)
        self.title_path_btn = ToolButton(FIF.FOLDER, self)
        self.title_state_label = BodyLabel('正在运行', self)

        self.addWidget(self.title_state_label)
        self.addWidget(self.title_stop_btn)
        self.addWidget(self.title_path_btn)

        self.rows = []
    def addGroupTask(self, filename: str):
        self.groupTaskTemplate = GroupTaskTemplate(filename, self)
        self.rows.append(self.groupTaskTemplate)

        self.addGroupWidget(self.groupTaskTemplate)

    def addMoreSymbol(self):
        self.dotBox = QWidget(self)
        self.dotLayout = QHBoxLayout(self.dotBox)
        self.dotLayout.setContentsMargins(50, 10, 55, 10)
        self.dotLabel = BodyLabel('...', self)
        self.dotLayout.addWidget(self.dotLabel)
        self.addGroupWidget(self.dotBox)


class TaskCard(QWidget):
    def __init__(self, functionName: str, fileList: list, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)


        task_text = str(f"任务进度 1 / {len(fileList)}")

        if functionName == 'Recondeing':
            self.task_card = TaskCardTemplate(FIF.VIDEO, '媒体重编码', task_text, self)
        elif functionName == 'Demuxing':
            self.task_card = TaskCardTemplate(FIF.MOVIE, '媒体抽流', task_text, self)
        elif functionName == 'Muxing':
            self.task_card = TaskCardTemplate(FIF.MEDIA, '媒体封装', task_text, self)
        elif functionName == 'AutoEncoding':
            self.task_card = TaskCardTemplate(FIF.TRAIN, 'AME', task_text, self)

        # 如果 传入的文件列表长度超过 4，则只显示前 4 个文件，并添加一个“...”的占位符
        if len(fileList) > 4:
            for i in range(4):
                self.task_card.addGroupTask(fileList[i])
            self.task_card.addMoreSymbol()


        self.layout.addWidget(self.task_card)
        self.setLayout(self.layout)



class TaskInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('TaskInterface')

        self.view = QWidget(self)
        self.layout = QVBoxLayout(self.view)
        self.layout.setContentsMargins(20, 20, 20, 20)

        self.setWidget(self.view) # 设置滚动区域的内容部件
        self.setWidgetResizable(True) # 使内容部件随滚动区域大小调整


        fileList_test = ['文件1.mp4', '文件2.mp4', '文件3.mp4', '文件4.mp4', '文件5.mp4, 文件6.mp4']

        self.titleLabel = TitleLabel('任务进度', self.view)
        self.task = TaskCard('Recondeing', fileList_test, self.view)

        self.layout.addWidget(self.titleLabel)
        self.layout.addSpacing(20)
        self.layout.addWidget(self.task)
        self.layout.addStretch()

        self.setStyleSheet("""QScrollArea { border: none; background: transparent; }""")
        self.view.setStyleSheet("""background: transparent;""")


