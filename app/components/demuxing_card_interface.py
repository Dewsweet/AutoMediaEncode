from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidgetItem, QApplication

from qfluentwidgets import CardWidget, HeaderCardWidget, TreeWidget, RoundMenu, Action, BodyLabel, ComboBox, CheckBox, LineEdit, PushButton, PrimaryPushButton, FluentIcon as FIF

from ..services.demuxing.demux_probe_service import DemuxProbeService

class InputFilesCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('输入文件')
        self.probe_service = DemuxProbeService()

        self.mianBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mianBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.inputFilesTree = TreeWidget()
        self.inputFilesTree.setHeaderHidden(True)
        self.inputFilesTree.setContextMenuPolicy(Qt.CustomContextMenu)

        self.mainLayout.addWidget(self.inputFilesTree)
        self.viewLayout.addWidget(self.mianBox)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self._connect_signals()

    def _connect_signals(self):
        self.inputFilesTree.customContextMenuRequested.connect(self.show_context_mune)

    def update_files(self, files: list):
        self.inputFilesTree.clear()
        QApplication.processEvents()

        for file_path in files:
            path_obj = Path(file_path)
            top_item = QTreeWidgetItem([path_obj.name])
            
            probe_data = self.probe_service.probe_file(file_path)
            if "error" in probe_data:
                err_item = QTreeWidgetItem([f"解析失败: {probe_data['error']}"])
                top_item.addChild(err_item)
                self.inputFilesTree.addTopLevelItem(top_item)
                continue

            track_number = 1
            
            # Video Tracks
            for stream in probe_data.get('video', []):
                track_text = self.probe_service.format_track_for_ui(stream, track_number)
                child = QTreeWidgetItem([track_text])
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, {"type": "video", "id": stream['id']})
                top_item.addChild(child)
                track_number += 1
                
            # Audio Tracks
            for stream in probe_data.get('audio', []):
                track_text = self.probe_service.format_track_for_ui(stream, track_number)
                child = QTreeWidgetItem([track_text])
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, {"type": "audio", "id": stream['id']})
                top_item.addChild(child)
                track_number += 1

            # Subtitle Tracks
            for stream in probe_data.get('subtitle', []):
                track_text = self.probe_service.format_track_for_ui(stream, track_number)
                child = QTreeWidgetItem([track_text])
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, {"type": "subtitle", "id": stream['id']})
                top_item.addChild(child)
                track_number += 1

            # Attachments (Start numbering from 1 independently)
            attachment_number = 1
            for stream in probe_data.get('attachment', []):
                track_text = self.probe_service.format_track_for_ui(stream, attachment_number)
                child = QTreeWidgetItem([track_text])
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, {"type": "attachment", "id": stream['id']})
                top_item.addChild(child)
                attachment_number += 1

            # Chapters
            chapters_count = probe_data.get('chapters', 0)
            if chapters_count > 0:
                child = QTreeWidgetItem([f"章节: {chapters_count} 个条目"])
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, {"type": "chapter"})
                top_item.addChild(child)

            self.inputFilesTree.addTopLevelItem(top_item)

        self.inputFilesTree.expandAll()

    def show_context_mune(self, pos):
        mune = RoundMenu(parent=self)

        select_all = Action('全选', triggered=self.select_all_items)

        select_submune = RoundMenu("选择", self)
        select_video = Action('选择视频', triggered=self.select_video)
        select_audio = Action('选择音频', triggered=self.select_audio)
        select_sub = Action('选择字幕', triggered=self.select_sub)
        select_att = Action('选择附件', triggered=self.select_att)
        select_mune = Action('选择菜单', triggered=self.select_mune)

        select_submune.addActions([select_video, select_audio, select_sub, select_att, select_mune])

        mune.addAction(select_all)
        mune.addMenu(select_submune)
        mune.exec(self.inputFilesTree.mapToGlobal(pos))
        
    def select_all_items():
        pass
    def select_video():
        pass
    def select_audio():
        pass
    def select_sub():
        pass
    def select_att():
        pass
    def select_mune():
        pass

class MuxingOptionCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('其他选项')

        self.mainBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.contextHLayout1 = QHBoxLayout()
        # self.contextHLayout2 = QHBoxLayout()
        # self.contextHLayout3 = QHBoxLayout()

        self.chapter_suffix_label = BodyLabel('章节后缀: ')
        self.chapter_suffix_cb = ComboBox()
        self.chapter_suffix_cb.addItems(['XML', 'OGM', 'CUE', 'TXT'])

        self.sub_departition_ckeackbox = CheckBox('字幕去子集化')

        self.turehd_decore_ckeackbox = CheckBox('TrueHD 去核心')

        self.contextHLayout1.addWidget(self.chapter_suffix_label)
        self.contextHLayout1.addWidget(self.chapter_suffix_cb)
        self.contextHLayout1.addStretch(1)

        self.mainLayout.addLayout(self.contextHLayout1)
        self.mainLayout.addWidget(self.sub_departition_ckeackbox)
        self.mainLayout.addWidget(self.turehd_decore_ckeackbox)
        self.mainLayout.addStretch(1)

        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(20, 10, 10, 10)

class OutputCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('输出设置')

        self.mainBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.OutputPathLayout = QHBoxLayout()

        self.output_path_label = BodyLabel('输出路径: ')
        self.output_path_lineEdit = LineEdit()

        self.using_source_dir_checkbox = CheckBox('源目录')
        self.output_path_view_button = PrimaryPushButton('浏览')

        self.OutputPathLayout.addWidget(self.output_path_label)
        self.OutputPathLayout.addWidget(self.output_path_lineEdit)
        self.OutputPathLayout.addWidget(self.using_source_dir_checkbox)
        self.OutputPathLayout.addWidget(self.output_path_view_button)


        self.mainLayout.addLayout(self.OutputPathLayout)

        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(10, 10, 10, 10)


        







