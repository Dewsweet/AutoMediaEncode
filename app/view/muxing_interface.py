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
        self.trackCard.table.itemChanged.connect(self._handle_track_item_changed)
        self.optionCard.optionValueChanged.connect(self._handle_option_value_changed)

    def _handle_track_item_changed(self, item):
        # 只有第一列的状态改变，才会影响后缀推断
        if item.column() == 0:
            self._update_output_path()

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
        
        self._update_output_path()

    def _handle_files_removed(self, paths: list):
        # 从 TrackCard 中移除属于这些文件的轨道信息
        for path in paths:
            self.trackCard.remove_tracks_by_file(path)
            self.attachmentCard.remove_attachments_by_file(path)
        self._update_output_path()

    def _update_output_path(self):
        # 依据加载进去的第一个文件为准，如果没有文件就清空
        if self.inputFilesCard.table.rowCount() == 0:
            self.outputCard.output_path_lineEdit.clear()
            return
        
        # 获取第一个文件的路径
        first_file_item = self.inputFilesCard.table.item(0, 3)
        if not first_file_item:
            return
            
        first_file_path = first_file_item.text()
        
        # 解析当前的轨道类型
        has_video = False
        has_audio = False
        has_subtitle = False
        
        for row in range(self.trackCard.table.rowCount()):
            codec_item = self.trackCard.table.item(row, 0)
            type_item = self.trackCard.table.item(row, 1)
            
            # 判断是否启用该轨道
            if codec_item and codec_item.checkState() == Qt.Checked:
                t_type = type_item.text() if type_item else ''
                if '视频' in t_type:
                    has_video = True
                elif '音频' in t_type:
                    has_audio = True
                elif '字幕' in t_type:
                    has_subtitle = True
        
        # 后缀判定: 默认 mkv。除非仅有音频那就是 mka，或者仅有字幕那就是 mks。
        ext = '.mkv'
        if not has_video:
            if has_audio and not has_subtitle:
                ext = '.mka'
            elif has_subtitle and not has_audio:
                ext = '.mks'
                
        import os
        base_path = os.path.splitext(first_file_path)[0]
        
        # 为了避免跟原文件同名，加一个 "_muxed" 尾缀
        default_out = f"{base_path}_muxed{ext}"
        self.outputCard.output_path_lineEdit.setText(default_out)
        
    def _handle_files_cleared(self):
        # 清空整个 TrackCard 的子轨道
        self.trackCard.clear_all_tracks()
        self.attachmentCard.clear_all_attachments()
        self._update_output_path()

