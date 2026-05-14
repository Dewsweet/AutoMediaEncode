# coding: utf-8
import time
import bcp47
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QStackedWidget, QFileDialog
from qfluentwidgets import qrouter, StrongBodyLabel, InfoBar, InfoBarPosition

from ..common.signal_bus import signalBus
from ..common.task_types import MuxPayload
from ..common.media_utils import MUXING_EXTS
from ..components.muxing_card_interface import InputFilesCard, TrackCard, OptionCard, OutputCard, AttachmentCard
from ..components.fileload_interface import FileLoadInterface
from ..components.hearder_widget import HeaderWidget
from ..services.muxing.mux_probe_service import MuxProbeService

class MuxProbeWorker(QThread):
    """用于在后台异步探测媒体文件信息的线程"""
    infoLoaded = Signal(str, object) # 参数: (文件路径, 探测结果字典)
    workFinished = Signal()

    def __init__(self, file_paths: list, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths

    def run(self):
        for path in self.file_paths:
            file_info = MuxProbeService.probe_file(path)
            self.infoLoaded.emit(path, file_info)
        self.workFinished.emit()

class MuxingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MuxingInterface")

        self.mainPage = QWidget()
        self.mainPage.setObjectName('mainPage')
        self.mainLayout = QVBoxLayout(self.mainPage)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)

        self.vBoxLayout = QVBoxLayout(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self._probe_workers = []
        self.mux_ext_filter = "所支持的媒体文件 (" + " ".join(f"*{ext}" for ext in MUXING_EXTS ) + ");;所有文件 (*)"

        self._initWidget()
        self._loadPage()
        self._initLayout()
        self._connect_signals()

    def _initWidget(self):
        self.header = HeaderWidget('媒体混流', '对各种媒体工具进行混流, 封装成媒体文件', '开始混流', self)
        self.inputFilesCard = InputFilesCard(self)
        self.trackCard = TrackCard(self)
        self.optionCard = OptionCard(self)
        self.outputCard = OutputCard(self)
        self.attachmentCard = AttachmentCard(self)
        self.attachmentCard.hide()

    def _loadPage(self):
        self.loadPage = QWidget()
        self.loadPage.setObjectName('LoadPage')
        self.loadLayout = QVBoxLayout(self.loadPage)
        self.loaderComponent = FileLoadInterface(self.mux_ext_filter, "📌 点击 or 拖放载入文件🥱", parent=self.loadPage)
        self.loaderComponent.setFixedSize(360, 200)
        self.loadLayout.addWidget(self.loaderComponent, 0, Qt.AlignCenter)

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

        self.stackedWidget.addWidget(self.loadPage)
        self.stackedWidget.addWidget(self.mainPage)
        qrouter.setDefaultRouteKey(self.stackedWidget, self.loadPage.objectName())
        self.stackedWidget.setCurrentIndex(0)

    def _connect_signals(self):
        signalBus.taskCompleted.connect(self.on_task_finished)
        signalBus.taskCancelled.connect(self.on_task_finished)
        signalBus.taskError.connect(self.on_task_error)

        self.header.reload_button.clicked.connect(self.open_file_dialog)
        self.header.start_button.clicked.connect(self.emit_builder_output)

        self.inputFilesCard.filesAdded.connect(self._handle_files_added)
        self.loaderComponent.filesReady.connect(self.on_files_loaded)
        self.inputFilesCard.removeFilesRequested.connect(self._handle_files_removed)
        self.inputFilesCard.clearFilesRequested.connect(self._handle_files_cleared)
        
        self.trackCard.trackSelectionUpdated.connect(self._handle_track_selection_changed)
        self.trackCard.table.itemChanged.connect(self._handle_track_item_changed)

        self.optionCard.enable_attachment_checkbox.stateChanged.connect(
            lambda state: self.attachmentCard.setVisible(state == Qt.CheckState.Checked.value)
        )
        self.optionCard.optionValueChanged.connect(self._handle_option_value_changed)
        self.optionCard.containerCb.currentTextChanged.connect(lambda _: self._update_output_path())

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择混流媒体文件", "", self.mux_ext_filter)
        if files:
            self.on_files_loaded(files)

    def _handle_files_added(self, file_paths: list):
        if not file_paths:
            return
            
        # 允许多个加载任务并发执行（存入列表防止被 Python GC 强制回收导致奔溃）
        worker = MuxProbeWorker(file_paths, self)
        self._probe_workers.append(worker)
        
        worker.infoLoaded.connect(self._on_show_loaded_info)
        worker.workFinished.connect(self._update_output_path)
        worker.workFinished.connect(lambda: self._cleanup_worker(worker))
        worker.start()

    def on_files_loaded(self, files: list):
        if not files or Path(files[0]).suffix.lower() not in MUXING_EXTS:
            InfoBar.warning(
                title='提示',
                content='请选择支持的媒体文件进行混流',
                orient=Qt.Horizontal,
                isClosable=False,
                duration=3000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
            return
    
        if self.stackedWidget.currentIndex() != 1:
            self.stackedWidget.setCurrentWidget(self.mainPage)
        self._handle_files_added(files)

    def _cleanup_worker(self, worker):
        if worker in self._probe_workers:
            self._probe_workers.remove(worker)
            worker.deleteLater()

    def _on_show_loaded_info(self, file_path: str, file_info: dict):
        """接收探测结果的槽函数，负责将文件信息展示到 UI 上，并关联轨道和附件"""
        if file_info:
            # 添加到 InputFilesCard 的表格中，并获取返回的 color_emoji
            color_emoji = self.inputFilesCard.add_file_to_table(file_info)
            if color_emoji:
                # 关联轨道
                self.trackCard.add_tracks(file_info, color_emoji)   
                # 附件区域
                attachments = file_info.get('attachments', [])
                if attachments:
                    self.attachmentCard.add_attachments(file_info['path'], attachments)
                    self.optionCard.enable_attachment_checkbox.setChecked(True)


    def _handle_files_removed(self, paths: list):
        """当文件被移除时, 更新 TrackCard 和 AttachmentCard 中对应的轨道和附件"""
        for path in paths:
            self.trackCard.remove_tracks_by_file(path)
            self.attachmentCard.remove_attachments_by_file(path)
        self._update_output_path()

    def _handle_files_cleared(self):
        """当文件被清空时, 清空 TrackCard 和 AttachmentCard 中的所有轨道和附件"""
        self.trackCard.clear_all_tracks()
        self.attachmentCard.clear_all_attachments()
        self._update_output_path()

    def _handle_track_item_changed(self, item):
        """当 TrackCard 中的某个 item 发生改变时, 检查是否是启用状态的改变, 如果是则更新输出路径"""
        if item.column() == 0:
            self._update_output_path()

    def _handle_track_selection_changed(self, row: int):
        """当 TrackCard 中的选中行发生改变时, 更新 OptionCard 中显示对应轨道的信息"""
        if row == -1:
            self.optionCard.set_track_selected_state(False)
            return

        data = self.trackCard.get_track_data(row)
        if data:
            enabled, name, language, is_default, flags = data
            self.optionCard.set_track_selected_state(True)
            self.optionCard.update_from_track(enabled, name, language, is_default, flags)

    def _handle_option_value_changed(self, key: str, value: object):
        """当选项卡中的值发生改变时，更新 TrackCard 中对应行的数据"""
        selected_items = self.trackCard.table.selectedItems()
        if not selected_items:
            return
            
        selected_rows = set(item.row() for item in selected_items)
        for row in selected_rows:
            self.trackCard.set_track_data(row, key, value)

    def _update_output_path(self):
        """根据当前输入的文件和轨道选择情况，自动生成一个默认的输出路径"""
        if getattr(self.outputCard, 'has_manual_path', False):
            return

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
            
            if codec_item and codec_item.checkState() == Qt.Checked:
                t_type = type_item.text() if type_item else ''
                if '视频' in t_type:
                    has_video = True
                elif '音频' in t_type:
                    has_audio = True
                elif '字幕' in t_type:
                    has_subtitle = True
        
        container_type = self.optionCard.containerCb.currentText().lower()
        
        if container_type == 'mkv':
            ext = '.mkv'
            if not has_video:
                if has_audio and not has_subtitle:
                    ext = '.mka'
                elif has_subtitle and not has_audio:
                    ext = '.mks'
        else:
            ext = f'.{container_type}'
                
        output_path = Path(first_file_path).with_suffix(ext)
        if output_path.exists():
             output_path = output_path.with_stem(output_path.stem + '_muxed')

        self.outputCard.output_path_lineEdit.setText(str(output_path))


    def emit_builder_output(self):
        track_data = self.trackCard.get_selected_tracks()
        option_state = self.optionCard.get_state()
        output_state = self.outputCard.get_state()
        attachment_state = self.attachmentCard.get_state() if self.optionCard.enable_attachment_checkbox.isChecked() else {'attachments': []}
        input_files = track_data.get('files', {})
        chapter_files = track_data.get('chapter_files', [])
        ordered_tracks = track_data.get('ordered_tracks', [])
        files_list = list(input_files.keys())
        target_container = str(option_state.get('container', '')).lower()

        enabled_video_tracks = []
        enabled_audio_tracks = []
        enabled_sub_tracks = []
        has_chapter_tracks = bool(chapter_files)

        for file_tracks in input_files.values():
            enabled_video_tracks.extend(file_tracks.get('video', []))
            enabled_audio_tracks.extend(file_tracks.get('audio', []))
            enabled_sub_tracks.extend(file_tracks.get('subtitle', []))
            has_chapter_tracks = has_chapter_tracks or bool(file_tracks.get('keep_chapters', False))

        if target_container in ('mp4', 'mov'):
            if enabled_sub_tracks or has_chapter_tracks:
                InfoBar.warning(
                    title='提示',
                    content='MP4 / MOV 不会封装软字幕和章节，请关闭对应轨道。',
                    parent=self,
                    isClosable=False,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return

            if len(enabled_video_tracks) > 1 or len(enabled_audio_tracks) > 1:
                InfoBar.error(
                    title='错误',
                    content='MP4 / MOV 仅支持一个视频轨和一个音频轨，请减少启用的轨道数量。',
                    parent=self,
                    isClosable=False,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return

            if len(enabled_video_tracks) + len(enabled_audio_tracks) == 0:
                InfoBar.error(
                    title='错误',
                    content='MP4 / MOV 至少需要启用一个视频轨或一个音频轨。',
                    parent=self,
                    isClosable=False,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return

        # 判断轨道中的语言标签是否合法
        for track in enabled_video_tracks + enabled_audio_tracks + enabled_sub_tracks:
            language = track.get('language', '')
            if language.lower() != 'und' and not language in bcp47.tags:
                InfoBar.error(
                    title='提示',
                    content=f'语言标签 "{language}" 不合法, 请修改为合法 BCP 47 语言标签',
                    parent=self,
                    isClosable=False,
                    duration=3000,
                    position=InfoBarPosition.TOP_RIGHT
                )
                return

        if not input_files:
            InfoBar.warning(
                title='错误', 
                content='请至少保留一个启用的轨道', 
                parent=self, 
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT
                )
            return
            
        if not output_state.get('output_path'):
            InfoBar.warning(
                title='错误', 
                content='请确保输出路径和输入参数正确', 
                parent=self,
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT
                )
            return

        task_id = f"task_{int(time.time()*1000)}"
        payload = MuxPayload(
            task_id=task_id,
            type="Mux",
            files=files_list,
            states={
                "tracks_state": input_files,
                "chapter_files": chapter_files,
                "ordered_tracks": ordered_tracks,
                "option_state": option_state,
                "output_state": output_state,
                "attachment_state": attachment_state
            }
        )

        self._current_checking_task_id = task_id
        self._current_task_has_error = False
        self._current_task_is_finished = False

        self.header.start_button.setText('正在执行中...')
        self.header.start_button.setEnabled(False)

        signalBus.taskAdded.emit(payload)
        QTimer.singleShot(800, lambda t=task_id: self._check_task_start_success(t))

    def _check_task_start_success(self, task_id: str):
        if getattr(self, '_current_checking_task_id', '') == task_id and not getattr(self, '_current_task_has_error', False) and not getattr(self, '_current_task_is_finished', False):
            InfoBar.success(
                title='任务执行成功',
                content='混流任务已开始执行，进入「任务进度」可查看详情',
                orient=Qt.Horizontal,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    def on_task_finished(self, task_id: str):
        if getattr(self, '_current_checking_task_id', '') == task_id:
            self._current_task_is_finished = True
            self.header.start_button.setText('开始混流')
            self.header.start_button.setEnabled(True)

    def on_task_error(self, task_id: str, error_msg: str):
        if getattr(self, '_current_checking_task_id', '') == task_id:
            self._current_task_has_error = True
            self.header.start_button.setText('开始混流')
            self.header.start_button.setEnabled(True)
            InfoBar.error(
                title='运行错误',
                content=f'执行任务期间发生错误, 请检查相关设置',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=-1,
                parent=self
            )