from PySide6.QtCore import Qt, QEvent, QThread, Signal, QCoreApplication
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QStackedWidget, QFileDialog

from qfluentwidgets import (TitleLabel, CaptionLabel, PushButton, ToggleButton, ComboBox, 
                            TextEdit, TextBrowser, ToolTipFilter, qrouter )
from qfluentwidgets import FluentIcon as FIF

from ..components.fileload_interface import FileLoadInterface
from ..services.mediainfo_service import MediaInfoService
from app.common.logger import logger


class MediaInfoWorker(QThread):
    """异步解析媒体信息的后台工作线程"""
    info_ready = Signal(int, str, bool)

    def __init__(self, service, request_id, file_path, is_basic_mode, parent=None):
        super().__init__(parent)
        self.service = service
        self.request_id = request_id
        self.file_path = file_path
        self.is_basic_mode = is_basic_mode

    def run(self):
        try:
            if self.is_basic_mode:
                result = self.service.view_info(self.file_path)
            else:
                result = self.service.full_info(self.file_path)
        except Exception as exc:
            logger.exception(f"MediaInfo 报告生成失败: {self.file_path} - {exc}")
            result = QCoreApplication.translate(
                "MediaInfoService", "无法读取媒体信息，请检查文件和 MediaInfo DLL。")
        self.info_ready.emit(self.request_id, result, self.is_basic_mode)


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
        self._request_id = 0
        self._pending_request = None
        self._shutting_down = False
        QCoreApplication.instance().aboutToQuit.connect(self.shutdown)

    def _hearderArea(self):
        self.headerBox = QWidget(self)
        self.headerLayout = QVBoxLayout(self.headerBox)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)

        self.buttonHBoxLayout = QHBoxLayout()

        self.titleLabel = TitleLabel(self.tr('媒体信息'), self)
        self.subTitleLabel = CaptionLabel(self.tr('使用 MediaInfo 查询媒体信息'), self)
        self.subTitleLabel.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))

        self.reLoadButton = PushButton(self.tr('重新载入文件'), self)
        self.reLoadButton.setToolTip(self.tr('直接拖入文本框也行✨'))
        self.reLoadButton.installEventFilter(ToolTipFilter(self.reLoadButton))
        self.switchButton = ToggleButton(self.tr('查看详细信息'), self)
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
        self.buttonHBoxLayout.addSpacing(10)
        self.buttonHBoxLayout.addWidget(self.switchButton, alignment=Qt.AlignRight)
        self.buttonHBoxLayout.setAlignment(Qt.AlignVCenter | Qt.AlignRight) 

        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addWidget(self.subTitleLabel)
        self.headerLayout.addLayout(self.buttonHBoxLayout)
        self.headerLayout.setSpacing(0)

        self.mainLayout.addWidget(self.headerBox)
        self.mainLayout.addWidget(self.inputFilesList)
        self.mainLayout.addWidget(self.textEdit)
        self.mainLayout.setContentsMargins(20, 20, 20, 10)
        
        # 页面放进索引
        self.stackedWidget.addWidget(self.loadPage) # index 0
        self.stackedWidget.addWidget(self.mainPage) # index 1
        
        qrouter.setDefaultRouteKey(self.stackedWidget, self.loadPage.objectName())
        
        self.stackedWidget.setCurrentIndex(0)

    def loadFilesPage(self):
        self.loadPage = QWidget() 
        self.loadPage.setObjectName("loadPage")
        self.loadLayout = QVBoxLayout(self.loadPage)
        self.loaderComponent = FileLoadInterface(title=self.tr("📌 媒体文件信息 😇"), desc=self.tr("查询媒体文件相关信息"), parent=self.loadPage)
        self.loaderComponent.setFixedWidth(360)
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
            
        # 批量更新后仅提交一次请求，避免清空列表时显示旧文件结果。
        list_blocked = self.inputFilesList.blockSignals(True)
        switch_blocked = self.switchButton.blockSignals(True)
        try:
            self.inputFilesList.clear()
            self.switchButton.setChecked(True)
            self.inputFilesList.addItems(files)
        finally:
            self.inputFilesList.blockSignals(list_blocked)
            self.switchButton.blockSignals(switch_blocked)
        self.get_media_info()
        
        # 将页面从加载层切换到正在运行的功能层
        if self.stackedWidget.currentIndex() != 1:
            qrouter.push(self.stackedWidget, self.mainPage.objectName())
            self.stackedWidget.setCurrentIndex(1)

    def on_reload_clicked(self):
        """点击重新载入，弹出文件选择框，获取文件后更新下拉框和页面状态"""
        files, _ = QFileDialog.getOpenFileNames(self, self.tr("选择文件"), "", self.tr("所有文件 (*)"))
        if not files:
            return
        
        self.on_files_loaded(files)
        
    def get_media_info(self, *args):
        """
        从下拉框读文件，启动 QThread 去后台解析，避免阻塞UI主线程
        """
        if self._shutting_down:
            return
        self._request_id += 1
        self._pending_request = None
        current_file = self.inputFilesList.currentText()
        if not current_file:
            return
            
        is_basic_mode = self.switchButton.isChecked()
        
        # 预先设置UI状态，给用户视觉反馈
        if is_basic_mode:
            self.switchButton.setText(self.tr('查看详细信息'))
            self.textEdit.setMarkdown(self.tr("正在分析基本媒体信息..."))
        else:
            self.switchButton.setText(self.tr('查看基本信息'))
            self.textEdit.setPlainText(self.tr("正在分析完整媒体信息..."))
            
        request = (self._request_id, current_file, is_basic_mode)
        if self.worker is not None:
            self._pending_request = request
        else:
            self._start_worker(request)

    def _start_worker(self, request):
        """同一页面仅有一个活动线程，其余操作合并为最新请求。"""
        self.worker = MediaInfoWorker(self.mis, *request, parent=self)
        self.worker.info_ready.connect(self.on_info_ready)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_finished(self):
        worker = self.sender()
        if worker is not self.worker:
            return
        self.worker = None
        worker.deleteLater()
        pending = self._pending_request
        self._pending_request = None
        if pending is not None and not self._shutting_down:
            self._start_worker(pending)

    def on_info_ready(self, request_id: int, info_text: str, is_basic_mode: bool):
        """旧文件或旧模式的结果不覆盖最新操作。"""
        if self._shutting_down or request_id != self._request_id:
            return
        if is_basic_mode:
            self.textEdit.setMarkdown(info_text)
        else:
            self.textEdit.setPlainText(info_text)

    def shutdown(self):
        """正常等待 DLL 调用结束，不能强制终止持有共享锁的线程。"""
        self._shutting_down = True
        self._pending_request = None
        self._request_id += 1
        if self.worker is not None:
            self.worker.wait()
            self.worker.deleteLater()
            self.worker = None

    def closeEvent(self, event):
        self.shutdown()
        super().closeEvent(event)

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
        