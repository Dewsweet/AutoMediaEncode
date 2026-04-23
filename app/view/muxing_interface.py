# coding: utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import qrouter, StrongBodyLabel

from ..components.muxing_card_interface import InputFilesCard, TrackCard, OptionCard, OutputCard
from ..components.hearder_widget import HeaderWidget
#from ..components.fileload_interface import FileLoadInterface

class MuxingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MuxingInterface")

        self.mainPage = QWidget()
        self.mainPage.setObjectName('mainPage')
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)

        self.vLayout1 = QVBoxLayout()
        self.vLayout1.setContentsMargins(0, 0, 0, 0)

        self.vLayout2 = QVBoxLayout()
        self.vLayout2.setContentsMargins(0, 0, 0, 0)

        self.hLayout = QHBoxLayout()
        self.hLayout.setContentsMargins(0, 0, 0, 0)

        self._initWidget()
        self._initLayout()

    def _initWidget(self):
        self.header = HeaderWidget('媒体混流', '对各种媒体工具进行混流, 封装成媒体文件', '开始混流', self)

        self.inputFilesCard = InputFilesCard(self)
        self.trackCard = TrackCard(self)
        self.optionCard = OptionCard(self)
        self.outputCard = OutputCard(self)

    def _initLayout(self):
        self.vLayout1.addWidget(self.inputFilesCard)
        self.vLayout1.addWidget(self.trackCard)

        self.vLayout2.addWidget(self.optionCard)

        self.hLayout.addLayout(self.vLayout1, 6)
        self.hLayout.addLayout(self.vLayout2, 4)

        self.mainLayout.addWidget(self.header, alignment=Qt.AlignTop)
        self.mainLayout.addLayout(self.hLayout)
        self.mainLayout.addWidget(self.outputCard, alignment=Qt.AlignBottom)
        # self.setLayout(self.mainLayout)

