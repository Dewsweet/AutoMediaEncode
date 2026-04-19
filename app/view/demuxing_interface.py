from pathlib import Path
import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QStackedWidget

from qfluentwidgets import FluentIcon as FIF, InfoBar, InfoBarPosition, qrouter

from ..components.fileload_interface import FileLoadInterface
from ..components.hearder_widget import HeaderWidget
from ..components.demuxing_card_interface import InputFilesCard, MuxingOptionCard, OutputCard
from ..common.media_utils import DEMUXING_EXTS
from ..common.signal_bus import signalBus
from ..common.task_types import DemuxPayload

class DemuxingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('MuxingInterface')

        self.mainPage = QWidget(self)
        self.mainPage.setObjectName('mainPage')
        self.mainLayout = QVBoxLayout(self.mainPage)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)

        self.vBoxLayout = QVBoxLayout(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.Hbox = QWidget(self)
        self.HboxLayout = QHBoxLayout(self.Hbox)

        self.header = HeaderWidget('媒体抽流', '从视频文件中提取各种音频、视频、字幕流……', '开始抽流', self)
        self.inputFilesCard = InputFilesCard(self)
        self.optionCard = MuxingOptionCard(self)
        self.outputCard = OutputCard(self)

        self._init_file_filter()
        self._loadPage()
        self._initLayout()
        self._connect_signals()

    def _loadPage(self):
        self.loadPage = QWidget()
        self.loadPage.setObjectName('LoadPage')
        self.loadLayout = QVBoxLayout(self.loadPage)

        self.loaderComponent = FileLoadInterface(self.file_filter, "📌 点击 or 拖放载入文件😋", parent=self.loadPage)
        self.loaderComponent.setFixedSize(360, 200)
        self.loadLayout.addWidget(self.loaderComponent, 0, Qt.AlignCenter)

    def _initLayout(self):
        self.HboxLayout.addWidget(self.inputFilesCard, 7)
        self.HboxLayout.addWidget(self.optionCard, 3)
        self.HboxLayout.setContentsMargins(0, 0, 0, 0)

        self.mainLayout.addWidget(self.header, alignment=Qt.AlignTop)
        self.mainLayout.addWidget(self.Hbox)
        self.mainLayout.addWidget(self.outputCard, alignment=Qt.AlignBottom)

        self.stackedWidget.addWidget(self.loadPage)
        self.stackedWidget.addWidget(self.mainPage)

        qrouter.setDefaultRouteKey(self.stackedWidget, self.loadPage.objectName())
        self.stackedWidget.setCurrentIndex(0)

    def _init_file_filter(self):
        v_ext = "视频文件 (" + " ".join(f"*{ext}" for ext in DEMUXING_EXTS) + ")"
        all_ext = "所有文件 (*)"
        self.file_filter = f"{v_ext};;{all_ext}"

    def _connect_signals(self):
        # 载入文件
        self.loaderComponent.filesReady.connect(self.on_files_loaded)
        self.header.reload_button.clicked.connect(self.open_file_dialog)
        self.inputFilesCard.load_files_requested.connect(self.open_file_dialog)
        self.header.start_button.clicked.connect(self.emit_builder_output)

        # 输出路径
        self.outputCard.output_path_view_button.clicked.connect(self.choose_output_dir)
        
        # 挂载任务状态侦听信号
        signalBus.taskCompleted.connect(self.on_task_finished)
        signalBus.taskCancelled.connect(self.on_task_finished)
        signalBus.taskError.connect(self.on_task_error)

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择抽流文件", "", self.file_filter)
        if files:
            self.on_files_loaded(files)

    def on_files_loaded(self, files: list):
        if not files: 
            return
            
        self.inputFilesCard.update_files(files)
        
        if self.stackedWidget.currentIndex() != 1:
            qrouter.push(self.stackedWidget, self.mainPage.objectName())
            self.stackedWidget.setCurrentIndex(1)

    def choose_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.outputCard.output_path_lineEdit.setText(folder)

    def emit_builder_output(self):
        """组装抽流任务负载并发出全局信号"""
        tracks_state = self.inputFilesCard.get_selected_tracks()
        option_state = self.optionCard.get_state()
        output_state = self.outputCard.get_state()
        
        files = list(tracks_state.keys())
        
        if not files:
            InfoBar.error(
                title='无法开始',
                content='文件列表为空，或未选择任何需要抽取的轨道！',
                orient=Qt.Horizontal,
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return

        if not output_state.get('output_dir') and not output_state.get('use_source_dir'):
            InfoBar.error(
                title='无法开始',
                content='未设置输出目录，请选择输出路径或勾选"使用源目录"!',
                orient=Qt.Horizontal,
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return 

        task_id = f"task_{int(time.time()*1000)}"
        payload = DemuxPayload(
            task_id=task_id,
            type="Demux",
            files=files,
            states={
                "tracks_state": tracks_state,
                "option_state": option_state,
                "output_state": output_state
            }
        )
        
        self._current_checking_task_id = task_id
        self._current_task_has_error = False
        self._current_task_is_finished = False

        self.header.start_button.setText('正在执行中...')
        self.header.start_button.setEnabled(False)

        signalBus.taskAdded.emit(payload)
        
        # 延时 800 毫秒后判定后端程序是否闪崩报错或者是秒完成
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, lambda t=task_id: self._check_task_start_success(t))

    def _check_task_start_success(self, task_id: str):
        if getattr(self, '_current_checking_task_id', '') == task_id and not getattr(self, '_current_task_has_error', False) and not getattr(self, '_current_task_is_finished', False):
            InfoBar.success(
                title='任务执行成功',
                content='抽流任务已开始执行，进入「任务进度」可查看详情',
                orient=Qt.Horizontal,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    def on_task_finished(self, task_id: str):
        """侦听任务完成信号"""
        if getattr(self, '_current_checking_task_id', '') == task_id:
            self._current_task_is_finished = True
            self.header.start_button.setText('开始抽流')
            self.header.start_button.setEnabled(True)

    def on_task_error(self, task_id: str, error_msg: str):
        """侦听任务异常信号"""
        if getattr(self, '_current_checking_task_id', '') == task_id:
            self._current_task_has_error = True
            self.header.start_button.setText('开始抽流')
            self.header.start_button.setEnabled(True)
            InfoBar.error(
                title='运行错误',
                content=f'执行任务期间发生错误:\n{error_msg}',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=-1,
                parent=self
            )







