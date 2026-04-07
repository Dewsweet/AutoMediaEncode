# coding: utf-8
import time
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFileDialog, QApplication
from PySide6.QtCore import Qt

from qfluentwidgets import ScrollArea, TitleLabel, CaptionLabel, PushButton, PrimaryPushButton, qrouter
from qfluentwidgets import InfoBar, InfoBarPosition, FluentIcon as FIF

from ..components.recode_card_interface import InputFilesCard, FileInfoViewCard, VideoParamCard, AudioParamCard, ImageParamCard, SubtitleParamCard, OutputCard
# from ..components.fileload_interface import FileLoadInterface
from ..common.media_utils import classify_files, get_present_types, VIDEO_EXTS, AUDIO_EXTS, IMAGE_EXTS, SUBTITLE_EXTS
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
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

        self._initLayout()
        self._connect_signal()


    def _hearderArea(self):
        # 添加布局
        self.hearderBox = QWidget()
        self.hearderVLayout = QVBoxLayout(self.hearderBox)
        self.hearderVLayout.setContentsMargins(0, 0, 25, 10)
        self.hearderVLayout.setSpacing(0)

        self.hearderButtonBox = QWidget()
        self.hearderButtonLayout = QHBoxLayout(self.hearderButtonBox)
        self.hearderButtonLayout.setContentsMargins(0, 20, 0, 0)
        self.hearderButtonLayout.setSpacing(10)

        # 添加控件
        self.title_label = TitleLabel('媒体重编码', self)
        self.subtitle_label = CaptionLabel('调用 ffmpeg 对媒体文件进行简单的重编码', self)

        self.reLoad_button = PushButton('重载文件', self, FIF.ADD)
        self.start_recode_button = PrimaryPushButton('开始转码', self, FIF.PLAY)

    def _srollArea(self):
        # 添加布局
        self.scrollContainer = QWidget()
        self.scrollContainer.setObjectName("scrollContainer")
        self.scrollContainerVBoxLayout = QVBoxLayout(self.scrollContainer)
        self.scrollContainerVBoxLayout.setContentsMargins(0, 0, 25, 0)

        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollContainer)
        StyleSheet.RECODE_INTERFACE.apply(self)


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

    def _initLayout(self):
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

    def _connect_signal(self):
        # 展示预览信息
        self.inputFilesList.fileClicked.connect(self.display_view_info)

        self.videoParam.using_preset_switch.checkedChanged.connect(lambda state: self.update_videoParam_layout())

        self.reLoad_button.clicked.connect(self.open_file_dialog)

        self.imageParam.enable_image_base_process_switchButton.checkedChanged.connect(lambda state: self.emit_image_size())

        # 调试用：绑定组装测试打印到 开始转码 按钮
        self.start_recode_button.clicked.connect(self.emit_builder_output)


    def open_file_dialog(self):
        v_ext = "视频文件 (" + " ".join(f"*{ext}" for ext in VIDEO_EXTS) + ")"
        a_ext = "音频文件 (" + " ".join(f"*{ext}" for ext in AUDIO_EXTS) + ")"
        i_ext = "图片文件 (" + " ".join(f"*{ext}" for ext in IMAGE_EXTS) + ")"
        s_ext = "字幕文件 (" + " ".join(f"*{ext}" for ext in SUBTITLE_EXTS) + ")"
        all_ext = "所有文件 (*)"
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", f"{v_ext};;{a_ext};;{i_ext};;{s_ext};;{all_ext}")
        if files:
            self.process_loaded_files(files)
            self.fileInfoView.clear_info()

    def process_loaded_files(self, files):
        """对加载的文件进行分类, 更新UI显示, 并调整参数卡片的可见性"""
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

    def display_view_info(self, file_path):
        """根据传入的文件路径, 使用 MediaInfoService 获取文件基本信息, 并更新 fileInfoView 显示"""
        file_path = Path(file_path)
        QApplication.processEvents() # 强制刷新 UI 渲染文字
        mis = MediaInfoService()
        try: 
            if file_path.is_file(): 
                info_text = mis.view_info(file_path)
                self.fileInfoView.update_info(info_text)
            else:
                self.fileInfoView.update_info("该文件不是一个有效的文件!")
        except Exception as e:
            self.fileInfoView.update_info(f"读取文件信息失败: {str(e)}")

    def emit_image_size(self):
        """当启用图片基础处理时，获取当前载入的第一张图片的尺寸信息，并更新 imageParam 的原始尺寸状态"""
        files = self.inputFilesList.get_all_file_paths()
        if not files:
            print("未检测到文件，无法获取图片尺寸信息。")
            return
        mis = MediaInfoService()
        file = mis.image_size_info(files[0])
        width = file.get("width")
        height = file.get("height")
        if width and height:
            self.imageParam.set_original_size(width, height)
        
    def emit_builder_output(self):
        """Debug: 测试参数装配逻辑, 打印出根据当前UI状态和输入文件生成的命令行参数"""
        video_state = self.videoParam.get_state()
        audio_state = self.audioParam.get_state()
        image_state = self.imageParam.get_state()
        subtitle_state = self.subtitleParam.get_state()
        output_state = self.outputCard.get_state()
        
        # 获取当前列表中的文件
        files = self.inputFilesList.get_all_file_paths()
        
        # 空文件列表检查
        if not files:
            InfoBar.error(
                title='运行错误',
                content='文件列表为空, 请检查输入文件',
                orient=Qt.Horizontal,
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        
        # 文件存在性和有效性检查
        for f in files:
            if not Path(f).exists() or not Path(f).is_file():
                InfoBar.error(
                    title='运行错误',
                    content=f'文件不存在或已被删除:\n{f}',
                    orient=Qt.Horizontal,
                    isClosable=False,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
                return
        
        # 文件格式冲突检查
        for file in files:
            # 获取扩展名并去到"."，进行简单的格式冲突检查
            f = Path(file).suffix.strip(".").lower()

            if f in [video_state.get('container', '').lower(), audio_state.get('encoder_format', '').lower(), image_state.get('encoder_format', '').lower(), subtitle_state.get('encoder_format', '').lower()] and not output_state.get('custom_suffix'):
                InfoBar.warning(
                    title='注意',
                    content=f'输入文件容器与输出容器设置冲突: {f}\n请检查或者启用输出自定义后缀设置',
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=-1,
                    parent=self
                )
                return
        
        # 输出目录设置检查
        if not output_state.get('output_dir') and not output_state.get('use_source_dir'):
            InfoBar.error(
                title='运行错误',
                content='输出目录未设置, 请检查输出设置',
                orient=Qt.Horizontal,
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        
        # 通过基础检查后，组装任务负载并发出信号，通知后台开始处理
        task_id = f"task_{int(time.time()*1000)}"
        payload = {
            "task_id": task_id,
            "type": "Recondeing",
            "files": files,
            "states": {
                "video_state": video_state,
                "audio_state": audio_state,
                "image_state": image_state,
                "subtitle_state": subtitle_state,
                "output_state": output_state
            }
        }
        signalBus.taskAdded.emit(payload)
        

    def update_videoParam_layout(self):
        """根据当前窗口宽度和预设开关状态，动态调整 videoParam 和 audioParam 的布局方式"""
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



