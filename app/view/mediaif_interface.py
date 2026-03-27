from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QStackedWidget, QFileDialog

from qfluentwidgets import (TitleLabel, CaptionLabel, PushButton, ToggleButton, ComboBox, 
                            TextEdit, TextBrowser, ToolTipFilter, qrouter )
from qfluentwidgets import FluentIcon as FIF

from app.components.file_load_widget import FileLoadWidget
from app.services.mediainfo_service import MediaInfoService


class MediaifInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("MediaifInterface")

        # 用 QStackedWidget 来支持页面的切换
        self.vBoxLayout = QVBoxLayout(self)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.stackedWidget) 

        # 创建加载页面
        self.loadFilesPage()

        # 创建功能页面
        self.mainPage = QWidget()
        self.mainPage.setObjectName("mainPage")
        self.mainLayout = QVBoxLayout(self.mainPage)

        # 标题栏区域
        self.headerlayout = QVBoxLayout()
        self.headerlayout.setContentsMargins(0, 0, 0, 0)
        self.headerlayout.setSpacing(0)
        self.buttonHoxLayout = QHBoxLayout()
        self.buttonHoxLayout.setSpacing(10)

        self.titleLabel = TitleLabel('Media Info', self)
        self.subtitleLabel = CaptionLabel('调用mediainfo查询媒体信息', self)
        self.subtitleLabel.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))

        self.reLoadButton = PushButton('重新载入文件', self, FIF.ADD)
        self.reLoadButton.setToolTip('直接拖入文本框也行✨')
        self.reLoadButton.installEventFilter(ToolTipFilter(self.reLoadButton)) # 
        self.switchButton = ToggleButton('查看详细信息', self)
        self.switchButton.setChecked(True) 

        # 添加标题布局
        self.buttonHoxLayout.addStretch(1)
        self.buttonHoxLayout.addWidget(self.reLoadButton, alignment=Qt.AlignRight)
        self.buttonHoxLayout.addWidget(self.switchButton, alignment=Qt.AlignRight)
        self.buttonHoxLayout.setAlignment(Qt.AlignVCenter | Qt.AlignRight) 

        self.headerlayout.addWidget(self.titleLabel)
        self.headerlayout.addWidget(self.subtitleLabel)
        self.headerlayout.addLayout(self.buttonHoxLayout)
        self.headerlayout.setAlignment(Qt.AlignTop) 

        # 主要内容区域
        self.inputFilesList = ComboBox(self)
        self.inputFilesList.setMinimumHeight(36)
        self.inputFilesList.clear()

        self.textEdit = TextEdit(self)
        self.textEdit.setReadOnly(True)

        self.textEdit.setAcceptDrops(True)
        self.textEdit.installEventFilter(self)

        # 添加整体布局，放进 mainLayout
        self.mainLayout.addLayout(self.headerlayout)
        self.mainLayout.addWidget(self.inputFilesList)
        self.mainLayout.addWidget(self.textEdit)
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setSpacing(10)
        
        # 页面放进索引
        self.stackedWidget.addWidget(self.loadPage) # index 0
        self.stackedWidget.addWidget(self.mainPage) # index 1
        
        qrouter.setDefaultRouteKey(self.stackedWidget, self.loadPage.objectName())
        
        self.stackedWidget.setCurrentIndex(0)
        
        self._connect_signals()

    def loadFilesPage(self):
        self.loadPage = QWidget() 
        self.loadPage.setObjectName("loadPage")
        self.loadLayout = QVBoxLayout(self.loadPage)
        self.loaderComponent = FileLoadWidget(
            parent=self.loadPage,
        )
        self.loaderComponent.setFixedSize(360, 200)
        self.loadLayout.addWidget(self.loaderComponent, 0, Qt.AlignCenter)
        
    def _connect_signals(self):
        self.loaderComponent.filesReady.connect(self.on_files_loaded)
        self.reLoadButton.clicked.connect(self.on_reload_clicked)
        self.inputFilesList.currentTextChanged.connect(self.get_media_info)
        self.switchButton.toggled.connect(self.get_media_info)

    def on_files_loaded(self, files: list): # files 由 FileLoadWidget 通过信号传入，是一个文件路径列表
        """接收文件列表，更新下拉框和页面状态"""
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
            
        self.inputFilesList.clear()
        self.switchButton.setChecked(True)
        self.inputFilesList.addItems(files)
        
    def get_media_info(self, *args):
        """从文件列表读文件，用 CLI 更新文本

        根据 switchButton 状态：
        isChecked==True 表示“可点击进入详细模式”, 所以按钮文字显示“查看详细信息”, 当前处于“基础信息”模式
        isChecked==False 表示“可点击退回基本模式”, 所以按钮文字显示“查看基本信息”, 当前处于“详细信息”模式
        """
        current_file = self.inputFilesList.currentText()
        if not current_file:
            return
            
        is_basic_mode = self.switchButton.isChecked()
        
        if is_basic_mode:
            self.switchButton.setText('查看详细信息')
            self.textEdit.setMarkdown("正在分析基础媒体信息...")
        else:
            self.switchButton.setText('查看基本信息')
            self.textEdit.setPlainText("正在分析完整媒体信息...")
            
        info_text = MediaInfoService.get_info(current_file, basic_mode=is_basic_mode)
        
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
        












        
