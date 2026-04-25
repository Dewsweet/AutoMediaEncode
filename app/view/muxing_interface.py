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
        
        self.trackCard.trackSelectionUpdated.connect(self._handle_track_selection_changed)
        self.optionCard.optionValueChanged.connect(self._handle_option_value_changed)

    def _handle_track_selection_changed(self, row: int):
        if row == -1:
            self.optionCard.set_track_selected_state(False)
            return

        data = self.trackCard.get_track_data(row)
        if data:
            enabled, name, language, is_default, flags = data
            self.optionCard.set_track_selected_state(True)
            self.optionCard.update_from_track(enabled, name, language, is_default, flags)

    def _handle_option_value_changed(self, key: str, value: object):
        # 将 OptionCard 发出的修改，应用到当前选中的轨道上
        # 因为我们允许多选但这里主要针对触发联动的最后一行。如果需要修改所有选中行，可以获取所有选中行
        selected_items = self.trackCard.table.selectedItems()
        if not selected_items:
            return
            
        selected_rows = set(item.row() for item in selected_items)
        for row in selected_rows:
            self.trackCard.set_track_data(row, key, value)

    def _handle_files_added(self, file_paths: list):
        for path in file_paths:
            # TODO: 后续改为子线程中调用，防界面卡顿。先直接调用
            file_info = MuxProbeService.probe_file(path)
            if file_info:
                # 把基础信息发给列表展示
                color_emoji = self.inputFilesCard.add_file_to_table(file_info)
                if color_emoji:
                    # 下一步就是把这个 file_info 数据传递给 self.trackCard 去解析轨道信息
                    self.trackCard.add_tracks(file_info, color_emoji)
                    
                    # 附件区域
                    attachments = file_info.get('attachments', [])
                    if attachments:
                        self.attachmentCard.add_attachments(file_info['path'], attachments)

    def _handle_files_removed(self, paths: list):
        # 从 TrackCard 中移除属于这些文件的轨道信息
        for path in paths:
            self.trackCard.remove_tracks_by_file(path)
            self.attachmentCard.remove_attachments_by_file(path)
        
    def _handle_files_cleared(self):
        # 清空整个 TrackCard 的子轨道
        self.trackCard.clear_all_tracks()
        self.attachmentCard.clear_all_attachments()

