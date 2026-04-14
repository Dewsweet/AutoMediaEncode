from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import FluentIcon as FIF

from ..components.hearder_widget import HeaderWidget
from ..components.demuxing_card_interface import InputFilesCard, MuxingOptionCard, OutputCard

class DemuxingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('MuxingInterface')

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)

        self.Hbox = QWidget(self)
        self.HboxLayout = QHBoxLayout(self.Hbox)

        self.header = HeaderWidget('媒体抽流', '从视频文件中提取各种音频、视频、字幕流……', '开始抽流', self)
        self.inputFilesCard = InputFilesCard(self)
        self.optionCard = MuxingOptionCard(self)
        self.outputCard = OutputCard(self)

        self.HboxLayout.addWidget(self.inputFilesCard, 7)
        self.HboxLayout.addWidget(self.optionCard, 3)
        self.HboxLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addWidget(self.header, alignment=Qt.AlignTop)
        self.mainLayout.addWidget(self.Hbox)
        self.mainLayout.addWidget(self.outputCard, alignment=Qt.AlignBottom)






