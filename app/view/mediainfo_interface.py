from PySide6.QtCore import Qt, QEvent, QThread, Signal
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QStackedWidget, QFileDialog

from qfluentwidgets import (TitleLabel, CaptionLabel, PushButton, ToggleButton, ComboBox, 
                            TextEdit, TextBrowser, ToolTipFilter, qrouter )
from qfluentwidgets import FluentIcon as FIF

from ..components.fileload_interface import FileLoadInterface
from ..services.mediainfo_service import MediaInfoService


class MediaInfoWorker(QThread):
    """异步解析媒体信息的后台工作线程"""
    info_ready = Signal(str, bool)

    def __init__(self, service, file_path, is_basic_mode, parent=None):
        super().__init__(parent)
        self.service = service
        self.file_path = file_path
        self.is_basic_mode = is_basic_mode

    def run(self):
        # 耗时操作：用pymediainfo解析文件并在实例中组装文本
        if self.is_basic_mode:
            result = self.service.view_info(self.file_path)
        else:
            result = self.service.full_info(self.file_path)
        
        # 通过信号安全地传回主线程
        self.info_ready.emit(result, self.is_basic_mode)


class MediaifInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("MediaifInterface")

        self.mainPage = QWidget()
        self.mainPage.setObjectName("mainPage")
        self.mainLayout = QVBoxLayout(self.mainPage)

        # 用 QStackedWidget 来支持页面的切换
        self.vBoxLayout = QVBoxLayout(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.stackedWidget)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.loadFilesPage()
        self._hearderArea()
        self._bodyArea()
        self._initWidgets()
        self._connect_signals()

        # 初始化服务对象与线程池占位符
        self.mis = MediaInfoService()
        self.worker = None

    def _hearderArea(self):
        self.headerBox = QWidget(self)
        self.headerLayout = QVBoxLayout(self.headerBox)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)

        self.buttonHBoxLayout = QHBoxLayout()

        self.titleLabel = TitleLabel('Media Info', self)
        self.subTitleLabel = CaptionLabel('调用mediainfo查询媒体信息', self)
        self.subTitleLabel.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))

        self.reLoadButton = PushButton('重新载入文件', self, FIF.ADD)
        self.reLoadButton.setToolTip('直接拖入文本框也行✨')
        self.reLoadButton.installEventFilter(ToolTipFilter(self.reLoadButton)) # 
        self.switchButton = ToggleButton('查看详细信息', self)
        self.switchButton.setChecked(True) 

    def _bodyArea(self):
        self.inputFilesList = ComboBox(self)
        self.inputFilesList.setMinimumHeight(36)
        self.inputFilesList.clear()

        self.textEdit = TextEdit(self)
        self.textEdit.setReadOnly(True)
        self.textEdit.setAcceptDrops(True)
        self.textEdit.installEventFilter(self)

    def _initWidgets(self):
        self.buttonHBoxLayout.addStretch(1)
        self.buttonHBoxLayout.addWidget(self.reLoadButton, alignment=Qt.AlignRight)
        self.buttonHBoxLayout.addWidget(self.switchButton, alignment=Qt.AlignRight)
        self.buttonHBoxLayout.setAlignment(Qt.AlignVCenter | Qt.AlignRight) 

        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addWidget(self.subTitleLabel)
        self.headerLayout.addLayout(self.buttonHBoxLayout)
        self.headerLayout.setAlignment(Qt.AlignTop) 

        self.mainLayout.addWidget(self.headerBox)
        self.mainLayout.addWidget(self.inputFilesList)
        self.mainLayout.addWidget(self.textEdit)
        self.mainLayout.setContentsMargins(30, 20, 30, 20)
        
        # 页面放进索引
        self.stackedWidget.addWidget(self.loadPage) # index 0
        self.stackedWidget.addWidget(self.mainPage) # index 1
        
        qrouter.setDefaultRouteKey(self.stackedWidget, self.loadPage.objectName())
        
        self.stackedWidget.setCurrentIndex(0)

    def loadFilesPage(self):
        self.loadPage = QWidget() 
        self.loadPage.setObjectName("loadPage")
        self.loadLayout = QVBoxLayout(self.loadPage)
        self.loaderComponent = FileLoadInterface(
            parent=self.loadPage,
        )
        self.loaderComponent.setFixedSize(360, 200)
        self.loadLayout.addWidget(self.loaderComponent, 0, Qt.AlignCenter)
        
    def _connect_signals(self):
        self.loaderComponent.filesReady.connect(self.on_files_loaded)
        self.reLoadButton.clicked.connect(self.on_reload_clicked)
        self.inputFilesList.currentTextChanged.connect(self.get_media_info)
        self.switchButton.toggled.connect(self.get_media_info)


    def on_files_loaded(self, files: list):
        """
        接收文件列表，更新下拉框和页面状态
        files 由 FileLoadWidget 通过信号传入
        """
        if not files: 
            return
            
        self.inputFilesList.clear()
        self.switchButton.setChecked(True)
        self.inputFilesList.addItems(files)
        
        # 将页面从加载层切换到正在运行的功能层
        if self.stackedWidget.currentIndex() != 1:
            qrouter.push(self.stackedWidget, self.mainPage.objectName())
            self.stackedWidget.setCurrentIndex(1)

    def on_reload_clicked(self):
        """点击重新载入，弹出文件选择框，获取文件后更新下拉框和页面状态"""
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "所有文件 (*)")
        if not files:
            return
        
        self.on_files_loaded(files)
        
    def get_media_info(self, *args):
        """
        从下拉框读文件，启动 QThread 去后台解析，避免阻塞UI主线程
        """
        current_file = self.inputFilesList.currentText()
        if not current_file:
            return
            
        is_basic_mode = self.switchButton.isChecked()
        
        # 预先设置UI状态，给用户视觉反馈
        if is_basic_mode:
            self.switchButton.setText('查看详细信息')
            self.textEdit.setMarkdown("正在分析基本媒体信息...")
        else:
            self.switchButton.setText('查看基本信息')
            self.textEdit.setPlainText("正在分析完整媒体信息...")
            
        # 防止用户疯狂点击导致启动多个线程
        if self.worker is not None and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        # 实例化子工作线程并通过信号连回主线程
        self.worker = MediaInfoWorker(self.mis, current_file, is_basic_mode, self)
        self.worker.info_ready.connect(self.on_info_ready)
        self.worker.start()

    def on_info_ready(self, info_text: str, is_basic_mode: bool):
        """接收子线程传回来的数据，在主线程安全地更新UI"""
        if is_basic_mode:
            self.textEdit.setMarkdown(info_text)
        else:
            self.textEdit.setPlainText(info_text)

    def eventFilter(self, watched, event):
        """劫持文本编辑区的拖放事件，支持直接将文件拖入文本区进行分析"""
        if watched == self.textEdit:
            if event.type() == QEvent.Type.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True 
            
            elif event.type() == QEvent.Type.Drop:
                urls = event.mimeData().urls()
                files = [u.toLocalFile() for u in urls if u.isLocalFile()]
                if files:
                    self.on_files_loaded(files)
                return True
            
        return super().eventFilter(watched, event)
        