from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidgetItem, QApplication

from qfluentwidgets import CardWidget, HeaderCardWidget, TreeWidget, RoundMenu, Action, BodyLabel, ComboBox, CheckBox, LineEdit, PushButton, PrimaryPushButton, FluentIcon as FIF

from ..services.demuxing.demux_probe_service import DemuxProbeService
from ..common.media_utils import classify_files, get_present_types, DEMUXING_EXTS

class ProbeWorker(QThread):
    """后台扫描文件的线程，防止界面卡顿"""
    file_probed = Signal(str, dict)

    def __init__(self, files, probe_service, parent=None):
        super().__init__(parent)
        self.files = files
        self.probe_service = probe_service

    def run(self):
        for file_path in self.files:
            data = self.probe_service.probe_file(file_path)
            self.file_probed.emit(file_path, data)

class InputFilesCard(HeaderCardWidget):
    load_files_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('输入文件')
        self.probe_service = DemuxProbeService()
        self.setAcceptDrops(True)

        self.mianBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mianBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.inputFilesTree = TreeWidget()
        self.inputFilesTree.setHeaderHidden(True)
        self.inputFilesTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.inputFilesTree.setAcceptDrops(True)

        self.mainLayout.addWidget(self.inputFilesTree)
        self.viewLayout.addWidget(self.mianBox)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.loading_items = {} # 记录正在加载的文件对应的树节点，key为文件路径，value 为 QTreeWidgetItem

        self._connect_signals()

    def _connect_signals(self):
        self.inputFilesTree.customContextMenuRequested.connect(self.show_context_menu)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if files:
            self.update_files(files)

    def update_files(self, files: list):
        self.inputFilesTree.clear()
        self.loading_items.clear()
        
        for file_path in files:
            path_obj = Path(file_path)
            top_item = QTreeWidgetItem([path_obj.name])
            top_item.setData(0, Qt.UserRole, {"file_path": file_path})
            
            # 使用临时子节点显示加载中
            loading_child = QTreeWidgetItem(["文件加载中……"])
            top_item.addChild(loading_child)
            
            self.inputFilesTree.addTopLevelItem(top_item)
            top_item.setExpanded(True)
            self.loading_items[file_path] = top_item
            
        # 启动后台线程读取信息
        self.worker = ProbeWorker(files, self.probe_service, self)
        self.worker.file_probed.connect(self._on_file_probed)
        self.worker.start()

    def _on_file_probed(self, file_path: str, probe_data: dict):
        top_item = self.loading_items.get(file_path)
        if not top_item: return

        # 移除"加载中"的节点
        for i in range(top_item.childCount()):
            top_item.takeChild(0)

        if "error" in probe_data:
            err_item = QTreeWidgetItem([f"解析失败: {probe_data['error']}"])
            top_item.addChild(err_item)
            return

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
        # Attachments
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

    def show_context_menu(self, pos):
        mune = RoundMenu(parent=self)

        load_action = Action('载入文件', triggered=lambda: self.load_files_requested.emit())
        
        select_all = Action('全选所有项', triggered=self.select_all_items)
        deselect_all = Action('取消全选', triggered=self.deselect_all_items)
        invert_select = Action('反选', triggered=self.invert_all_items)
        remove_selected = Action('移除已选文件', triggered=self.remove_selected_files)

        select_submune = RoundMenu("快速选择...", self)
        select_video = Action('所有视频', triggered=lambda: self.select_by_type("video"))
        select_audio = Action('所有音频', triggered=lambda: self.select_by_type("audio"))
        select_sub = Action('所有字幕', triggered=lambda: self.select_by_type("subtitle"))
        select_att = Action('所有附件', triggered=lambda: self.select_by_type("attachment"))
        select_chapter = Action('所有章节', triggered=lambda: self.select_by_type("chapter"))

        select_submune.addActions([select_video, select_audio, select_sub, select_att, select_chapter])

        mune.addAction(load_action)
        mune.addAction(remove_selected)
        mune.addSeparator()
        mune.addActions([select_all, deselect_all, invert_select])
        mune.addMenu(select_submune)
        
        mune.exec(self.inputFilesTree.mapToGlobal(pos))
        
    def _iterate_child_items(self):
        for i in range(self.inputFilesTree.topLevelItemCount()):
            top_item = self.inputFilesTree.topLevelItem(i)
            for j in range(top_item.childCount()):
                yield top_item.child(j)
                
    def select_all_items(self):
        for child in self._iterate_child_items():
            if child.flags() & Qt.ItemIsUserCheckable:
                child.setCheckState(0, Qt.Checked)
                
    def deselect_all_items(self):
        for child in self._iterate_child_items():
            if child.flags() & Qt.ItemIsUserCheckable:
                child.setCheckState(0, Qt.Unchecked)

    def invert_all_items(self):
        for child in self._iterate_child_items():
            if child.flags() & Qt.ItemIsUserCheckable:
                state = child.checkState(0)
                child.setCheckState(0, Qt.Unchecked if state == Qt.Checked else Qt.Checked)

    def select_by_type(self, target_type):
        for child in self._iterate_child_items():
            if child.flags() & Qt.ItemIsUserCheckable:
                data = child.data(0, Qt.UserRole)
                if data and data.get("type", "") == target_type:
                    child.setCheckState(0, Qt.Checked)

    def remove_selected_files(self):
        # 移除有选中的复选框关联的父节点文件
        items_to_remove = set()
        for i in range(self.inputFilesTree.topLevelItemCount()):
            top_item = self.inputFilesTree.topLevelItem(i)
            for j in range(top_item.childCount()):
                if top_item.child(j).checkState(0) == Qt.Checked:
                    items_to_remove.add(top_item)
                    break
        for item in items_to_remove:
            index = self.inputFilesTree.indexOfTopLevelItem(item)
            self.inputFilesTree.takeTopLevelItem(index)

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


        







