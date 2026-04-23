# coding: utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter

from qfluentwidgets import qrouter, StrongBodyLabel

from ..components.muxing_card_interface import InputFilesCard, TrackCard, OptionCard, OutputCard, AttachmentCard
from ..components.hearder_widget import HeaderWidget
from ..services.muxing.mux_probe_service import MuxProbeService

class MuxingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MuxingInterface")

        self.mainPage = QWidget()
        self.mainPage.setObjectName('mainPage')
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)

        self._initWidget()
        self._initLayout()

    def _initWidget(self):
        self.header = HeaderWidget('媒体混流', '对各种媒体工具进行混流, 封装成媒体文件', '开始混流', self)

        self.inputFilesCard = InputFilesCard(self)
        self.trackCard = TrackCard(self)
        self.optionCard = OptionCard(self)
        self.outputCard = OutputCard(self)
        self.attachmentCard = AttachmentCard(self)
        self.attachmentCard.hide()

    def _initLayout(self):
        self.leftSplitter = QSplitter(Qt.Vertical)
        self.leftSplitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")
        self.leftSplitter.addWidget(self.inputFilesCard)
        self.leftSplitter.addWidget(self.trackCard)
        self.leftSplitter.setHandleWidth(5)
        self.leftSplitter.setChildrenCollapsible(False) 
        self.leftSplitter.setStretchFactor(0, 5) 
        self.leftSplitter.setStretchFactor(1, 5)

        self.mainSplitter = QSplitter(Qt.Horizontal)
        self.mainSplitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")
        self.mainSplitter.addWidget(self.leftSplitter)
        self.mainSplitter.addWidget(self.optionCard)
        self.mainSplitter.setHandleWidth(5)
        self.mainSplitter.setChildrenCollapsible(False)
        self.mainSplitter.setStretchFactor(0, 2)
        self.mainSplitter.setStretchFactor(1, 1)

        self.contentSplitter = QSplitter(Qt.Vertical)
        self.contentSplitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")
        self.contentSplitter.addWidget(self.mainSplitter)
        self.contentSplitter.addWidget(self.attachmentCard)
        self.contentSplitter.setHandleWidth(5)
        self.contentSplitter.setChildrenCollapsible(False)

        self.mainLayout.addWidget(self.header, alignment=Qt.AlignTop)
        self.mainLayout.addWidget(self.contentSplitter, 1)
        self.mainLayout.addWidget(self.outputCard, alignment=Qt.AlignBottom)
        # self.setLayout(self.mainLayout)

        self._connect_signals()

    def _connect_signals(self):
        self.inputFilesCard.filesAdded.connect(self._handle_files_added)
        self.inputFilesCard.removeFilesRequested.connect(self._handle_files_removed)
        self.inputFilesCard.clearFilesRequested.connect(self._handle_files_cleared)
        
        self.optionCard.enable_attachment_checkbox.stateChanged.connect(
            lambda state: self.attachmentCard.setVisible(state == Qt.CheckState.Checked.value)
        )

    def _handle_files_added(self, file_paths: list):
        for path in file_paths:
            # TODO: 后续改为子线程中调用，防界面卡顿。先直接调用
            file_info = MuxProbeService.probe_file(path)
            if file_info:
                # 把基础信息发给列表展示
                self.inputFilesCard.add_file_to_table(file_info)
                
                # TODO: 下一步就是把这个 file_info 数据传递给 self.trackCard 去解析轨道信息

    def _handle_files_removed(self, paths: list):
        print("Mux Interface remove: ", paths)
        # TODO: 从 TrackCard 中移除属于这些文件的轨道信息
        
    def _handle_files_cleared(self):
        print("Mux Interface cleared.")
        # TODO: 清空整个 TrackCard 的子轨道

