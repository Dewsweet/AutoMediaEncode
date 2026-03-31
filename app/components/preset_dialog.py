# coding:utf-8
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import (MessageBoxBase, SubtitleLabel, BodyLabel, LineEdit, TextEdit, CardWidget, 
                            PushButton, PrimaryPushButton, Action, ToolButton, FluentIcon as FIF,
                            ScrollArea)

from app.services.preset_service import preset_service

class PresetItemCard(CardWidget):
    """预设卡片中, 每一条预设对应的单行卡片, 控件仅有预设名和删改按钮"""
    # 信号：当用户要求编辑此条目 (参数：预设名, 预设参数)
    editRequested = Signal(str, str)
    # 信号：当用户要求删除此条目 (参数：预设名)
    deleteRequested = Signal(str)

    def __init__(self, preset_name, preset_params, parent=None):
        super().__init__(parent=parent)
        self.preset_name = preset_name
        self.preset_params = preset_params
        # 设置卡片边框
        self.setStyleSheet("""CardWidget { border: 1px solid #E0E0E0; border-radius: 5px;}""")
        self.setFixedHeight(60)

        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(20, 5, 20, 5)

        self.nameLabel = BodyLabel(preset_name, self)
        self.nameLabel.setFixedWidth(120)

        self.editButton = ToolButton(FIF.EDIT, self)
        self.deleteButton = ToolButton(FIF.DELETE, self)

        self.hBoxLayout.addWidget(self.nameLabel)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.editButton)
        self.hBoxLayout.addWidget(self.deleteButton)

        self.editButton.clicked.connect(lambda: self.editRequested.emit(self.preset_name, self.preset_params))
        self.deleteButton.clicked.connect(lambda: self.deleteRequested.emit(self.preset_name))

class PresetEditDialog(MessageBoxBase):
    """
    新建或编辑预设的二级小弹窗
    """
    def __init__(self, title_text, init_name="", init_params="", parent=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel(title_text, self)

        # 这边输入预设名
        self.nameLineEdit = LineEdit(self)
        self.nameLineEdit.setPlaceholderText("预设名称 (例如: 日常压制)")
        self.nameLineEdit.setText(init_name)

        # 输入多行参数
        self.paramTextEdit = TextEdit(self)
        self.paramTextEdit.setPlaceholderText("CLI 参数 (例如: --preset veryslow --crf 18 ...)")
        self.paramTextEdit.setText(init_params)
        # 移除固定的setFixedHeight使其能随窗口伸缩
        # self.paramTextEdit.setFixedHeight(120)

        # 将组件添加到 Base 的预留布局 viewLayout 里
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.nameLineEdit)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.paramTextEdit, 1) # 给 textedit 增加拉伸比例

        # 调整自身尺寸为相对主窗口变大的动态尺寸
        if parent:
            target_w = max(450, int(parent.width() * 0.5))
            target_h = max(350, int(parent.height() * 0.5))
            self.widget.setFixedSize(target_w, target_h)
        else:
            self.widget.setMinimumWidth(380)
            self.widget.setMinimumHeight(280)
        
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

    def get_data(self):
        """返回用户填写的名称和参数"""
        return self.nameLineEdit.text().strip(), self.paramTextEdit.toPlainText().strip()


class PresetManagerDialog(MessageBoxBase):
    """
    预设管理主弹窗 (展示列表)
    """
    def __init__(self, encoder_name, parent=None):
        super().__init__(parent)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.encoder_name = encoder_name
        self.titleLabel = BodyLabel(f"{encoder_name} 预设", self)
        self.titleLabel.setContentsMargins(20, 20, 0, 0)
        
        # 将数据拷贝为本地状态，点击"应用"时才真实保存
        self.local_presets = preset_service.get_presets_by_encoder(self.encoder_name).copy()

        # 因为预设可能很多，需要一个滚动区域
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setStyleSheet("background-color: transparent; border: none;")
        # 移除固定高度，使其能随弹窗自适应
        # self.scrollArea.setFixedHeight(340)

        self.scrollWidget = QWidget()
        self.scrollWidget.setStyleSheet("background-color: transparent;")
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setContentsMargins(20, 0, 20, 0)
        self.scrollArea.setWidget(self.scrollWidget)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(15)
        self.viewLayout.addWidget(self.scrollArea, alignment=Qt.AlignTop) 
        self.viewLayout.addStretch(1)

        if parent:
            target_w = max(600, int(parent.width() * 0.75))
            target_h = max(500, int(parent.height() * 0.75))
            self.widget.setFixedSize(target_w, target_h)
        else:
            self.widget.setMinimumWidth(560)
            self.widget.setMinimumHeight(450)

        # 隐藏自带的完成/关闭按钮底栏，我们将自己画
        self.yesButton.hide()
        self.cancelButton.hide()
        self.buttonGroup.hide()  

        # 绘制自定义底部按钮栏
        self._init_custom_buttons()

        self.refresh_list()

    def _init_custom_buttons(self):
        # 创建新的底部容器
        self.customButtonLayout = QHBoxLayout()
        # 按照需求调边距，保持和上面统一的 20 像素边距
        self.customButtonLayout.setContentsMargins(20, 5, 20, 20)
        
        self.addBtn = PushButton("添加", self)
        self.addBtn.setFixedWidth(100)
        self.defaultBtn = PushButton("默认", self)
        self.defaultBtn.setFixedWidth(100)
        self.applyBtn = PrimaryPushButton("应用", self)
        self.applyBtn.setFixedWidth(100)
        self.customCancelBtn = PushButton("取消", self)
        self.customCancelBtn.setFixedWidth(100)
        
        self.customButtonLayout.addWidget(self.addBtn)
        self.customButtonLayout.addSpacing(10)
        self.customButtonLayout.addWidget(self.defaultBtn)
        self.customButtonLayout.addStretch(1)
        self.customButtonLayout.addWidget(self.applyBtn)
        self.customButtonLayout.addSpacing(10)
        self.customButtonLayout.addWidget(self.customCancelBtn)
        
        self.viewLayout.addLayout(self.customButtonLayout)
        
        # 绑定事件
        self.addBtn.clicked.connect(self._on_add_clicked)
        self.defaultBtn.clicked.connect(self._on_default_clicked)
        self.applyBtn.clicked.connect(self._on_apply_clicked)
        self.customCancelBtn.clicked.connect(self.reject)

    def refresh_list(self):
        """重绘列表"""
        # 彻底清空布局中的所有元素，必须连同残余的弹簧(QSpacerItem)一起清空，否则会导致排版慢慢居中
        while self.scrollLayout.count():
            item = self.scrollLayout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None) # 立即从父控件切断，解决残影问题
                widget.deleteLater()
        
        for name, params in self.local_presets.items():
            item_widget = PresetItemCard(name, params, self)
            item_widget.editRequested.connect(self._on_edit_clicked)
            item_widget.deleteRequested.connect(self._on_delete_clicked)
            self.scrollLayout.addWidget(item_widget)
            
        self.scrollLayout.addStretch(1)
        # 强制触发一次界面的重绘，确保删除时的残影横线立刻消失
        self.scrollWidget.update()

    def _on_add_clicked(self):
        dialog = PresetEditDialog("新建预设", parent=self.window())
        if dialog.exec():
            name, params = dialog.get_data()
            if name and params:
                self.local_presets[name] = params
                self.refresh_list()

    def _on_edit_clicked(self, old_name, old_params):
        dialog = PresetEditDialog(f"编辑: {old_name}", old_name, old_params, parent=self.window())
        if dialog.exec():
            new_name, new_params = dialog.get_data()
            if new_name and new_params:
                if new_name != old_name:
                    del self.local_presets[old_name]
                self.local_presets[new_name] = new_params
                self.refresh_list()

    def _on_delete_clicked(self, name):
        if name in self.local_presets:
            del self.local_presets[name]
        self.refresh_list()

    def _on_default_clicked(self):
        """恢复默认预设 (重新从模板读取)"""
        default_presets = preset_service.get_default_presets_by_encoder(self.encoder_name)
        if default_presets:
            self.local_presets = default_presets.copy()
            self.refresh_list()

    def _on_apply_clicked(self):
        """保存所有改动到本地"""
        data = preset_service.load_all_presets()
        data[self.encoder_name] = self.local_presets
        preset_service.save_all_presets(data)
        self.accept()