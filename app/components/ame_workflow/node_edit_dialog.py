from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QSlider, QLineEdit, QCheckBox,
                                QFileDialog, QSpinBox)

from qfluentwidgets import (BodyLabel, LineEdit, ComboBox, Slider, PushButton,
                            PrimaryPushButton, CheckBox, MessageBoxBase,
                            SpinBox, ProgressRing)

from . import CATEGORY_COLORS


class AMENodeEditDialog(MessageBoxBase):
    params_changed = Signal(str, object)

    def __init__(self, node_item, parent=None):
        self._node_item = node_item
        self._node_data = node_item.get_state()
        node_type = self._node_data.get('type', '')
        node_name = self._node_data.get('name', node_type)
        self._node_id = self._node_data.get('id', '')
        self._param_widgets = {}

        super().__init__(parent)
        self.viewLayout.setContentsMargins(20, 20, 20, 20)

        self.titleLabel = BodyLabel(f"编辑节点: {node_name}", self)
        self.titleLabel.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(16)

        self._build_params_ui()
        self.viewLayout.addSpacing(12)

        self.yesButton.setText("确定")
        self.yesButton.clicked.connect(self._on_save)
        self.cancelButton.setText("取消")

    def _build_params_ui(self):
        node_type = self._node_data.get('type', '')
        params = self._node_data.get('params', {})

        if node_type == 'workspace':
            self._build_workspace_params(params)
        elif node_type == 'input_file':
            self._build_input_file_params(params)
        elif node_type == 'splitter':
            self._build_splitter_params(params)
        elif node_type in ('encoder_x264', 'encoder_x265', 'encoder_svtav1'):
            self._build_cli_encoder_params(params, node_type)
        elif node_type == 'encoder_ffmpeg_video':
            self._build_ffmpeg_video_params(params)
        elif node_type == 'encoder_ffmpeg_audio':
            self._build_ffmpeg_audio_params(params)
        elif node_type == 'muxer_mkvmerge':
            self._build_muxer_mkvmerge_params(params)
        elif node_type == 'muxer_ffmpeg':
            self._build_muxer_ffmpeg_params(params)
        elif node_type == 'output':
            self._build_output_params(params)

    def _add_row(self, label_text, widget):
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 4, 0, 4)
        label = BodyLabel(label_text, self)
        label.setFixedWidth(100)
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        self.viewLayout.addWidget(row)
        return widget

    def _build_workspace_params(self, params):
        w = LineEdit(self)
        w.setText(params.get('work_dir', ''))
        w.setPlaceholderText("选择工作区目录...")
        browse_btn = PushButton("浏览", self)
        browse_btn.clicked.connect(lambda: self._browse_dir(w))
        self._add_row("工作目录", w)
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(100, 4, 0, 4)
        layout.addWidget(browse_btn)
        layout.addStretch()
        self.viewLayout.addWidget(row)
        self._param_widgets['work_dir'] = w

    def _build_input_file_params(self, params):
        w = LineEdit(self)
        w.setText(params.get('file_path', ''))
        w.setPlaceholderText("选择媒体文件...")
        browse_btn = PushButton("浏览", self)
        browse_btn.clicked.connect(lambda: self._browse_file(w, "选择媒体文件"))
        self._add_row("文件路径", w)
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(100, 4, 0, 4)
        layout.addWidget(browse_btn)
        layout.addStretch()
        self.viewLayout.addWidget(row)

        file_types = ["auto", "video", "audio", "subtitle", "chapter", "attachment"]
        file_type_names = ["自动检测", "完整容器", "裸视频流", "裸音频流", "独立字幕", "独立章节", "附件"]
        cb = ComboBox(self)
        for name, val in zip(file_type_names, file_types):
            cb.addItem(name)
        cb.setCurrentText(file_type_names[file_types.index(params.get('file_type', 'auto'))] if params.get('file_type', 'auto') in file_types else file_type_names[0])
        self._add_row("文件类型", cb)
        self._param_widgets['file_path'] = w
        self._param_widgets['file_type'] = cb

    def _build_splitter_params(self, params):
        tool_cb = ComboBox(self)
        tool_cb.addItems(["ffmpeg", "mkvextract"])
        tool_cb.setCurrentText(params.get('tool', 'ffmpeg'))
        self._add_row("工具", tool_cb)

        mode_cb = ComboBox(self)
        mode_cb.addItems(["extract", "refer"])
        mode_names = {"extract": "物理提取（分离为实际文件）", "refer": "映射引用（传递轨道索引，不产生新文件）"}
        mode_cb.setCurrentText(params.get('mode', 'extract'))
        self._add_row("模式", mode_cb)
        self._param_widgets['tool'] = tool_cb
        self._param_widgets['mode'] = mode_cb

    def _build_cli_encoder_params(self, params, node_type):
        from app.services.setting.preset_service import preset_service
        presets = {}
        if node_type == 'encoder_x264':
            presets = preset_service.get_presets_by_encoder('x264')
        elif node_type == 'encoder_x265':
            presets = preset_service.get_presets_by_encoder('x265')
        elif node_type == 'encoder_svtav1':
            presets = preset_service.get_presets_by_encoder('SVTAV1')

        preset_cb = ComboBox(self)
        preset_cb.addItem("(无预设)")
        preset_names = list(presets.keys()) if presets else []
        for pname in preset_names:
            preset_cb.addItem(pname)
        current_preset = params.get('preset', '')
        if current_preset in preset_names:
            preset_cb.setCurrentText(current_preset)
        self._add_row("预设", preset_cb)

        cli_edit = LineEdit(self)
        cli_edit.setText(params.get('custom_cli', ''))
        cli_edit.setPlaceholderText("自定义 CLI 参数，如 --crf 18 --preset slower")
        self._add_row("自定义参数", cli_edit)

        self._param_widgets['preset'] = preset_cb
        self._param_widgets['custom_cli'] = cli_edit

    def _build_ffmpeg_video_params(self, params):
        codec_cb = ComboBox(self)
        codec_cb.addItems([
            "libx264", "libx265", "svt_av1", "libvpx-vp9", "mpeg4",
            "h264_nvenc", "hevc_nvenc", "h264_qsv", "hevc_qsv", "h264_amf", "hevc_amf"
        ])
        codec_cb.setCurrentText(params.get('codec', 'libx264'))
        self._add_row("编码器", codec_cb)

        rc_cb = ComboBox(self)
        rc_cb.addItems(["crf", "abr", "cqp"])
        rc_names = {"crf": "CRF（恒定质量）", "abr": "ABR（平均码率）", "cqp": "CQP（恒定QP）"}
        rc_cb.setCurrentText(params.get('rc_mode', 'crf'))
        self._add_row("码率控制", rc_cb)

        quality_spin = SpinBox(self)
        quality_spin.setRange(0, 63)
        quality_spin.setValue(params.get('quality_val', 23))
        self._add_row("CRF/QP 值", quality_spin)

        bitrate_edit = LineEdit(self)
        bitrate_edit.setText(params.get('bitrate', '5000k'))
        bitrate_edit.setPlaceholderText("如 5000k, 8M")
        self._add_row("码率", bitrate_edit)

        preset_cb = ComboBox(self)
        preset_cb.addItems(["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"])
        preset_cb.setCurrentText(params.get('preset', 'medium'))
        self._add_row("预设速度", preset_cb)

        profile_edit = LineEdit(self)
        profile_edit.setText(params.get('profile', ''))
        profile_edit.setPlaceholderText("如 high, main10")
        self._add_row("Profile", profile_edit)

        tune_edit = LineEdit(self)
        tune_edit.setText(params.get('tune', ''))
        tune_edit.setPlaceholderText("如 film, animation, grain")
        self._add_row("Tune", tune_edit)

        custom_edit = LineEdit(self)
        custom_edit.setText(params.get('custom_options', ''))
        custom_edit.setPlaceholderText("自定义 FFmpeg 参数")
        self._add_row("扩展参数", custom_edit)

        self._param_widgets = {
            'codec': codec_cb, 'rc_mode': rc_cb, 'quality_val': quality_spin,
            'bitrate': bitrate_edit, 'preset': preset_cb, 'profile': profile_edit,
            'tune': tune_edit, 'custom_options': custom_edit,
        }

    def _build_ffmpeg_audio_params(self, params):
        codec_cb = ComboBox(self)
        codec_cb.addItems(["aac", "libmp3lame", "flac", "opus", "libvorbis", "ac3"])
        codec_names = {"aac": "AAC", "libmp3lame": "MP3", "flac": "FLAC", "opus": "Opus", "libvorbis": "Vorbis", "ac3": "AC-3"}
        codec_cb.setCurrentText(params.get('codec', 'aac'))
        self._add_row("编码器", codec_cb)

        rc_cb = ComboBox(self)
        rc_cb.addItems(["cbr", "abr", "quality"])
        rc_names = {"cbr": "CBR（恒定码率）", "abr": "ABR（平均码率）", "quality": "Quality（质量）"}
        rc_cb.setCurrentText(params.get('rc_mode', 'cbr'))
        self._add_row("码率控制", rc_cb)

        bitrate_edit = LineEdit(self)
        bitrate_edit.setText(params.get('bitrate', '192k'))
        bitrate_edit.setPlaceholderText("如 192k, 320k")
        self._add_row("码率", bitrate_edit)

        quality_spin = SpinBox(self)
        quality_spin.setRange(0, 12)
        quality_spin.setValue(params.get('quality_val', 5))
        self._add_row("质量等级", quality_spin)

        custom_edit = LineEdit(self)
        custom_edit.setText(params.get('custom_options', ''))
        custom_edit.setPlaceholderText("自定义 FFmpeg 参数")
        self._add_row("扩展参数", custom_edit)

        self._param_widgets = {
            'codec': codec_cb, 'rc_mode': rc_cb, 'bitrate': bitrate_edit,
            'quality_val': quality_spin, 'custom_options': custom_edit,
        }

    def _build_muxer_mkvmerge_params(self, params):
        info = BodyLabel("轨道属性请在封装执行前于执行弹窗中设置", self)
        info.setStyleSheet("color: #888;")
        self.viewLayout.addWidget(info)

    def _build_muxer_ffmpeg_params(self, params):
        cb = ComboBox(self)
        cb.addItems(["mp4", "mov"])
        cb.setCurrentText(params.get('container', 'mp4'))
        self._add_row("容器格式", cb)

        fs_cb = CheckBox("启用 faststart（流式播放优化，仅 MP4）", self)
        fs_cb.setChecked(params.get('faststart', False))
        self._add_row("", fs_cb)

        self._param_widgets = {'container': cb, 'faststart': fs_cb}

    def _build_output_params(self, params):
        w = LineEdit(self)
        w.setText(params.get('output_path', ''))
        w.setPlaceholderText("选择输出路径...")
        browse_btn = PushButton("浏览", self)
        browse_btn.clicked.connect(lambda: self._browse_save_file(w))
        self._add_row("输出路径", w)
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(100, 4, 0, 4)
        layout.addWidget(browse_btn)
        layout.addStretch()
        self.viewLayout.addWidget(row)

        template_edit = LineEdit(self)
        template_edit.setText(params.get('filename_template', '{input_name}_encoded'))
        template_edit.setPlaceholderText("{input_name}_encoded")
        self._add_row("文件名模板", template_edit)

        self._param_widgets = {'output_path': w, 'filename_template': template_edit}

    def _browse_dir(self, line_edit):
        from PySide6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "选择工作区目录")
        if path:
            line_edit.setText(path)

    def _browse_file(self, line_edit, title):
        from PySide6.QtWidgets import QFileDialog
        exts = "Media Files (*.mkv *.mp4 *.m2ts *.ts *.mts *.avi *.mov *.wmv *.flv *.webm *.h264 *.h265 *.ivf *.aac *.flac *.opus *.wav *.mp3 *.ac3 *.dts *.ass *.srt *.vtt *.lrc *.xml *.txt *.cue *.ttf *.otf *.png *.jpg);;All Files (*)"
        path, _ = QFileDialog.getOpenFileName(self, title, "", exts)
        if path:
            line_edit.setText(path)

    def _browse_save_file(self, line_edit):
        from PySide6.QtWidgets import QFileDialog
        exts = "Matroska (*.mkv);;MP4 (*.mp4);;All Files (*)"
        path, _ = QFileDialog.getSaveFileName(self, "选择输出路径", "", exts)
        if path:
            line_edit.setText(path)

    def _on_save(self):
        if self._node_item:
            params = self._node_item.params()
            for key, widget in self._param_widgets.items():
                if hasattr(widget, 'currentText'):
                    params[key] = widget.currentText()
                elif hasattr(widget, 'isChecked'):
                    params[key] = widget.isChecked()
                elif hasattr(widget, 'text'):
                    params[key] = widget.text()
                elif hasattr(widget, 'value'):
                    params[key] = widget.value()
            self._node_item.set_param('params', params)
            self.params_changed.emit(self._node_id, params)
        self.accept()
