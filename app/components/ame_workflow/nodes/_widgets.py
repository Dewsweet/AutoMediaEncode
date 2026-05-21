from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QComboBox, QStyleFactory, QFrame
from qfluentwidgets import PushButton, PrimaryPushButton, LineEdit, ComboBox, SwitchButton, BodyLabel, TextEdit, RoundMenu, Action, Slider, TransparentToolButton, FluentIcon as FIF
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

    def addItem(self, text, user_data=None): # 这里的 user_data 暂不使用，但保留接口以便未来扩展
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


class PathBrowseWidget(NodeBaseWidget):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.name = name
        row = QWidget()
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self._btn = PushButton(self.name, row)
        self._btn.setFixedHeight(32)
        self._btn.clicked.connect(self._browse)

        self._edit = LineEdit(row)
        self._edit.setFixedHeight(32)
        self._edit.setPlaceholderText('选择路径...')
        self._edit.textChanged.connect(lambda t: self.on_value_changed(t))
        layout.addWidget(self._btn)
        layout.addWidget(self._edit, 1)
        self.set_custom_widget(row)

    def _browse(self):
        pass

    def get_value(self):
        return self._edit.text()

    def set_value(self, value):
        if value:
            self._edit.setText(str(value))

class DirBrowseWidget(PathBrowseWidget):
    def __init__(self, parent, name):
        super().__init__(parent, name)

    def _browse(self):
        p = QFileDialog.getExistingDirectory(None, '选择目录')
        if p:
            self._edit.setText(p)

class FileBrowseWidget(PathBrowseWidget):
    def __init__(self, parent, name, exts=''):
        self._ext_filter = exts
        super().__init__(parent, name)

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(None, '选择文件', '', self._ext_filter or 'All Files (*)')
        if p:
            self._edit.setText(p)

class SaveBrowseWidget(PathBrowseWidget):
    def __init__(self, parent, name, exts=''):
        self._ext_filter = exts
        super().__init__(parent, name)

    def _browse(self):
        p, _ = QFileDialog.getSaveFileName(None, '保存路径', '', self._ext_filter or 'All Files (*)')
        if p:
            self._edit.setText(p)


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
        self._edit.setPlaceholderText('自定义 CLI 参数...')
        self._edit.setMinimumHeight(48)
        self._edit.setMaximumHeight(100)
        self._edit.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self.set_custom_widget(self._edit)

    def get_value(self):
        return self._edit.toPlainText()

    def set_value(self, value):
        if value:
            self._edit.setPlainText(str(value))

class mkvmergeWidget(NodeBaseWidget):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self.mainbox = QWidget()
        self.mainLayout = QVBoxLayout(self.mainbox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(10)

        self.moreSettingsBox = QFrame()
        self.moreSettingsVLayout = QVBoxLayout(self.moreSettingsBox)
        self.expanHLayout = QHBoxLayout()

        self.defaultTrackHLayout = QHBoxLayout()
        self.trackLanguageHLayout = QHBoxLayout()
        self.trackNameHLayout = QHBoxLayout()

        self._expandLabel = BodyLabel('More', self.mainbox)
        self._expandBtn = TransparentToolButton(FIF.RIGHT_ARROW, self.mainbox)
        
        self._defaultTrackLabel = BodyLabel('默认轨道:', self.mainbox)
        self._defaultTrackSwitch = SwitchButton(self.mainbox)
        self._defaultTrackSwitch.setOnText('启用')
        self._defaultTrackSwitch.setOffText('禁用')

        self._trackLanguageLabel = BodyLabel('轨道语言:', self.mainbox)
        self._trackLanguageEdit = LineEdit(self.mainbox)

        self._trackNameLabel = BodyLabel('轨道名称:', self.mainbox)
        self._trackNameEdit = LineEdit(self.mainbox)

        self._newTrackBtn = PushButton('添加新轨道', self.mainbox)

        self.expanHLayout.addWidget(self._expandLabel)
        self.expanHLayout.addStretch(1)
        self.expanHLayout.addWidget(self._expandBtn)

        self.defaultTrackHLayout.addWidget(self._defaultTrackLabel)
        self.defaultTrackHLayout.addWidget(self._defaultTrackSwitch)

        self.trackLanguageHLayout.addWidget(self._trackLanguageLabel)
        self.trackLanguageHLayout.addWidget(self._trackLanguageEdit)

        self.trackNameHLayout.addWidget(self._trackNameLabel)
        self.trackNameHLayout.addWidget(self._trackNameEdit)

        self.moreSettingsVLayout.addLayout(self.defaultTrackHLayout)
        self.moreSettingsVLayout.addLayout(self.trackLanguageHLayout)
        self.moreSettingsVLayout.addLayout(self.trackNameHLayout)
        self.moreSettingsVLayout.addWidget(self._newTrackBtn)
        self.moreSettingsBox.setVisible(False)

        self.mainLayout.addLayout(self.expanHLayout)
        self.mainLayout.addWidget(self.moreSettingsBox)
        self.mainLayout.addStretch(1)
        self.set_custom_widget(self.mainbox)

        self._connect_signals()
    
    def _connect_signals(self):
        self._defaultTrackSwitch.checkedChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._trackLanguageEdit.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._trackNameEdit.textChanged.connect(lambda: self.on_value_changed(self.get_value()))
        self._expandBtn.clicked.connect(lambda: self.moreSettingsBox.setVisible(not self.moreSettingsBox.isVisible()))


    def get_value(self):
        return {
            'default_track': self._defaultTrackSwitch.isChecked(),
            'track_language': self._trackLanguageEdit.text(),
            'track_name': self._trackNameEdit.text()
        }
    def set_value(self, value):
        if isinstance(value, dict):
            self._defaultTrackSwitch.setChecked(value.get('default_track', False))
            self._trackLanguageEdit.setText(value.get('track_language', ''))
            self._trackNameEdit.setText(value.get('track_name', ''))
