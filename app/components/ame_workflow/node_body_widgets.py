import os
import subprocess
import shutil
import re

from PySide6.QtCore import Qt, Signal, QPoint, QPointF, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPainter, QPen, QBrush
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsDropShadowEffect, QStackedWidget, QLabel, QFileDialog, QTextEdit
from qfluentwidgets import (ToolButton, FluentIcon as FIF, BodyLabel, PushButton, LineEdit, ComboBox, SwitchButton, SpinBox, isDarkTheme, qconfig, MessageBoxBase)


class NodeBodyWidget(QWidget):
    param_changed = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._layout.setSpacing(2)
        self.setStyleSheet("background: transparent;")

    def get_params(self) -> dict:
        return {}

    def set_params(self, params: dict):
        pass


class WorkspaceBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout()
        row.setSpacing(4)
        self._btn = PushButton("浏览", self)
        self._edit = LineEdit(self)
        self._edit.setPlaceholderText("选择工作区...")
        self._btn.clicked.connect(lambda: self._pick_dir())
        self._edit.textChanged.connect(lambda t: self.param_changed.emit('work_dir', t))
        row.addWidget(self._btn)
        row.addWidget(self._edit, 1)
        self._layout.addLayout(row)

    def _pick_dir(self):
        p = QFileDialog.getExistingDirectory(self.window(), "选择工作区")
        if p:
            self._edit.setText(p)

    def get_params(self):
        return {'work_dir': self._edit.text()}

    def set_params(self, params: dict):
        self._edit.setText(str(params.get('work_dir', '')))


class InputFileBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout()
        row.setSpacing(4)
        self._btn = PushButton("浏览", self)
        self._edit = LineEdit(self)
        self._edit.setPlaceholderText("选择文件...")
        self._btn.clicked.connect(lambda: self._pick_file())
        self._edit.textChanged.connect(lambda t: self.param_changed.emit('file_path', t))
        row.addWidget(self._btn)
        row.addWidget(self._edit, 1)
        self._layout.addLayout(row)

    def _pick_file(self):
        exts = ("Media Files (*.mkv *.mp4 *.m2ts *.ts *.mts *.avi *.mov *.wmv *.flv *.webm"
                " *.h264 *.h265 *.ivf *.vc1 *.aac *.flac *.opus *.wav *.mp3 *.ac3 *.dts"
                " *.eac3 *.ogg *.ass *.srt *.vtt *.lrc *.xml *.txt *.cue *.ttf *.otf)"
                ";;All Files (*)")
        p, _ = QFileDialog.getOpenFileName(self.window(), "选择文件", "", exts)
        if p:
            self._edit.setText(p)

    def get_params(self):
        return {'file_path': self._edit.text()}

    def set_params(self, params: dict):
        self._edit.setText(str(params.get('file_path', '')))


class VPYBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout()
        row.setSpacing(4)
        self._btn = PushButton("浏览", self)
        self._edit = LineEdit(self)
        self._edit.setPlaceholderText("选择 .vpy 文件...")
        self._btn.clicked.connect(lambda: self._pick_file())
        self._edit.textChanged.connect(lambda t: self.param_changed.emit('vpy_path', t))
        row.addWidget(self._btn)
        row.addWidget(self._edit, 1)
        self._layout.addLayout(row)

    def _pick_file(self):
        p, _ = QFileDialog.getOpenFileName(self.window(), "选择脚本", "", "VPY (*.vpy);;All (*)")
        if p:
            self._edit.setText(p)

    def get_params(self):
        return {'vpy_path': self._edit.text()}

    def set_params(self, params: dict):
        self._edit.setText(str(params.get('vpy_path', '')))


class VSPipeBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout.addWidget(BodyLabel("VapourSynth Pipe", self))


class EncoderCLIBody(NodeBodyWidget):
    def __init__(self, encoder_type: str, parent=None):
        super().__init__(parent)
        self._enc = encoder_type
        preset_names = {"x264": "x264", "x265": "x265", "svtav1": "SVTAV1"}
        enc_key = preset_names.get(encoder_type, encoder_type)
        r1 = QHBoxLayout(); r1.setSpacing(4)
        r1.addWidget(BodyLabel("预设:", self))
        self._sw = SwitchButton(self)
        self._sw.setChecked(True); self._sw.setOnText(""); self._sw.setOffText("")
        r1.addWidget(self._sw)
        self._cb = ComboBox(self)
        self._cb.addItem("(无)")
        try:
            from app.services.setting.preset_service import preset_service
            for n in preset_service.get_presets_by_encoder(enc_key).keys():
                self._cb.addItem(n)
        except Exception: pass
        r1.addWidget(self._cb, 1)
        self._layout.addLayout(r1)
        self._cli = QTextEdit(self)
        self._cli.setPlaceholderText("自定义 CLI 参数 (每行一个参数或空格分隔均可)")
        self._cli.setMinimumHeight(60)
        self._cli.setMaximumHeight(120)
        self._cli.setStyleSheet("QTextEdit { border: 1px solid #555; border-radius: 4px; padding: 4px; }")
        self._layout.addWidget(self._cli)
        self._sw.checkedChanged.connect(lambda c: self._cb.setEnabled(c))
        self._cb.currentTextChanged.connect(lambda: self.param_changed.emit('preset', self._cb.currentText()))
        self._sw.checkedChanged.connect(lambda c: self.param_changed.emit('use_preset', c))
        self._cli.textChanged.connect(lambda: self.param_changed.emit('custom_cli', self._cli.toPlainText()))

    def get_params(self):
        return {'use_preset': self._sw.isChecked(),
                'preset': self._cb.currentText() if self._sw.isChecked() else '',
                'custom_cli': self._cli.toPlainText()}

    def set_params(self, params: dict):
        self._sw.setChecked(params.get('use_preset', True))
        self._cb.setEnabled(params.get('use_preset', True))
        if params.get('preset'): self._cb.setCurrentText(params['preset'])
        self._cli.setPlainText(str(params.get('custom_cli', '')))


class EncoderFFmpegVideoBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._codecs = [
            ("libx264","H.264"), ("libx265","H.265"), ("svt_av1","AV1(SVT)"),
            ("libvpx-vp9","VP9"), ("mpeg4","MPEG-4"),
            ("h264_nvenc","H.264 NV"), ("hevc_nvenc","H.265 NV"),
            ("h264_qsv","H.264 QSV"), ("hevc_qsv","H.265 QSV"),
            ("h264_amf","H.264 AMF"), ("hevc_amf","H.265 AMF"),
        ]
        self._keys = [k for k,_ in self._codecs]
        self._names = [n for _,n in self._codecs]

        r = QHBoxLayout(); r.setSpacing(4)
        r.addWidget(BodyLabel("编码器:", self))
        self._cb_codec = ComboBox(self); self._cb_codec.addItems(self._names); r.addWidget(self._cb_codec, 1)
        self._layout.addLayout(r)

        r2 = QHBoxLayout(); r2.setSpacing(4)
        r2.addWidget(BodyLabel("码率控制:", self))
        self._cb_rc = ComboBox(self); self._cb_rc.addItems(["CRF","ABR","CQP"]); r2.addWidget(self._cb_rc, 1)
        self._layout.addLayout(r2)

        r3 = QHBoxLayout(); r3.setSpacing(4)
        r3.addWidget(BodyLabel("CRF/QP:", self))
        self._q = SpinBox(self); self._q.setRange(0,63); self._q.setValue(23); r3.addWidget(self._q)
        r3.addWidget(BodyLabel("码率:", self))
        self._br = LineEdit(self); self._br.setPlaceholderText("5000k"); r3.addWidget(self._br)
        self._layout.addLayout(r3)

        r4 = QHBoxLayout(); r4.setSpacing(4)
        r4.addWidget(BodyLabel("速度:", self))
        self._preset = ComboBox(self)
        self._preset.addItems(["ultrafast","superfast","veryfast","faster","fast","medium","slow","slower","veryslow","placebo"])
        self._preset.setCurrentText("medium"); r4.addWidget(self._preset, 1)
        self._layout.addLayout(r4)

        r5 = QHBoxLayout(); r5.setSpacing(4)
        r5.addWidget(BodyLabel("扩展:", self))
        self._custom = LineEdit(self); self._custom.setPlaceholderText("自定义..."); r5.addWidget(self._custom, 1)
        self._layout.addLayout(r5)

    def get_params(self):
        ci = self._cb_codec.currentIndex()
        return {'codec': self._keys[ci] if 0 <= ci < len(self._keys) else 'libx264',
                'rc_mode': self._cb_rc.currentText().lower(),
                'quality_val': self._q.value(), 'bitrate': self._br.text(),
                'preset': self._preset.currentText(), 'custom_options': self._custom.text()}

    def set_params(self, params: dict):
        c = params.get('codec', 'libx264')
        if c in self._keys: self._cb_codec.setCurrentIndex(self._keys.index(c))
        rc = params.get('rc_mode', 'crf')
        self._cb_rc.setCurrentText(rc.upper() if rc else 'CRF')
        self._q.setValue(int(params.get('quality_val', 23)))
        self._br.setText(str(params.get('bitrate', '5000k')))
        self._preset.setCurrentText(str(params.get('preset', 'medium')))
        self._custom.setText(str(params.get('custom_options', '')))


class EncoderFFmpegAudioBody(NodeBodyWidget):
    def __init__(self, default_codec="aac", parent=None):
        super().__init__(parent)
        self._codecs = [("aac","AAC"),("libmp3lame","MP3"),("flac","FLAC"),("opus","Opus"),("libvorbis","Vorbis"),("ac3","AC-3")]
        self._keys = [k for k,_ in self._codecs]
        self._names = [n for _,n in self._codecs]
        r1 = QHBoxLayout(); r1.setSpacing(4)
        r1.addWidget(BodyLabel("编码器:", self))
        self._cb_c = ComboBox(self); self._cb_c.addItems(self._names); r1.addWidget(self._cb_c, 1)
        self._layout.addLayout(r1)
        r2 = QHBoxLayout(); r2.setSpacing(4)
        r2.addWidget(BodyLabel("控制:", self))
        self._cb_r = ComboBox(self); self._cb_r.addItems(["CBR","ABR","Quality"]); r2.addWidget(self._cb_r, 1)
        self._layout.addLayout(r2)
        r3 = QHBoxLayout(); r3.setSpacing(4)
        r3.addWidget(BodyLabel("码率:", self))
        self._br = LineEdit(self); self._br.setPlaceholderText("192k"); r3.addWidget(self._br)
        r3.addWidget(BodyLabel("质量:", self))
        self._q = SpinBox(self); self._q.setRange(0,12); self._q.setValue(5); r3.addWidget(self._q)
        self._layout.addLayout(r3)
        r4 = QHBoxLayout(); r4.setSpacing(4)
        r4.addWidget(BodyLabel("扩展:", self))
        self._custom = LineEdit(self); r4.addWidget(self._custom, 1)
        self._layout.addLayout(r4)

    def get_params(self):
        ci = self._cb_c.currentIndex()
        return {'codec': self._keys[ci] if 0 <= ci < len(self._keys) else 'aac',
                'rc_mode': self._cb_r.currentText().lower(),
                'bitrate': self._br.text(), 'quality_val': self._q.value(),
                'custom_options': self._custom.text()}

    def set_params(self, params: dict):
        c = params.get('codec', 'aac')
        if c in self._keys: self._cb_c.setCurrentIndex(self._keys.index(c))
        rc = params.get('rc_mode', 'cbr')
        self._cb_r.setCurrentText(rc.upper() if rc else 'CBR')
        self._br.setText(str(params.get('bitrate', '192k')))
        self._q.setValue(int(params.get('quality_val', 5)))
        self._custom.setText(str(params.get('custom_options', '')))


class FFmpegProcessorBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout.addWidget(BodyLabel("FFmpeg 参数:", self))
        self._cli = QTextEdit(self)
        self._cli.setPlaceholderText("-vf scale=1920:1080 ...")
        self._cli.setMinimumHeight(60)
        self._cli.setMaximumHeight(120)
        self._cli.setStyleSheet("QTextEdit { border: 1px solid #555; border-radius: 4px; padding: 4px; }")
        self._layout.addWidget(self._cli)
        self._cli.textChanged.connect(lambda: self.param_changed.emit('cli_args', self._cli.toPlainText()))

    def get_params(self):
        return {'cli_args': self._cli.toPlainText()}
    def set_params(self, params: dict):
        self._cli.setPlainText(str(params.get('cli_args', '')))


class MuxerMkvmergeBody(NodeBodyWidget):
    port_add_requested = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        r = QHBoxLayout(); r.setSpacing(4)
        for t, b in [("视频","+V"),("音频","+A"),("字幕","+S"),("附件","+F")]:
            btn = PushButton(b, self); btn.clicked.connect(lambda _, x=t: self.port_add_requested.emit(x)); r.addWidget(btn)
        r.addStretch()
        self._layout.addLayout(r)

    def get_params(self):
        return {'tracks': []}
    def set_params(self, params: dict):
        pass


class MuxerFFmpegBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        r = QHBoxLayout(); r.setSpacing(4)
        r.addWidget(BodyLabel("容器:", self))
        self._cb = ComboBox(self); self._cb.addItems(["MP4","MOV"]); r.addWidget(self._cb, 1)
        self._layout.addLayout(r)
        self._cb.currentTextChanged.connect(lambda t: self.param_changed.emit('container', t.lower()))

    def get_params(self):
        return {'container': self._cb.currentText().lower()}
    def set_params(self, params: dict):
        self._cb.setCurrentText(params.get('container','mp4').upper())


class OutputBody(NodeBodyWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(); row.setSpacing(4)
        self._btn = PushButton("浏览", self)
        self._edit = LineEdit(self); self._edit.setPlaceholderText("输出路径...")
        self._btn.clicked.connect(lambda: self._pick_file())
        self._edit.textChanged.connect(lambda t: self.param_changed.emit('output_path', t))
        row.addWidget(self._btn); row.addWidget(self._edit, 1)
        self._layout.addLayout(row)

    def _pick_file(self):
        p, _ = QFileDialog.getSaveFileName(self.window(), "选择输出", "", "MKV (*.mkv);;MP4 (*.mp4);;All (*)")
        if p: self._edit.setText(p)

    def get_params(self):
        return {'output_path': self._edit.text()}
    def set_params(self, params: dict):
        self._edit.setText(str(params.get('output_path', '')))
