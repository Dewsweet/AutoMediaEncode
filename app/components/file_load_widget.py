# from typing import List
from PySide6.QtCore import Qt, Signal, QEvent, QCoreApplication
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QFileDialog, QVBoxLayout
from qfluentwidgets import SimpleCardWidget, IconWidget, FluentIcon, SubtitleLabel, CaptionLabel, PrimaryPushButton

class FileLoadWidget(SimpleCardWidget):
    """
    文件载入组件
    提供一个带有图标和文本的拖拽/点击响应区域，
    获取到文件后通过 filesReady 信号将文件列表抛出。
    """
    # 定义信号：发送包含文件完整路径的列表
    filesReady = Signal(list)

    def __init__(self, file_filter="所有文件 (*)", title="📌 点击 or 拖放载入文件🙄", icon=FluentIcon.FOLDER_ADD, parent=None):
        super().__init__(parent)
        self.file_filter = file_filter
        # 设置组件属性
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 300)
        self.setCursor(Qt.PointingHandCursor)
        # self.setStyleSheet("FileLoadWidget { background-color: rgb(120, 120, 120); border-radius: 8px; border: none;}")

        
        #主要布局
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignCenter)
        
        # self.iconWidget = IconWidget(icon, self)
        # self.iconWidget.setFixedSize(80, 80) # 稍微调大一点更有识别度

        self.inputButton = PrimaryPushButton('选择文件', self, FluentIcon.FOLDER_ADD)
        self.inputButton.setMinimumSize(120, 40)
        # self.inputButton.setStyleSheet("""
        #     PushButton {
        #         background-color: rgb(100, 100, 100);
        #         color: white;
        #         border: none;
        #         border-radius: 5px;
        #     }
        #     PushButton:hover {
        #         background-color: rgb(140, 140, 140);
        #     }
        # """)

        self.inputButton.clicked.connect(self._open_file_dialog) 
        
        self.label = SubtitleLabel(title, self)
        self.label.setAlignment(Qt.AlignCenter)
        
        # 添加布局
        self.vBoxLayout.addStretch(1)
        #s elf.vBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignCenter)

        self.vBoxLayout.addWidget(self.label, 0, Qt.AlignCenter)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.inputButton, 0, Qt.AlignCenter)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addStretch(1)

        # 如果父组件存在，安装事件过滤器以劫持父组件的拖放事件
        if parent is not None:
            parent.setAcceptDrops(True)
            parent.installEventFilter(self)

    def eventFilter(self, watched, event):
        """事件过滤器：劫持父页面的拖拽事件"""
        if watched == self.parent():
            if event.type() == QEvent.Type.DragEnter:
                self.dragEnterEvent(event)
                return True
            elif event.type() == QEvent.Type.Drop:
                self.dropEvent(event)
                return True
        return super().eventFilter(watched, event)

    def mouseReleaseEvent(self, event):
        """鼠标点击非按钮区域，也能弹出选择框"""
        if event.button() == Qt.LeftButton:
            self._open_file_dialog()
        super().mouseReleaseEvent(event)
    
    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", self.file_filter)
        if files:
            self.filesReady.emit(files)

    def dragEnterEvent(self, event):
        """拖入文件进入区域时触发"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """在区域内松开鼠标落下文件时触发"""
        urls = event.mimeData().urls()
        # 提取出本地文件的路径
        files = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if files:
            self.filesReady.emit(files)

    def enterEvent(self, event):
        """鼠标进入外围卡片"""
        # 给按钮发送模拟的悬停事件
        enter_event = QEvent(QEvent.Type.Enter)
        QCoreApplication.sendEvent(self.inputButton, enter_event)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开外围卡片"""
        # 给按钮发送模拟的离开事件
        leave_event = QEvent(QEvent.Type.Leave)
        QCoreApplication.sendEvent(self.inputButton, leave_event)
        super().leaveEvent(event)
