"""AME 工作流加载页 — 卡片网格 + 底部按钮栏"""
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QLabel, QFileDialog)

from qfluentwidgets import (TitleLabel, BodyLabel, CaptionLabel, PrimaryPushButton, PushButton,
                            RoundMenu, Action, InfoBar, InfoBarPosition,
                            isDarkTheme, FluentIcon as FIF, FlowLayout,
                            MessageBoxBase, LineEdit, ElevatedCardWidget, ScrollArea)

from app.services.ame_workflow.ame_preset_service import preset_service, WorkflowInfo


class NameInputDialog(MessageBoxBase):
    def __init__(self, title, label, parent=None):
        super().__init__(parent)
        self.widget.setMinimumSize(QSize(300, 200))
        self._label = BodyLabel(label, self)
        self._edit = LineEdit(self)
        self.viewLayout.addWidget(self._label)
        self.viewLayout.addWidget(self._edit)
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

    def get_text(self):
        return self._edit.text()


class WorkflowCard(ElevatedCardWidget):
    card_clicked = Signal(WorkflowInfo)
    double_clicked = Signal(WorkflowInfo)
    delete_requested = Signal(WorkflowInfo)
    rename_requested = Signal(WorkflowInfo)
    set_thumb_requested = Signal(WorkflowInfo)

    def __init__(self, info: WorkflowInfo, parent=None):
        super().__init__(parent)
        self._info = info
        self.setFixedSize(200, 175)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(4)

        self._thumb = QLabel(self)
        self._thumb.setFixedSize(184, 108)
        self._load_thumbnail()
        layout.addWidget(self._thumb, alignment=Qt.AlignCenter)

        self._name_label = BodyLabel(self._info.name[:24], self)
        font = self._name_label.font()
        font.setBold(True)
        font.setPointSize(10)
        self._name_label.setFont(font)
        layout.addWidget(self._name_label)

        tm = self._info.modified.strftime('%Y-%m-%d %H:%M')
        self._time_label = CaptionLabel(tm, self)
        layout.addWidget(self._time_label)

    def _load_thumbnail(self):
        pix = None
        if self._info.thumbnail and self._info.thumbnail.exists():
            pix = QPixmap(str(self._info.thumbnail))
        if not pix or pix.isNull():
            pix = QPixmap(':app/images/default_project.png')
        if pix and not pix.isNull():
            scaled = pix.scaled(184, 108, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            if scaled.width() > 184 or scaled.height() > 108:
                x = (scaled.width() - 184) // 2
                y = (scaled.height() - 108) // 2
                scaled = scaled.copy(x, y, 184, 108)
            self._thumb.setPixmap(scaled)

    def info(self):
        return self._info

    def set_selected(self, on: bool):
        if on:
            color = "#dcdcdc" if isDarkTheme() else "#333333"
            self.setStyleSheet(
                "ElevatedCardWidget { border: 2px solid " + color + "; border-radius: 8px; }")
        else:
            self.setStyleSheet("")

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self._info)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.card_clicked.emit(self._info)

    def contextMenuEvent(self, event):
        menu = RoundMenu(parent=self)
        menu.addAction(Action("删除", triggered=lambda: self.delete_requested.emit(self._info)))
        menu.addAction(Action("重命名", triggered=lambda: self.rename_requested.emit(self._info)))
        menu.addAction(Action("设置封面", triggered=lambda: self.set_thumb_requested.emit(self._info)))
        menu.exec(event.globalPos())


class AMELoaderPage(QWidget):
    workflow_selected = Signal(str)
    new_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('AMELoaderPage')
        self._cards = []
        self._selected = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(10)

        title = TitleLabel("节点式工作流", self)
        # desc = CaptionLabel("可视化编辑节点 快速搭建编码工作流", self)

        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        # layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(5)

        self._scroll = ScrollArea(self)
        self._scroll.setObjectName("AMELoaderScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget(self._scroll)
        container.setObjectName("AMELoaderContainer")
        container.setContentsMargins(20, 0, 20, 0)
        self._flow = FlowLayout(container, needAni=False)
        self._flow.setSpacing(12)
        self._scroll.setWidget(container)
        layout.addWidget(self._scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 0, 20, 0)
        btn_row.setSpacing(10)
        self._new_btn = PrimaryPushButton(FIF.ADD, "新建", self)
        self._open_btn = PushButton(FIF.PLAY, "打开", self)
        self._open_btn.setEnabled(False)
        self._import_btn = PushButton(FIF.DOWN, "导入", self)
        self._export_btn = PushButton(FIF.UP, "导出", self)
        self._export_btn.setEnabled(False)
        for btn in [self._new_btn, self._open_btn, self._import_btn, self._export_btn]:
            btn.setFixedHeight(32)
            btn.setFixedWidth(120)
        btn_row.addWidget(self._new_btn)
        btn_row.addWidget(self._open_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._import_btn)
        btn_row.addWidget(self._export_btn)
        layout.addLayout(btn_row)

        self._new_btn.clicked.connect(self._on_new)
        self._open_btn.clicked.connect(self._on_open)
        self._import_btn.clicked.connect(self._on_import)
        self._export_btn.clicked.connect(self._on_export)

    def load(self):
        self._clear_cards()
        for info in preset_service.list_workflows():
            self._add_card(info)

    def _clear_cards(self):
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

    def _add_card(self, info):
        card = WorkflowCard(info, self._scroll)
        card.card_clicked.connect(self._on_card_clicked)
        card.double_clicked.connect(self._on_card_double)
        card.delete_requested.connect(self._on_card_delete)
        card.rename_requested.connect(self._on_card_rename)
        card.set_thumb_requested.connect(self._on_card_thumb)
        self._flow.addWidget(card)
        self._cards.append(card)

    def _on_card_clicked(self, info):
        for c in self._cards:
            c.set_selected(c.info() is info)
        self._selected = info
        self._open_btn.setEnabled(True)
        self._export_btn.setEnabled(True)
        self._export_btn.setEnabled(True)

    def _on_card_double(self, info):
        self._selected = info
        self._emit_selected()

    def _on_card_delete(self, info):
        preset_service.delete(info.name)
        self._selected = None
        self._open_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        self.load()

    def _on_card_rename(self, info):
        dlg = NameInputDialog("重命名", "新名称:", self.window())
        dlg._edit.setText(info.name)
        if dlg.exec():
            new_name = dlg.get_text().strip()
            if new_name and new_name != info.name:
                preset_service.rename(info.name, new_name)
                self.load()

    def _on_card_thumb(self, info):
        path, _ = QFileDialog.getOpenFileName(self, "选择封面", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            preset_service.set_thumbnail(info.name, path)
            self.load()

    def _on_new(self):
        self.new_requested.emit()

    def _on_open(self):
        self._emit_selected()

    def _emit_selected(self):
        if self._selected:
            self.workflow_selected.emit(self._selected.name)

    def mousePressEvent(self, event):
        child = self.childAt(event.pos())
        while child and child is not self:
            if isinstance(child, WorkflowCard):
                super().mousePressEvent(event)
                return
            child = child.parentWidget()
        for c in self._cards:
            c.set_selected(False)
        self._selected = None
        self._open_btn.setEnabled(False)
        self._export_btn.setEnabled(False)
        super().mousePressEvent(event)

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入 JSON", "", "JSON (*.json)")
        if path:
            name = preset_service.import_file(path)
            if name:
                self.load()
                InfoBar.success(
                    title="已导入", 
                    content=f"工作流: {name}",
                    orient=Qt.Horizontal, 
                    isClosable=False,
                    position=InfoBarPosition.TOP_RIGHT, 
                    duration=2000, 
                    parent=self
                    )

    def _on_export(self):
        if not self._selected:
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 JSON", "", "JSON (*.json)")
        if path:
            preset_service.export(self._selected.name, path)
            InfoBar.success(
                title="已导出", 
                content=f"工作流已导出",
                orient=Qt.Horizontal, 
                isClosable=False, 
                position=InfoBarPosition.TOP_RIGHT, 
                duration=2000, 
                parent=self
                )
