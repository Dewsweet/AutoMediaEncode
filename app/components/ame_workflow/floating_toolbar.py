from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QGraphicsDropShadowEffect

from qfluentwidgets import (PrimaryPushButton, ToolButton, TransparentToolButton, FluentIcon as FIF,
                            isDarkTheme, qconfig)


class FloatingToolbar(QFrame):
    start_clicked = Signal()
    pause_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FloatingToolbar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(200, 42)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 5, 4)
        layout.setSpacing(5)

        self._state = 'idle'
        self._drag_pos = None

        self.start_btn = PrimaryPushButton(FIF.PLAY, "开始任务", self)
        self.start_btn.setMinimumWidth(100)

        self.pause_btn = ToolButton(FIF.PAUSE, self)
        self.pause_btn.setFixedSize(32, 32)
        self.pause_btn.setToolTip("暂停")

        self.cancel_btn = ToolButton(FIF.CANCEL, self)
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.setToolTip("取消")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.cancel_btn)
        layout.addStretch()

        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)

        self.set_state('idle')
        self._apply_bg()
        qconfig.themeChanged.connect(self._apply_bg)

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
