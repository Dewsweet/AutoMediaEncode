from PySide6.QtCore import Qt, Signal, QPropertyAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                                QWidget, QGraphicsDropShadowEffect,
                                QStackedWidget, QLabel)

from qfluentwidgets import (ToolButton, FluentIcon as FIF, BodyLabel,
                            isDarkTheme, qconfig)

from .ame_nodes import create_node_widget


class FloatingInspector(QFrame):
    node_param_changed = Signal(str, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FloatingInspector")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._expanded = False
        self._node = None
        self._body_widget = None
        self._bar_w = 300
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
        bar_layout = QHBoxLayout(self._bar)
        bar_layout.setContentsMargins(12, 4, 6, 4)
        bar_layout.setSpacing(6)
        self._title_label = BodyLabel("检查器", self)
        self._title_label.setStyleSheet("color: #888;")
        bar_layout.addWidget(self._title_label)
        bar_layout.addStretch()
        self._arrow_btn = ToolButton(FIF.SETTING, self)
        self._arrow_btn.setFixedSize(26, 26)
        self._arrow_btn.clicked.connect(self._toggle)
        bar_layout.addWidget(self._arrow_btn)
        self._main.addWidget(self._bar)

        self._content = QStackedWidget(self)
        self._content.setVisible(False)
        self._empty_label = BodyLabel("请选择节点", self)
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: #888; padding: 12px;")
        self._body_holder = QWidget(self)
        self._body_holder_layout = QVBoxLayout(self._body_holder)
        self._body_holder_layout.setContentsMargins(12, 4, 12, 8)
        self._content.addWidget(self._empty_label)
        self._content.addWidget(self._body_holder)
        self._content.setCurrentIndex(0)
        self._main.addWidget(self._content)

        self.setFixedSize(self._bar_w, self._bar_h)
        self._apply_bg()
        qconfig.themeChanged.connect(self._apply_bg)

    def _apply_bg(self):
        dark = isDarkTheme()
        if dark:
            self.setStyleSheet(
                "#FloatingInspector { background: #2a2a2a; border-radius: 10px; border: 1px solid #3a3a3a; }"
            )
        else:
            self.setStyleSheet(
                "#FloatingInspector { background: #fafafa; border-radius: 10px; border: 1px solid #ddd; }"
            )

    def is_expanded(self):
        return self._expanded

    def _toggle(self):
        if self._expanded:
            self.collapse()
        else:
            self.expand()

    def expand(self):
        self._expanded = True
        self._content.setVisible(True)
        self._content.setCurrentIndex(0 if self._node is None else 1)
        ch = max(self._compute_body_height() if self._node else 0, 40)
        self.setFixedSize(self._bar_w, self._bar_h + ch)

    def collapse(self):
        self._expanded = False
        self._content.setVisible(False)
        self.setFixedSize(self._bar_w, self._bar_h)

    def set_node(self, node):
        if self._node is node:
            return
        self._node = node

        if self._body_widget:
            self._body_holder_layout.removeWidget(self._body_widget)
            self._body_widget.hide()
            self._body_widget.deleteLater()
            self._body_widget = None

        if node is None:
            if self._expanded:
                self._content.setCurrentIndex(0)
            self._title_label.setText("检查器")
            return

        self._title_label.setText(node.name())

        self._body_widget = create_node_widget(node)
        if self._body_widget is None:
            if self._expanded:
                self._content.setCurrentIndex(0)
            return

        self._body_widget.param_changed.connect(
            lambda k, v: self._on_param(node, k, v)
        )

        params_to_set = {}
        for pname in node.properties():
            val = node.get_property(pname)
            if val is not None:
                params_to_set[pname] = val
        if hasattr(self._body_widget, 'set_params'):
            self._body_widget.set_params(params_to_set)

        self._body_holder_layout.addWidget(self._body_widget)

        if not self._expanded:
            self.expand()
        else:
            self._content.setCurrentIndex(1)
            ch = max(self._compute_body_height(), 40)
            self.setFixedSize(self._bar_w, self._bar_h + ch)

    def _on_param(self, node, key, value):
        if node and node is self._node:
            node.set_property(key, value, push_undo=False)
            self.node_param_changed.emit(node.id, key, value)

    def _compute_body_height(self):
        if self._body_widget:
            sh = self._body_widget.sizeHint()
            return sh.height() + 20
        return 60

    def reposition(self, page_w, page_h):
        self.move(page_w - self.width() - 16, 12)
        if self.y() + self.height() > page_h - 20:
            self.move(self.x(), page_h - self.height() - 20)
