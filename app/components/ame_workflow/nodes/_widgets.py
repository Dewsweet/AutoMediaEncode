from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QFrame, QApplication
from qfluentwidgets import PushButton, PrimaryPushButton, LineEdit, ComboBox, SwitchButton, BodyLabel, TextEdit, RoundMenu, Action, Slider, TransparentPushButton, TransparentToolButton, MessageBoxBase, FluentIcon as FIF
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
from app.services.setting.preset_service import preset_service

class NodeComboBox(PushButton):
    """
    使用 RoundMune + PushButton 实现的顶层浮动 ComboBox 替代方案，解决 NodeGraphQt 中 ComboBox 的显示异样问题
    """
    currentTextChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(100)
        self._items = []
        self._current_text = ""
        self._menu = None
        self.clicked.connect(self._show_floating_menu)

    def addItems(self, items):
        for item in items:
            self.addItem(item)

    def addItem(self, text, user_data=None): 
        self._items.append({"text": text, "data": user_data})
        if not self._current_text:
            self.setCurrentText(text)

    def currentText(self):
        return self._current_text

    def setCurrentText(self, text):
        self._current_text = text
        self.setText(text)

    def clear(self):
        self._items.clear()
        self.setText("")
        self._current_text = ""

    def _show_floating_menu(self):
        if not self._items:
            return
        # 设置 parent=None让其跳出 QGraphicsScene
        self._menu = RoundMenu(parent=None)
        
        for item in self._items:
            action = Action(item["text"])
            action.triggered.connect(lambda checked=False, t=item["text"]: self._on_item_selected(t))
            self._menu.addAction(action)
            
        self._menu.exec(QCursor.pos())

    def _on_item_selected(self, text):
        self.setCurrentText(text)
        self.currentTextChanged.emit(text)

class NodeComboBoxWidget(NodeBaseWidget):
    def __init__(self, parent, name, items):
        super().__init__(parent, name)
        self._combo = NodeComboBox()
        self._combo.addItems(items)
        self._combo.currentTextChanged.connect(lambda t: self.on_value_changed(t))
        self.set_custom_widget(self._combo)

    def get_value(self):
        return self._combo.currentText()

    def set_value(self, value):
        if value:
            self._combo.setCurrentText(str(value))


class PathBrowseWidget(NodeBaseWidget):
    def __init__(self, parent, name, btn_text='浏览'):
        super().__init__(parent, name)
        self.btn_text = btn_text
        row = QWidget()
        row.setMinimumWidth(240)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self._btn = PushButton(self.btn_text, row)
        self._btn.setFixedHeight(32)
        self._btn.clicked.connect(self._browse)

        self._edit = LineEdit(row)
        self._edit.setFixedHeight(32)
        # self._edit.setPlaceholderText('选择路径...')
        self._edit.textChanged.connect(lambda t: self.on_value_changed(t))
        layout.addWidget(self._btn)
        layout.addWidget(self._edit)
        self.set_custom_widget(row)

    def _browse(self):
        pass

    def get_value(self):
        return self._edit.text()

    def set_value(self, value):
        if value:
            self._edit.setText(str(value))

class DirBrowseWidget(PathBrowseWidget):
    def __init__(self, parent, name, btn_text='选择文件夹'):
        super().__init__(parent, name, btn_text=btn_text)

    def _browse(self):
        p = QFileDialog.getExistingDirectory(None, '选择目录')
        if p:
            self._edit.setText(p)

class FileBrowseWidget(PathBrowseWidget):
    def __init__(self, parent, name, btn_text='选择输入文件', exts=''):
        self._ext_filter = exts
        super().__init__(parent, name, btn_text=btn_text)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(None, '选择文件', '', self._ext_filter or 'All Files (*)')
        if p:
            self._edit.setText(p)

class FilesBrowseWidget(NodeBaseWidget):
    def __init__(self, parent, name, btn_text='选择多个输入文件', exts=''):
        super().__init__(parent, name)
        self._ext_filter = exts
        self.btn_text = btn_text
        
        row = QWidget()
        row.setMinimumWidth(240)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self._btn = PushButton(self.btn_text, row)
        self._btn.setFixedHeight(32)
        self._btn.clicked.connect(self._browse)

        self._edit = TextEdit(row)
        self._edit.setPlaceholderText('此处显示选择的多个路径，每行一个...')
        self._edit.setMinimumHeight(64)
        self._edit.setMaximumHeight(140)
        self._edit.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        
        layout.addWidget(self._btn)
        layout.addWidget(self._edit)
        self.set_custom_widget(row)
        
    def _browse(self):
        paths, _ = QFileDialog.getOpenFileNames(None, '选择文件', '', self._ext_filter or 'All Files (*)')
        if paths:
            self._edit.setPlainText('\n'.join(paths))

    def get_value(self):
        return self._edit.toPlainText()

    def set_value(self, value):
        if value:
            self._edit.setPlainText(str(value))


class PresetSwitchWidget(NodeBaseWidget):
    def __init__(self, parent, name, encoder_type='x264'):
        super().__init__(parent, name)
        self._enc = encoder_type
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        self._sw = SwitchButton(row)
        self._sw.setChecked(True)
        self._sw.setOnText('')
        self._sw.setOffText('')
        self._sw.checkedChanged.connect(self._on_change)

        self._cb = NodeComboBox(row)
        self._cb.currentTextChanged.connect(self._on_change)

        # 预加载数据
        enc_key = {'x264': 'x264', 'x265': 'x265', 'svtav1': 'SVTAV1'}.get(self._enc , self._enc)
        try:
            presets = list(preset_service.get_presets_by_encoder(enc_key).keys())
            if presets:
                self._cb.addItems(presets)
            else:
                self._cb.addItem('(无)')
        except Exception:
            pass

        layout.addWidget(BodyLabel('使用预设:', row))
        layout.addWidget(self._sw)
        layout.addWidget(self._cb)
        self.set_custom_widget(row)

    def _on_change(self, *_):
        self.on_value_changed(self.get_value())

    def get_value(self):
        return {'use_preset': self._sw.isChecked(),
                'preset': self._cb.currentText() if self._sw.isChecked() else ''}

    def set_value(self, value):
        if isinstance(value, dict): 
            self._sw.setChecked(value.get('use_preset', True))
            if value.get('preset'):
                self._cb.setCurrentText(value['preset'])

class FfmpegSimpleOptionsWidget(NodeBaseWidget):
    def __init__(self, parent, name, coder_items):
        super().__init__(parent, name)

        mianbox = QWidget()
        mainLayout = QVBoxLayout(mianbox)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        self._encoderLabel = BodyLabel('编码器选项:', mianbox)
        self._encoder = NodeComboBox(mianbox)
        self._encoder.addItems(coder_items)

        self._customLabel = BodyLabel('自定义参数:', mianbox)
        self._customEdit = TextEdit(mianbox)
        self._customEdit.setPlaceholderText('输入自定义 FFmpeg CLI 参数...')
        self._customEdit.setMinimumHeight(64)
        self._customEdit.setMaximumHeight(100)

        mainLayout.addWidget(self._encoderLabel)
        mainLayout.addWidget(self._encoder)
        mainLayout.addWidget(self._customLabel)
        mainLayout.addWidget(self._customEdit)
        self.set_custom_widget(mianbox)

        self._connect_signals()

    def _connect_signals(self):
        self._encoder.currentTextChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._customEdit.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
    
    def get_value(self):
        return {
            'encoder': self._encoder.currentText(),
            'custom_cli': self._customEdit.toPlainText()
        }
    def set_value(self, value):
        if isinstance(value, dict):
            encoder = value.get('encoder', '')
            custom_cli = value.get('custom_cli', '')
            self._encoder.setCurrentText(encoder)
            self._customEdit.setPlainText(custom_cli)

class StapleAudioEncoderWidget(NodeBaseWidget):
    def __init__(self, parent, name, encoder_name='aac'):
        super().__init__(parent, name)
        self._encoder_name = encoder_name

        self.mainbox = QWidget()
        self.mainLayout = QVBoxLayout(self.mainbox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(10)
        self.modelHLayout = QHBoxLayout()
        self.modelHLayout.setContentsMargins(0, 0, 0, 0)
        self.modelHLayout.setSpacing(10)
        self.compressHLayout = QHBoxLayout()
        self.compressHLayout.setContentsMargins(0, 0, 0, 0)

        self._encoderModelLabel = BodyLabel('CVBR:', self.mainbox)
        self._encoderModelLine = LineEdit(self.mainbox)
        self._encoderModelLine.setFixedWidth(60)
        self._encoderModelUnit = BodyLabel('kbps', self.mainbox)

        self._encoderParamLine = TextEdit(self.mainbox)
        self._encoderParamLine.setPlaceholderText('输入自定义 CLI 参数...')
        self._encoderParamLine.setMinimumSize(220, 100)
        self._encoderParamLine.setMaximumHeight(140)

        self._comoressLevelSlider = Slider(Qt.Horizontal, self.mainbox)
        self._comoressLevelSlider.setRange(0, 8)
        self._comoressLevelSlider.setValue(5)
        self._comoressLevelSliderText = BodyLabel('5', self.mainbox)

        self.modelHLayout.addWidget(self._encoderModelLabel)
        self.modelHLayout.addWidget(self._encoderModelLine)
        self.modelHLayout.addWidget(self._encoderModelUnit)
        self.modelHLayout.addStretch(1) 

        self.compressHLayout.addWidget(self._comoressLevelSlider)
        self.compressHLayout.addWidget(self._comoressLevelSliderText)

        self._encoder_select()
        self._connect_signals()
    
    def _connect_signals(self):
        self._encoderModelLine.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._encoderParamLine.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._comoressLevelSlider.valueChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._comoressLevelSlider.valueChanged.connect(lambda v: self._comoressLevelSliderText.setText(str(v)))

    def _encoder_select(self):
        if self._encoder_name == 'aac':
            self._encoderModelLabel.setText('CVBR:')
            self._comoressLevelSlider.setVisible(False)
            self._comoressLevelSliderText.setVisible(False)
            self.mainLayout.addLayout(self.modelHLayout)
            self.mainLayout.addWidget(self._encoderParamLine)
            self.set_custom_widget(self.mainbox)
        elif self._encoder_name == 'opus':
            self._encoderModelLabel.setText('VBR:')
            self._comoressLevelSlider.setVisible(False)
            self._comoressLevelSliderText.setVisible(False)
            self.mainLayout.addLayout(self.modelHLayout)
            self.mainLayout.addWidget(self._encoderParamLine)
            self.set_custom_widget(self.mainbox)
        elif self._encoder_name == 'flac':
            self._encoderModelLabel.setText('压缩级别:')
            self._encoderParamLine.setVisible(False)
            self._encoderModelLine.setVisible(False)
            self._encoderModelUnit.setVisible(False)
            self.mainLayout.addWidget(self._encoderModelLabel)
            self.mainLayout.addLayout(self.compressHLayout)
            self.set_custom_widget(self.mainbox)
    
    def get_value(self):
        value = {
            'encoder': self._encoder_name,
            'custom_cli': self._encoderParamLine.toPlainText()
        }
        if self._encoder_name == 'flac':
            value['compression_level'] = self._comoressLevelSlider.value()
        elif self._encoder_name in ('aac', 'opus'):
            value['bitrate'] = self._encoderModelLine.text()
        return value
    def set_value(self, value):
        if isinstance(value, dict):
            custom_cli = value.get('custom_cli', '')
            self._encoderParamLine.setText(custom_cli)
            if self._encoder_name == 'flac':
                compression_level = value.get('compression_level', 5)
                self._comoressLevelSlider.setValue(compression_level)
                self._comoressLevelSliderText.setText(str(compression_level))
            elif self._encoder_name in ('aac', 'opus'):
                bitrate = value.get('bitrate', '')
                self._encoderModelLine.setText(bitrate)
        
class CLITextWidget(NodeBaseWidget):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self._edit = TextEdit()
        self._edit.setPlaceholderText('自定义 CLI 参数(不含输入输出部分)...')
        self._edit.setMinimumHeight(48)
        self._edit.setMaximumHeight(100)
        self._edit.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self.set_custom_widget(self._edit)

    def get_value(self):
        return self._edit.toPlainText()

    def set_value(self, value):
        if value:
            self._edit.setPlainText(str(value))

class MkvTrackConfigDialog(MessageBoxBase):
    def __init__(self, parent=None, title='轨道设置', data=None):
        super().__init__(parent)
        self.titleLabel = BodyLabel(title, self)

        self.defaultTrackHLayout = QHBoxLayout()
        self._defaultTrackLabel = BodyLabel('默认轨道:', self)
        self._defaultTrackSwitch = SwitchButton(self)
        self._defaultTrackSwitch.setOnText('是')
        self._defaultTrackSwitch.setOffText('否')
        self.defaultTrackHLayout.addWidget(self._defaultTrackLabel)
        self.defaultTrackHLayout.addWidget(self._defaultTrackSwitch)
        self.defaultTrackHLayout.addStretch(1)

        self.trackLanguageHLayout = QHBoxLayout()
        self._trackLanguageLabel = BodyLabel('语言:', self)
        self._trackLanguageEdit = LineEdit(self)
        self._trackLanguageEdit.setPlaceholderText('')
        self.trackLanguageHLayout.addWidget(self._trackLanguageLabel)
        self.trackLanguageHLayout.addWidget(self._trackLanguageEdit)

        self.trackNameHLayout = QHBoxLayout()
        self._trackNameLabel = BodyLabel('名称:', self)
        self._trackNameEdit = LineEdit(self)
        self.trackNameHLayout.addWidget(self._trackNameLabel)
        self.trackNameHLayout.addWidget(self._trackNameEdit)

        self.trackCustomVLayout = QVBoxLayout()
        self._trackCustomLabel = BodyLabel('自定义轨道参数:', self)
        self._trackCustomEdit = TextEdit(self)
        self._trackCustomEdit.setPlaceholderText('输入轨道额外参数...')
        self._trackCustomEdit.setMinimumHeight(80)
        self._trackCustomEdit.setMaximumHeight(150)
        self.trackCustomVLayout.addWidget(self._trackCustomLabel)
        self.trackCustomVLayout.addWidget(self._trackCustomEdit)
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addLayout(self.defaultTrackHLayout)
        self.viewLayout.addLayout(self.trackLanguageHLayout)
        self.viewLayout.addLayout(self.trackNameHLayout)
        self.viewLayout.addLayout(self.trackCustomVLayout)

        if parent:
            target_w = 350
            target_h = 250
            self.widget.setMinimumSize(target_w, target_h)
        
        self.yesButton.setText("确认")
        self.cancelButton.setText("取消")

        if data:
            self._defaultTrackSwitch.setChecked(data.get('default_track', False))
            self._trackLanguageEdit.setText(data.get('track_language', ''))
            self._trackNameEdit.setText(data.get('track_name', ''))
            self._trackCustomEdit.setPlainText(data.get('track_custom', ''))

    def get_data(self):
        return {
            'default_track': self._defaultTrackSwitch.isChecked(),
            'track_language': self._trackLanguageEdit.text(),
            'track_name': self._trackNameEdit.text(),
            'track_custom': self._trackCustomEdit.toPlainText()
        }

class MkvInlineConfigButton(NodeBaseWidget):
    addRequested = Signal(str)

    def __init__(self, parent, name, port_name, mode='base'):
        super().__init__(parent, name)
        self.port_name = port_name
        self._mode = mode  
        self.mainbox = QWidget()
        self.mainbox.setAttribute(Qt.WA_TranslucentBackground, True) # 设置背景透明 
        self.mainbox.setStyleSheet('background: transparent;') 
        layout = QHBoxLayout(self.mainbox)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(4)

        self.btn = TransparentPushButton('轨道设置', self.mainbox)
        self.btn.clicked.connect(self._open_dialog)
        layout.addWidget(self.btn)

        if self._mode == 'base':
            self._extra_btn = TransparentToolButton(FIF.ADD, self.mainbox)
            self._extra_btn.setFixedSize(28, 28)
            self._extra_btn.setAttribute(Qt.WA_TranslucentBackground, True)
            self._extra_btn.setStyleSheet('background: transparent; border: none;')
            self._extra_btn.clicked.connect(lambda: self.addRequested.emit(self.port_name))
            layout.addWidget(self._extra_btn)

        self.set_custom_widget(self.mainbox)
        try:
            group = self.widget()
            group.setFlat(True)
            group.setStyleSheet(
                'QGroupBox { background: transparent; border: 0px; margin-top: 0px; padding: 0px; }'
                'QGroupBox::title { color: transparent; background: transparent; }'
            )
        except Exception:
            pass
        self._value = {}

    def _open_dialog(self):
        title_map = {'video': '视频', 'audio': '音频', 'subtitle': '字幕', 'chapter': '章节', 'attachment': '附件'}

        # 兼容 track_1_video 等动态命名格式
        lookup_name = self.port_name
        if "track_" in self.port_name:
            lookup_name = self.port_name.split("_")[-1]

        title_prefix = title_map.get(lookup_name, self.port_name)
        dialog = MkvTrackConfigDialog(QApplication.activeWindow(), f'{title_prefix} 参数设置', self._value)
        if dialog.exec():
            self._value = dialog.get_data()
            self.on_value_changed(self._value)

    def get_value(self):
        return self._value

    def set_value(self, value):
        if isinstance(value, dict):
            self._value = value

class CustomNameWidget(NodeBaseWidget):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.mainbox = QWidget()
        self.mainLaoyut = QVBoxLayout(self.mainbox)
        self.mainLaoyut.setContentsMargins(0, 0, 0, 0)

        self.btnHLayout = QHBoxLayout()

        self._nameLabel = BodyLabel('自定义文件名称:', self.mainbox)
        self._nameEdit = TextEdit(self.mainbox)
        self._nameEdit.setPlaceholderText('输入自定义文件名称, 不要输入扩展名')
        self._nameEdit.setMaximumHeight(60)
        self._nameEdit.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._placeHolderBtn = PushButton('添加', self.mainbox)
        self._clearBtn = PushButton('清除', self.mainbox)

        self._placeHolderBtn.clicked.connect(self._add_placeholder)
        self._clearBtn.clicked.connect(lambda: self._nameEdit.clear())

        self.btnHLayout.addWidget(self._placeHolderBtn)
        self.btnHLayout.addWidget(self._clearBtn)
        
        self.mainLaoyut.addWidget(self._nameLabel)
        self.mainLaoyut.addWidget(self._nameEdit)
        self.mainLaoyut.addLayout(self.btnHLayout)
        self.set_custom_widget(self.mainbox)

    def _add_placeholder(self):
        menu = RoundMenu()
        placeholders = {
            '输入文件名': '{input_name}',
            '日期时间': '{datetime}',
        }
        for name, placeholder in placeholders.items():
            action = Action(name)
            action.triggered.connect(lambda checked=False, p=placeholder: self._insert_placeholder(p))
            menu.addAction(action)
        menu.exec(QCursor.pos())

    def _insert_placeholder(self, placeholder):
        cursor = self._nameEdit.textCursor()
        cursor.insertText(placeholder)
        self._nameEdit.setTextCursor(cursor)
        self.on_value_changed(self.get_value())

    def get_value(self):
        return self._nameEdit.toPlainText()
    
    def set_value(self, value):
        if value:
            self._nameEdit.setPlainText(str(value))

class ActionButtonWidget(NodeBaseWidget):
    """内嵌按钮控件，点击时触发回调"""
    def __init__(self, parent, name, label, on_click):
        super().__init__(parent, name)
        btn = PushButton(label)
        btn.setFixedWidth(180)
        btn.clicked.connect(on_click)
        self.set_custom_widget(btn)

    def get_value(self):
        return None
    def set_value(self, v):
        pass


class SwitchButtonWidget(NodeBaseWidget):
    """内嵌开关控件"""
    def __init__(self, parent, name, label):
        super().__init__(parent, name)
        mainbox = QWidget()
        mainLayout = QHBoxLayout(mainbox)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(10)

        self._sw = SwitchButton()
        self._sw.setChecked(False)
        self._sw.setOnText('')
        self._sw.setOffText('')
        self.label_w = BodyLabel(label)

        mainLayout.addWidget(self.label_w, alignment=Qt.AlignVCenter | Qt.AlignLeft)
        mainLayout.addWidget(self._sw)
        mainLayout.addStretch(1)
        self.set_custom_widget(mainbox)

        self._sw.checkedChanged.connect(lambda v: self.on_value_changed(v))

    def get_value(self):
        return self._sw.isChecked()

    def set_value(self, v):
        self._sw.setChecked(bool(v))

