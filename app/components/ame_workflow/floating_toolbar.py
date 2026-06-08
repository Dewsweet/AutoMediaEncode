from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QGraphicsDropShadowEffect, QWidget

from qfluentwidgets import (PrimaryPushButton, ToolButton, TransparentToolButton, PushButton, FluentIcon as FIF,
                            isDarkTheme, qconfig)


class FloatingToolbar(QFrame):
    start_clicked = Signal()
    pause_clicked = Signal()
    cancel_clicked = Signal()
    save_clicked = Signal()
    load_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FloatingToolbar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(230, 46)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        self._main = QVBoxLayout(self)
        self._main.setContentsMargins(10, 4, 5, 4)
        self._main.setSpacing(2)

        # row 1: 操作按钮 + gear
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(4)

        self._state = 'idle'
        self._drag_pos = None
        self._expanded = False

        self.start_btn = PrimaryPushButton(FIF.PLAY, "开始任务", self)
        self.start_btn.setMinimumWidth(100)

        self.pause_btn = ToolButton(FIF.PAUSE, self)
        self.pause_btn.setFixedSize(32, 32)
        self.pause_btn.setToolTip("暂停")

        self.cancel_btn = ToolButton(FIF.CANCEL, self)
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.setToolTip("取消")

        self.gear_btn = ToolButton(FIF.SETTING, self)
        self.gear_btn.setFixedSize(32, 32)
        self.gear_btn.setToolTip("更多设置")
        self.gear_btn.clicked.connect(self._toggle_expand)

        row1.addWidget(self.start_btn)
        row1.addWidget(self.pause_btn)
        row1.addWidget(self.cancel_btn)
        row1.addStretch()
        row1.addWidget(self.gear_btn)

        # row 2: 功能按钮 (默认隐藏)
        self._row2 = QWidget(self)
        self._row2.setVisible(False)
        row2_layout = QHBoxLayout(self._row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(4)

        self.save_btn = PushButton(FIF.SAVE, '保存', self)
        self.save_btn.setFixedHeight(32)
        self.save_btn.setToolTip("保存工作流")

        self.load_btn = PushButton(FIF.FOLDER, '加载',self)
        self.load_btn.setFixedHeight(32)
        self.load_btn.setToolTip("加载工作流")

        row2_layout.addStretch()
        row2_layout.addWidget(self.save_btn)
        row2_layout.addWidget(self.load_btn)
        row2_layout.addStretch()

        self._main.addLayout(row1)
        self._main.addWidget(self._row2)

        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        self.save_btn.clicked.connect(self.save_clicked.emit)
        self.load_btn.clicked.connect(self.load_clicked.emit)

        self.set_state('idle')
        self._apply_bg()
        qconfig.themeChanged.connect(self._apply_bg)

    def _toggle_expand(self):
        self._expanded = not self._expanded
        self._row2.setVisible(self._expanded)
        if self._expanded:
            self.setFixedHeight(78)
        else:
            self.setFixedHeight(46)

    def _apply_bg(self):
        dark = isDarkTheme()
        if dark:
            self.setStyleSheet(
                "#FloatingToolbar { background: #2a2a2a; border-radius: 10px; border: 1px solid #3a3a3a; }"
            )
        else:
            self.setStyleSheet(
                "#FloatingToolbar { background: #fafafa; border-radius: 10px; border: 1px solid #ddd; }"
            )

    def set_state(self, state: str):
        self._state = state
        if state == 'running':
            self.start_btn.setEnabled(False)
            self.start_btn.setText("运行中")
            self.pause_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
        elif state == 'paused':
            self.start_btn.setEnabled(True)
            self.start_btn.setText("继续")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(True)
            self.start_btn.setText("开始任务")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """实现拖拽移动浮动工具栏，自动限制在父窗口内"""
        if self._drag_pos is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            parent = self.parent()
            if parent:
                pw = parent.width(); ph = parent.height()
                w = self.width(); h = self.height()
                if new_pos.x() < 0: new_pos.setX(0)
                if new_pos.y() < 0: new_pos.setY(0)
                if new_pos.x() + w > pw: new_pos.setX(pw - w)
                if new_pos.y() + h > ph: new_pos.setY(ph - h)
            self.move(new_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
