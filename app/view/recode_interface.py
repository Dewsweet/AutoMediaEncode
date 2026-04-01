from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFileDialog, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor

from qfluentwidgets import ScrollArea, FlowLayout, TitleLabel, CaptionLabel, PushButton, PrimaryPushButton, qrouter
from qfluentwidgets import FluentIcon as FIF

from ..components.recode_card_interface import InputFilesCard, FileInfoViewCard, VideoParamCard, AudioParamCard, ImageParamCard, SubtitleParamCard, OutputCard
# from ..components.fileload_interface import FileLoadInterface
from ..common.media_utils import classify_files, get_present_types
from ..services.mediainfo_service import MediaInfoService

class RecodeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("RecodeInterface")

        self.mainPage = QWidget()
        self.mainLayout = QVBoxLayout(self.mainPage)
        self.mainLayout.setContentsMargins(20, 20, 0, 10)
        self.mainLayout.setSpacing(0)


        self._videoParam_is_horizontal = True

        self._hearderArea()
        self._srollArea()

        self._initWidget()
        self._conect_signal()


    def _hearderArea(self):
        # 添加布局
        self.hearderBox = QWidget()
        self.hearderVLayout = QVBoxLayout(self.hearderBox)
        self.hearderVLayout.setContentsMargins(0, 0, 20, 10)
        self.hearderVLayout.setSpacing(0)

        self.hearderButtonBox = QWidget()
        self.hearderButtonLayout = QHBoxLayout(self.hearderButtonBox)
        self.hearderButtonLayout.setContentsMargins(0, 0, 0, 0)
        self.hearderButtonLayout.setSpacing(10)

        # 添加控件
        self.title_label = TitleLabel('媒体重编码', self)
        self.subtitle_label = CaptionLabel('调用 ffmpeg 对媒体文件进行简单的重编码', self)

        self.reLoad_button = PushButton('重载文件', self, FIF.ADD)
        self.start_recode_button = PrimaryPushButton('开始转码', self, FIF.PLAY)

    def _srollArea(self):
        # 添加布局
        self.scrollContainer = QWidget()
        self.scrollContainer.setStyleSheet("background: transparent;")
        self.scrollContainerVBoxLayout = QVBoxLayout(self.scrollContainer)
        self.scrollContainerVBoxLayout.setContentsMargins(0, 0, 20, 0)

        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollContainer)
        self.scrollArea.setStyleSheet("QScrollArea { border: none; background: transparent; }")


        self.file_load_box = QWidget()
        self.file_load_hBoxLayout = QHBoxLayout(self.file_load_box)
        self.file_load_hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.encoderVAparamBox = QWidget()
        self.encoderVAparamVBoxLayout = QVBoxLayout(self.encoderVAparamBox)
        self.encoderVAparamVBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.encoderVAparamHBoxLayout = QHBoxLayout()
        self.encoderVAparamHBoxLayout.setContentsMargins(0, 0, 0, 0)


        self.inputFilesList = InputFilesCard(self)
        self.inputFilesList.setFixedHeight(300)
        self.fileInfoView = FileInfoViewCard(self)
        self.fileInfoView.setFixedHeight(300)

        self.videoParam = VideoParamCard(self)
        self.audioParam = AudioParamCard(self)
        self.imageParam = ImageParamCard(self)
        self.subtitleParam = SubtitleParamCard(self)

        self.outputCard = OutputCard(self)


    def _initWidget(self):
        # 头部标题和按钮布局
        self.hearderButtonLayout.addWidget(self.reLoad_button, alignment=Qt.AlignRight)
        self.hearderButtonLayout.addWidget(self.start_recode_button, alignment=Qt.AlignRight)

        self.hearderVLayout.addWidget(self.title_label)
        self.hearderVLayout.addWidget(self.subtitle_label)
        self.hearderVLayout.addWidget(self.hearderButtonBox, alignment=Qt.AlignRight)
        self.hearderVLayout.setAlignment(Qt.AlignTop)


        # 滚动区域内容布局
        # 文件加载区域
        self.file_load_hBoxLayout.addWidget(self.inputFilesList, 2)
        self.file_load_hBoxLayout.addWidget(self.fileInfoView, 1)

        # 编码参数区域
        self.encoderVAparamHBoxLayout.addWidget(self.videoParam, 5)
        self.encoderVAparamHBoxLayout.addWidget(self.audioParam, 4)

        self.encoderVAparamVBoxLayout.addLayout(self.encoderVAparamHBoxLayout)


        
        self.scrollContainerVBoxLayout.addWidget(self.file_load_box)
        self.scrollContainerVBoxLayout.addWidget(self.encoderVAparamBox)
        self.scrollContainerVBoxLayout.addWidget(self.imageParam)
        self.scrollContainerVBoxLayout.addWidget(self.subtitleParam)
        self.scrollContainerVBoxLayout.addWidget(self.outputCard)
        self.scrollContainerVBoxLayout.addStretch(1)

        # 总体布局
        self.mainLayout.addWidget(self.hearderBox)
        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)

    def _conect_signal(self):
        # 展示预览信息
        self.inputFilesList.fileClicked.connect(lambda file_path: self.fileInfoView.display_view_info(file_path))

        self.videoParam.using_preset_switch.checkedChanged.connect(lambda state: self.update_videoParam_layout())

        self.reLoad_button.clicked.connect(self.open_file_dialog)
        self.reLoad_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.reLoad_button.customContextMenuRequested.connect(self.inject_test_files)
        
        # 调试用：绑定组装测试打印到 开始转码 按钮
        self.start_recode_button.clicked.connect(self._test_builder_output)

    def _test_builder_output(self):
        from ..services.parameter_builder import MediaParameterBuilder
        from pathlib import Path
        
        # 收集用户当前UI状态
        video_state = self.videoParam.get_state()
        audio_state = self.audioParam.get_state()
        image_state = self.imageParam.get_state()
        subtitle_state = self.subtitleParam.get_state()
        output_state = self.outputCard.get_state()
        
        # 将状态喂入Builder组装参数
        builder = MediaParameterBuilder()
        v_args_list = builder.build_video_args(video_state)
        a_args = builder.build_audio_args(audio_state)
        # i_args 需要根据文件分辨率动态生成，移入循环
        s_args = builder.build_subtitle_args(subtitle_state)

        print("\n\n====== [参数装配测试] ======")
        
        files = self.inputFilesList.get_all_file_paths()
        if not files:
            print("未检测到文件，请先载入文件或右键重载测试文件。")
            return

        for f_path in files:
            file_path = Path(f_path)
            print(f"\n[处理文件]: {file_path.as_posix()}")
            
            # --- 1. 确定输出路径 ---
            # 使用 media_utils 中的 classify_files 进行分类判断
            classification = classify_files([file_path.as_posix()])
            is_video = bool(classification['video'])
            is_audio = bool(classification['audio'])
            is_image = bool(classification['image'])
            is_subtitle = bool(classification['subtitle'])
            
            # 获取分辨率 (仅图片需要)
            input_res = None
            if is_image:
                try:
                    raw_data = MediaInfoService.get_probe_data(file_path.as_posix())
                    tracks = raw_data.get("media", {}).get("track", [])
                    for t in tracks:
                        if t.get("@type") == "Image":
                            w = t.get("Width")
                            h = t.get("Height")
                            if w and h:
                                input_res = (int(w), int(h))

                                print(f"   >> [Probe] Detect Resolution: {w}x{h}")
                                break
                except Exception:
                    pass
            
            # 动态生成图片参数
            i_args = builder.build_image_args(image_state, input_resolution=input_res)

            # 确定输出后缀 (通过 builder.config 读取)
            out_ext = ""
            if is_video:
                out_ext = "." + video_state.get('container', 'mp4').lower() 
            elif is_audio:
                fmt = audio_state.get('encoder_format', 'AAC')
                container = builder.config.get("Audio", {}).get(fmt, {}).get("container", file_path.suffix.lstrip('.'))
                out_ext = f".{container}" if container else file_path.suffix
            elif is_image:
                fmt = image_state.get('encoder_format', 'JPEG')
                container = builder.config.get("Image", {}).get(fmt, {}).get("container", file_path.suffix.lstrip('.'))
                out_ext = f".{container}" if container else file_path.suffix
            elif is_subtitle:
                fmt = subtitle_state.get('encoder_format', 'SRT')
                container = builder.config.get("Subtitle", {}).get(fmt, {}).get("container", file_path.suffix.lstrip('.'))
                if not container: # 兜底简易映射
                    subtitle_ext_map = {'ASS': 'ass', 'SRT': 'srt', 'LRC': 'lrc', 'VTT': 'vtt'}
                    container = subtitle_ext_map.get(fmt, file_path.suffix.lstrip('.'))
                out_ext = f".{container}" if container else file_path.suffix
            else:
                out_ext = file_path.suffix
            
            # 确定输出目录
            out_dir = output_state['output_dir']
            if output_state['use_source_dir'] or not out_dir:
                out_dir_path = file_path.parent
            else:
                out_dir_path = Path(out_dir)
            
            # 确定文件名
            fname = file_path.stem
            if output_state.get('use_custom_suffix') and output_state.get('custom_suffix'):
                fname += output_state['custom_suffix']
                
            out_path = out_dir_path / (fname + out_ext)
            out_path_str = out_path.as_posix()
            in_path_str = file_path.as_posix()
            
            # --- 2. 组装命令 ---
            # 区分不同类型的参数组合
            if is_image:
                cmd = ["ffmpeg", "-y", "-i", f'"{in_path_str}"'] + i_args + [f'"{out_path_str}"']
                print(f">> CMD (Image): {' '.join(cmd)}")
                
            elif is_audio:
                cmd = ["ffmpeg", "-y", "-i", f'"{in_path_str}"'] + a_args + ["-vn"] + [f'"{out_path_str}"']
                print(f">> CMD (Audio): {' '.join(cmd)}")
                
            elif is_subtitle:
                print(f">> EXTENSION (Subtitle): Target Format {out_ext} (No FFmpeg command required)")
                
            elif is_video:
                # 视频可能涉及 2-pass 或 原生编码器
                for i, v_args in enumerate(v_args_list):
                    if isinstance(v_args, dict) and v_args.get("is_native"):
                        # 处理原生编码器 CLI
                        exe_name = v_args.get("encoder_exe", "encoder.exe")
                        cli_params = v_args.get("cli_params", "")
                        # 简单的将输入输出拼接到原生命令后面（可能需要根据具体编码器调整对应的输入输出参数名）
                        # 原生工具一般有各自的语法（例如 x264 --output out in 等），这里做简单的字符串示例组装
                        cmd_str = f'{exe_name} {cli_params} -i "{in_path_str}" -o "{out_path_str}"'
                        print(f">> CMD (Native Video Pass {i+1}): {cmd_str}")
                    else:
                        cmd = ["ffmpeg", "-y", "-i", f'"{in_path_str}"']
                        
                        # 视频参数
                        cmd.extend(v_args)
                        
                        # 音频参数及其他处理 (视频不包含字幕参数)
                        if len(v_args_list) > 1 and i == 0: 
                             # Pass 1: 输出为 NUL，手动添加 -an 以防 config 里没有
                             if "-an" not in cmd:
                                 cmd.append("-an")
                        else:
                             # Pass 2 or Single Pass: 加音频
                             cmd.extend(a_args)
                        
                        # 输出路径
                        if len(v_args_list) > 1 and i == 0:
                            cmd.append("NUL") # Windows 2-pass null output
                        else:
                            cmd.append(f'"{out_path_str}"')
                            
                        print(f">> CMD (Video Pass {i+1}): {' '.join(cmd)}")

        print("============================\n\n")

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "所有文件 (*)")
        if files:
            self.process_loaded_files(files)

    def inject_test_files(self, pos):
        # 模拟一份文件列表拿来测试（右键点击“重载文件”触发）
        test_files = [
            "C:/movies/test_video_1.mp4",
            "C:/movies/test_video_2.mkv",
            "D:/music/song_1.mp3",
            "D:/images/pic_1.jpg",
            "D:/subs/subtitle.srt"
        ]
        self.process_loaded_files(test_files)

    def process_loaded_files(self, files):
        classified_dict = classify_files(files)
        present_types = get_present_types(classified_dict)
        
        if not present_types:
            return

        # 1. 更新树形列表
        self.inputFilesList.update_files(classified_dict, present_types)
        
        # 2. 动态调整下方卡片显示状态
        self.videoParam.setVisible('video' in present_types)
        # 只要有音频或者有视频，都显示音频参数卡片
        self.audioParam.setVisible('audio' in present_types or 'video' in present_types)
        self.imageParam.setVisible('image' in present_types)
        self.subtitleParam.setVisible('subtitle' in present_types)
        
        self.update_videoParam_layout()

    def update_videoParam_layout(self):
        # 获取当前窗口的宽度
        window_width = self.width()
        threshold = 850

        needs_vertical = (window_width < threshold) or (not self.videoParam.using_preset_switch.isChecked())

        if needs_vertical and self._videoParam_is_horizontal:
            # 切换到垂直布局
            self.encoderVAparamHBoxLayout.removeWidget(self.videoParam)
            self.encoderVAparamHBoxLayout.removeWidget(self.audioParam)

            self.encoderVAparamVBoxLayout.addWidget(self.videoParam)
            self.encoderVAparamVBoxLayout.addWidget(self.audioParam)
            self._videoParam_is_horizontal = False
        elif not needs_vertical and not self._videoParam_is_horizontal:
            # 切换回水平布局
            self.encoderVAparamVBoxLayout.removeWidget(self.videoParam)
            self.encoderVAparamVBoxLayout.removeWidget(self.audioParam)

            self.encoderVAparamHBoxLayout.addWidget(self.videoParam, 5)
            self.encoderVAparamHBoxLayout.addWidget(self.audioParam, 4)
            self._videoParam_is_horizontal = True

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.update_videoParam_layout()



