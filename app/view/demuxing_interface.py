from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog

from qfluentwidgets import FluentIcon as FIF

from ..components.hearder_widget import HeaderWidget
from ..components.demuxing_card_interface import InputFilesCard, MuxingOptionCard, OutputCard
from ..common.media_utils import DEMUXING_EXTS

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

        self._init_file_filter()
        self._connect_signals()

    def _init_file_filter(self):
        v_ext = "视频文件 (" + " ".join(f"*{ext}" for ext in DEMUXING_EXTS) + ")"
        all_ext = "所有文件 (*)"
        self.file_filter = f"{v_ext};;{all_ext}"

    def _connect_signals(self):
        self.header.reload_button.clicked.connect(self.open_file_dialog)
        self.inputFilesCard.load_files_requested.connect(self.open_file_dialog)

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择抽流文件", "", self.file_filter)
        if files:
            self.inputFilesCard.update_files(files)






