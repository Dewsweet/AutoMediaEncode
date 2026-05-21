from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                                QWidget, QGraphicsDropShadowEffect,
                                QStackedWidget, QLabel)

from qfluentwidgets import (ToolButton, FluentIcon as FIF, BodyLabel,
                            isDarkTheme, qconfig)


class FloatingInspector(QFrame):
    node_param_changed = Signal(str, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('FloatingInspector')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._expanded = False
        self._node = None
        self._body = None
        self._bar_w = 320
        self._bar_h = 36

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        self._main = QVBoxLayout(self)
        self._main.setContentsMargins(0, 0, 0, 0)
        self._main.setSpacing(0)

        self._bar = QWidget(self)
        self._bar.setFixedHeight(self._bar_h)
        bl = QHBoxLayout(self._bar)
        bl.setContentsMargins(12, 4, 6, 4)
        bl.setSpacing(6)
        self._desc = BodyLabel('', self)
        self._desc.setStyleSheet('color:#888;font-size:11px;')
        bl.addWidget(self._desc, 1)
        self._gear = ToolButton(FIF.SETTING, self)
        self._gear.setFixedSize(26, 26)
        self._gear.clicked.connect(self._toggle)
        bl.addWidget(self._gear)
        self._main.addWidget(self._bar)

        self._stack = QStackedWidget(self)
        self._stack.setVisible(False)
        self._empty = BodyLabel('请选择一个节点', self)
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet('color:#888;padding:12px;')
        self._holder = QWidget(self)
        self._hlay = QVBoxLayout(self._holder)
        self._hlay.setContentsMargins(12, 4, 12, 8)
        self._stack.addWidget(self._empty)
        self._stack.addWidget(self._holder)
        self._stack.setCurrentIndex(0)
        self._main.addWidget(self._stack)

        self.setFixedSize(self._bar_w, self._bar_h)
        self._apply_bg()
        qconfig.themeChanged.connect(self._apply_bg)

    def _apply_bg(self):
        d = isDarkTheme()
        self.setStyleSheet(
            f"#FloatingInspector{{background:{'#2a2a2a' if d else '#fafafa'};border-radius:10px;border:1px solid {'#3a3a3a' if d else '#ddd'};}}"
        )

    def is_expanded(self):
        return self._expanded

    def _toggle(self):
        if self._expanded: self.collapse()
        else: self.expand()

    def expand(self):
        self._expanded = True
        self._stack.setVisible(True)
        self._stack.setCurrentIndex(0 if self._node is None else 1)
        ch = max(self._ch(), 40)
        self.setFixedSize(self._bar_w, self._bar_h + ch)

    def collapse(self):
        self._expanded = False
        self._stack.setVisible(False)
        self.setFixedSize(self._bar_w, self._bar_h)

    def _ch(self):
        return 60

    def set_node(self, node):
        if self._node is node:
            return
        self._node = node
        if self._body:
            self._hlay.removeWidget(self._body)
            self._body.hide()
            self._body.deleteLater()
            self._body = None
        if node is None:
            self._desc.setText('')
            if self._expanded: self._stack.setCurrentIndex(0)
            return
        desc = getattr(node, 'DESCRIPTION', '') or node.name()
        self._desc.setText(desc)
        w = node.get_inspector_widget()
        if w is None:
            if self._expanded: self._stack.setCurrentIndex(0)
            return
        self._body = w
        self._hlay.addWidget(self._body)
        if not self._expanded:
            self.expand()
        else:
            self._stack.setCurrentIndex(1)
            ch = max(self._ch(), 40)
            self.setFixedSize(self._bar_w, self._bar_h + ch)

    def reposition(self, pw, ph):
        self.move(pw - self.width() - 16, 12)
        if self.y() + self.height() > ph - 20:
            self.move(self.x(), ph - self.height() - 20)
