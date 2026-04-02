# coding: utf-8
from pathlib import Path
import json
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QButtonGroup, QGroupBox, QFileDialog, QTreeWidgetItem, QTreeWidgetItemIterator

from qfluentwidgets import (HeaderCardWidget, CardWidget, FlowLayout, TableWidget, ListWidget, TreeWidget, 
                            TextEdit, BodyLabel, ComboBox, SwitchButton, RadioButton, PushButton, Slider, StrongBodyLabel, SpinBox, DoubleSpinBox, PrimaryPushButton, CheckBox, EditableComboBox, LineEdit, RoundMenu, Action)

from ..services.hw_detect_service import hw_detect_service
from ..services.mediainfo_service import MediaInfoService
from ..services.path_service import PathService
from ..common.style_sheet import StyleSheet

class Frame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.setObjectName("frame")
        StyleSheet.RECODE_CARD_INTERFACE.apply(self)

    def addWidget(self, widget):
        self.vBoxLayout.addWidget(widget)

    def addLayout(self, layout):
        self.vBoxLayout.addLayout(layout)

class InputFilesCard(HeaderCardWidget):
    fileClicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('载入文件')

        self.frame = Frame(self)
        self.input_files_fist = TreeWidget()
        self.input_files_fist.setHeaderHidden(True)
        # 允许右键菜单
        self.input_files_fist.setContextMenuPolicy(Qt.CustomContextMenu)

        self.frame.addWidget(self.input_files_fist)
        self.viewLayout.addWidget(self.frame)
        self.viewLayout.setContentsMargins(10, 10, 10, 10)

        self._connect_signals()

    def update_files(self, classified_dict, present_types):
        """传入分类后的字典及其包含的有效分类列表，重绘树形列表"""
        self.input_files_fist.blockSignals(True) # 更新时阻止信号触发，避免不必要的处理
        self.input_files_fist.clear()

        type_names = {
            'video': '视频',
            'audio': '音频',
            'image': '图片',
            'subtitle': '字幕'
        }

        # 如果只有一种类型，不显示父节点，直接平铺
        if len(present_types) == 1:
            file_type = present_types[0]
            for file_path in classified_dict[file_type]:
                filename = Path(file_path).stem
                item = QTreeWidgetItem([filename])
                item.setData(0, Qt.UserRole, file_path) # 存储完整路径留作后用
                item.setCheckState(0, Qt.Checked)
                self.input_files_fist.addTopLevelItem(item)
        else:
            # 多种类型，显示父节点
            for t_key in ['video', 'audio', 'image', 'subtitle']:
                if t_key in present_types:
                    parent_item = QTreeWidgetItem([type_names[t_key]])
                    parent_item.setCheckState(0, Qt.Checked)
                    
                    for file_path in classified_dict[t_key]:
                        filename = Path(file_path).stem
                        child_item = QTreeWidgetItem([filename])
                        child_item.setData(0, Qt.UserRole, file_path)
                        child_item.setCheckState(0, Qt.Checked)
                        parent_item.addChild(child_item)
                        
                    self.input_files_fist.addTopLevelItem(parent_item)
                    
            self.input_files_fist.expandAll()

        self.input_files_fist.blockSignals(False)

    def _connect_signals(self):
        self.input_files_fist.itemChanged.connect(self.handle_item_changed)
        self.input_files_fist.customContextMenuRequested.connect(self.show_context_menu)
        self.input_files_fist.itemClicked.connect(self.on_item_clicked)

    def on_item_clicked(self, item, column):
        file_path = item.data(0, Qt.UserRole) 
        if file_path:
            self.fileClicked.emit(file_path)

    def get_all_file_paths(self):
        """遍历并返回树中所有有效并被选中的文件路径（叶子节点）"""
        paths = []
        iterator = QTreeWidgetItemIterator(self.input_files_fist) 
        while iterator.value(): 
            item = iterator.value()
            # 只获取勾选的项目
            if item.checkState(0) == Qt.Checked:
                file_path = item.data(0, Qt.UserRole)
                # data(0, Qt.UserRole) 存储的是完整路径，如果为空通常是父分类节点
                if file_path:
                    paths.append(file_path)
            iterator += 1 
        return paths

    def show_context_menu(self, pos):
        """右键菜单"""
        menu = RoundMenu(parent=self)
        
        select_all_action = Action('全选', triggered=self.select_all_items)
        deselect_all_action = Action('全不选', triggered=self.deselect_all_items)
        
        menu.addAction(select_all_action)
        menu.addAction(deselect_all_action)
        
        menu.exec(self.input_files_fist.mapToGlobal(pos))

    def select_all_items(self):
        self.input_files_fist.blockSignals(True)
        it = QTreeWidgetItemIterator(self.input_files_fist)
        while it.value():
            it.value().setCheckState(0, Qt.Checked)
            it += 1
        self.input_files_fist.blockSignals(False)

    def deselect_all_items(self):
        self.input_files_fist.blockSignals(True)
        it = QTreeWidgetItemIterator(self.input_files_fist)
        while it.value():
            it.value().setCheckState(0, Qt.Unchecked)
            it += 1
        self.input_files_fist.blockSignals(False)

    def handle_item_changed(self, item, column):
        if item.childCount() > 0: 
            state = item.checkState(column)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(column, state)  # 子节点跟随父节点状态
    
class FileInfoViewCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('信息预览')

        self.info_view = TextEdit()
        self.info_view.setReadOnly(True)
        self.info_view.setText("点击文件读取信息...")

        self.viewLayout.addWidget(self.info_view)
        self.viewLayout.setContentsMargins(10, 10, 10, 10)

    def update_info(self, info_text):
        self.info_view.setMarkdown(info_text)

    def clear_info(self):
        self.info_view.setText("点击文件读取信息...")

class VideoParamCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('视频编码设置')

        preset_path = PathService.get_config_dir() / 'custom_preset.json'
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                self.custom_preset_config = json.load(f) # 
        except Exception:
            self.custom_preset_config = {}

        self.mainLayout = QVBoxLayout()

        self.area_ecoder_select()
        self.area_using_presets()
        self.area_custom_encoder_settings()

        self._initLayout() 
        self._connect_signals()

    def area_ecoder_select(self):
        self.encoder_format_box = QWidget()
        self.encoder_format_hBoxLayout = QHBoxLayout(self.encoder_format_box)

        self.container_select_label = BodyLabel("封装格式:")
        self.container_select_combobox = ComboBox()
        self.container_select_combobox.setFixedWidth(90)
        self.container_select_combobox.addItems(["MKV", "MP4", "MOV", "AVI", "WebM", "FLV", "WMV"])

        all_encoders = ["Copy", "FFV1", "AVC (x264)", "AVC (NVEnc)", "AVC (QSV)", "AVC (AMF)", "HEVC (x265)", "HEVC (NVEnc)", "HEVC (QSV)", "HEVC (AMF)", "AV1 (SVT)", "VP9", "MPEG-4"]
        encoder_items = hw_detect_service.get_supported_video_encoders(all_encoders)

        self.encoder_format_label = BodyLabel("编码格式:")
        self.encoder_forma_combobox = ComboBox()
        self.encoder_forma_combobox.addItems(encoder_items)

    def area_using_presets(self):
        self.using_preset_box = QWidget()
        self.using_preset_hBoxLayout = QHBoxLayout(self.using_preset_box)
        self.using_preset_box.setEnabled(False)

        self.using_preset_switch_label = BodyLabel("使用预设:")

        self.using_preset_switch = SwitchButton()
        self.using_preset_switch.setChecked(True) 
        self.using_preset_switch.setOnText("")
        self.using_preset_switch.setOffText("")

        self.using_preset_label = BodyLabel("预设:")

        self.using_preset_cBox = ComboBox()

    def area_custom_encoder_settings(self):
        # 主要布局(共 4 个Box, 两个主要区域)
        self.custom_encoder_settings_mainBox = QGroupBox("自定义编码设置")
        self.custom_encoder_settings_mianLayout = QVBoxLayout(self.custom_encoder_settings_mainBox)

        self.custom_encoder_settings_box = QWidget()
        self.custom_encoder_settings_hBoxLayout = QHBoxLayout(self.custom_encoder_settings_box)


        self.encoder_bitrate_control_box = QWidget()
        self.encoder_bitrate_control_box_vBoxLayout = QVBoxLayout(self.encoder_bitrate_control_box)

        self.encoder_bitrate_control_box_hBox1Layout = QHBoxLayout()
        self.encoder_bitrate_control_box_2Box2Layout = QHBoxLayout()

        self.encoder_base_option_box = QWidget()
        self.encoder_base_option_box_vBoxLayout = QVBoxLayout(self.encoder_base_option_box)

        self.encoder_base_option_box_hBox1Layout = QHBoxLayout()
        self.encoder_base_option_box_hBox2Layout = QHBoxLayout()
        self.encoder_base_option_box_hBox3Layout = QHBoxLayout()

        
        # Bitrate Control 
        self.bitrate_control_label = StrongBodyLabel("码率控制:")

        self.crf_rb = RadioButton("恒定质量 (CRF):")
        self.crf_rb.setChecked(True) 
        self.crf_value_spinBox = DoubleSpinBox()
        self.crf_value_spinBox.setDecimals(1)
        self.crf_value_spinBox.setFixedWidth(140)
        self.crf_value_spinBox.setRange(0, 51)
        self.crf_value_spinBox.setSingleStep(1.0)
        self.crf_value_spinBox.setValue(20.0)

        self.abr_rb = RadioButton("平均码率 (ABR):")
        self.abr_value_pinBox = SpinBox()
        self.abr_value_pinBox.setFixedWidth(140)
        self.abr_value_pinBox.setRange(0, 100000)
        self.abr_value_pinBox.setSingleStep(100)
        self.abr_value_unit_label = BodyLabel("kbps")

        self.bitrate_control_button_group = QButtonGroup()
        self.bitrate_control_button_group.addButton(self.crf_rb)  
        self.bitrate_control_button_group.addButton(self.abr_rb)

        self.bitrate_control_2pass_checkBox = CheckBox("2pass")
        self.bitrate_control_2pass_checkBox.setEnabled(False)

        # Base Options
        self.base_options_label = StrongBodyLabel("编码器选项: ")

        self.encoder_preset_label = BodyLabel("编码器预设: ")

        self.encoder_preset_value_slider = Slider(Qt.Horizontal)
        self.encoder_preset_value_slider.setRange(0, 9)
        self.encoder_preset_value_slider.setTickInterval(4) # 设置刻度间隔为5
        self.encoder_preset_value_slider.setValue(5) # 默认值为4
        self.encoder_preset_value_slider.setFixedWidth(160)
        
        self.encoder_preset_value_label = BodyLabel("None")

        self.encoder_tune_label = BodyLabel("编码器调优: ")
        self.encoder_tune_cBox = ComboBox()
        self.encoder_tune_cBox.setFixedWidth(130)


        self.encoder_profile_label = BodyLabel("编码器配置: ")
        self.encoder_profile_cBox = ComboBox()
        self.encoder_profile_cBox.setFixedWidth(100)

        self.encoder_level_label = BodyLabel("编码器级别: ")
        self.encoder_level_cBox = ComboBox()
        self.encoder_level_cBox.setFixedWidth(80)

        # 原定的 x264、x265、svtav1 高级选项, 考虑到参数过多, 目前并不考虑 
        self.encoder_option_more_button = PrimaryPushButton("高级选项")
        self.encoder_option_more_button.setVisible(False) 

        self.custom_options_textEdit = TextEdit()
        self.custom_options_textEdit.setPlaceholderText("在此输入 ffmpeg 视频相关参数(填入后将覆盖上方设置)")


    def _initLayout(self):
        # 编码器区域布局
        # area_ecoder_select
        self.encoder_format_hBoxLayout.addWidget(self.container_select_label)
        self.encoder_format_hBoxLayout.addWidget(self.container_select_combobox)
        self.encoder_format_hBoxLayout.addSpacing(10)
        self.encoder_format_hBoxLayout.addWidget(self.encoder_format_label)
        self.encoder_format_hBoxLayout.addWidget(self.encoder_forma_combobox)
        self.encoder_format_hBoxLayout.addStretch(1)
        self.encoder_format_hBoxLayout.setContentsMargins(0, 0, 0, 0)

        # Area_Ecoder_Preset
        self.using_preset_hBoxLayout.addWidget(self.using_preset_switch_label)
        self.using_preset_hBoxLayout.addWidget(self.using_preset_switch)
        self.using_preset_hBoxLayout.addSpacing(40)
        self.using_preset_hBoxLayout.addWidget(self.using_preset_label)
        self.using_preset_hBoxLayout.addWidget(self.using_preset_cBox)
        self.using_preset_hBoxLayout.addStretch(1)
        self.using_preset_hBoxLayout.setContentsMargins(0, 0, 0, 0)


        # Bitrate Control
        self.encoder_bitrate_control_box_hBox1Layout.addWidget(self.crf_rb, alignment=Qt.AlignLeft)
        self.encoder_bitrate_control_box_hBox1Layout.addWidget(self.crf_value_spinBox, alignment=Qt.AlignLeft)
        self.encoder_bitrate_control_box_hBox1Layout.addStretch(1)

        self.encoder_bitrate_control_box_2Box2Layout.addWidget(self.abr_rb, alignment=Qt.AlignLeft)
        self.encoder_bitrate_control_box_2Box2Layout.addWidget(self.abr_value_pinBox, alignment=Qt.AlignLeft)
        self.encoder_bitrate_control_box_2Box2Layout.addWidget(self.abr_value_unit_label, alignment=Qt.AlignLeft)
        self.encoder_bitrate_control_box_2Box2Layout.addStretch(1)


        self.encoder_bitrate_control_box_vBoxLayout.addWidget(self.bitrate_control_label)
        self.encoder_bitrate_control_box_vBoxLayout.addLayout(self.encoder_bitrate_control_box_hBox1Layout)
        self.encoder_bitrate_control_box_vBoxLayout.addLayout(self.encoder_bitrate_control_box_2Box2Layout)
        self.encoder_bitrate_control_box_vBoxLayout.addWidget(self.bitrate_control_2pass_checkBox)
        self.encoder_bitrate_control_box_vBoxLayout.addStretch(1)
        self.encoder_bitrate_control_box_vBoxLayout.setContentsMargins(0, 0, 0, 0)

        # Base Options
        self.encoder_base_option_box_hBox1Layout.addWidget(self.encoder_preset_label)
        self.encoder_base_option_box_hBox1Layout.addWidget(self.encoder_preset_value_slider)
        self.encoder_base_option_box_hBox1Layout.addWidget(self.encoder_preset_value_label)

        self.encoder_base_option_box_hBox2Layout.addWidget(self.encoder_profile_label)
        self.encoder_base_option_box_hBox2Layout.addWidget(self.encoder_profile_cBox)
        self.encoder_base_option_box_hBox2Layout.addWidget(self.encoder_level_label)
        self.encoder_base_option_box_hBox2Layout.addWidget(self.encoder_level_cBox)
        self.encoder_base_option_box_hBox2Layout.addStretch(1)

        self.encoder_base_option_box_hBox3Layout.addWidget(self.encoder_tune_label)
        self.encoder_base_option_box_hBox3Layout.addWidget(self.encoder_tune_cBox)
        self.encoder_base_option_box_hBox3Layout.addSpacing(10)
        self.encoder_base_option_box_hBox3Layout.addStretch(1)
        self.encoder_base_option_box_hBox3Layout.addWidget(self.encoder_option_more_button, alignment=Qt.AlignRight)


        self.encoder_base_option_box_vBoxLayout.addWidget(self.base_options_label)
        self.encoder_base_option_box_vBoxLayout.addLayout(self.encoder_base_option_box_hBox1Layout)
        self.encoder_base_option_box_vBoxLayout.addLayout(self.encoder_base_option_box_hBox2Layout)
        self.encoder_base_option_box_vBoxLayout.addLayout(self.encoder_base_option_box_hBox3Layout)
        self.encoder_base_option_box_vBoxLayout.addStretch(1)
        self.encoder_base_option_box_vBoxLayout.setContentsMargins(0, 0, 0, 0)


        # 添加左右设置区域
        self.custom_encoder_settings_hBoxLayout.addWidget(self.encoder_bitrate_control_box, alignment=Qt.AlignLeft)
        self.custom_encoder_settings_hBoxLayout.addSpacing(40)
        self.custom_encoder_settings_hBoxLayout.addWidget(self.encoder_base_option_box, alignment=Qt.AlignLeft)
        self.custom_encoder_settings_hBoxLayout.addStretch(1)
        self.custom_encoder_settings_hBoxLayout.setContentsMargins(0, 0, 0, 0)

        # 添加主布局
        # self.custom_Encoder_Settings_VBoxLayout.addWidget(self.custom_Encoder_Settings_Label)
        self.custom_encoder_settings_mianLayout.addWidget(self.custom_encoder_settings_box)
        self.custom_encoder_settings_mianLayout.addWidget(self.custom_options_textEdit)
        self.custom_encoder_settings_mianLayout.setContentsMargins(20, 10, 20, 10)

        self.custom_encoder_settings_mainBox.setLayout(self.custom_encoder_settings_mianLayout)
        self.custom_encoder_settings_mainBox.setVisible(False) 
        
        # Main Layout
        self.mainLayout.addWidget(self.encoder_format_box)
        self.mainLayout.addWidget(self.using_preset_box)
        self.mainLayout.addWidget(self.custom_encoder_settings_mainBox)
        self.mainLayout.addStretch(1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.viewLayout.addLayout(self.mainLayout)
        self.viewLayout.setContentsMargins(20, 10, 20, 10 )

    def _connect_signals(self):
        self.encoder_forma_combobox.currentTextChanged.connect(self.encoder_select)

        self.using_preset_switch.checkedChanged.connect(self.open_encoder_custom_area)

        self.bitrate_control_button_group.buttonClicked.connect(self.enable_2pass_checkBox)


    def encoder_select(self):
        self.using_preset_box.setEnabled(False)
        self.using_preset_cBox.clear()
        
        self.encoder_tune_cBox.clear()
        self.encoder_profile_cBox.clear()
        self.encoder_level_cBox.clear()

        self.crf_value_spinBox.setRange(0, 51)
        
        format = self.encoder_forma_combobox.currentText()
        if format in ["AVC (x264)", "HEVC (x265)", "AV1 (SVT)"]: 
            self.using_preset_switch.setChecked(True)
            self.using_preset_box.setEnabled(True)
            self.crf_value_spinBox.setSingleStep(0.5)

            self.encoder_option_more_button.setVisible(False)
        elif format in ["Copy", "FFV1"]:
            self.using_preset_switch.setChecked(True)
        else:
            self.using_preset_switch.setChecked(False)
            self.crf_value_spinBox.setSingleStep(1.0)
            self.encoder_option_more_button.setVisible(False)

        if format == "AVC (x264)":
            self.crf_rb.setText("恒定质量 (CRF): ")
            self.using_preset_cBox.addItems(list(self.custom_preset_config.get("x264", {}).keys()))
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Ultrafast", "Superfast", "Veryfast", "Faster", "Fast", "Medium", "Slow", "Slower", "Veryslow", "Placebo"])
            self.encoder_tune_cBox.addItems(["None", "Film", "Animation", "Grain", "Still Image", "PSNR", "SSIM", "Zero Latency"])
            self.encoder_profile_cBox.addItems(["Auto", "Baseline", "Main", "High"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "1b", "1.1", "1.2", "1.3", "2.0", "2.1", "2.2", "3.0", "3.1", "3.2", "4.0", "4.1", "4.2", "5.0", "5.1", "5.2", "6.0", "6.1", "6.2"])


        elif format == "AVC (NVEnc)":
            self.crf_rb.setText("恒定质量 (CQ): ")
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Fastest", "Faster", "Fast", "Medium", "Slow", "Slower", "Slowest"])
            self.encoder_tune_cBox.addItems(["None"])
            self.encoder_profile_cBox.addItems(["Auto", "Baseline", "Main", "High"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "1b", "1.1", "1.2", "1.3", "2.0", "2.1", "2.2", "3.0", "3.1", "3.2", "4.0", "4.1", "4.2", "5.0", "5.1", "5.2", "6.0", "6.1", "6.2"])

        elif format == "AVC (QSV)":
            self.crf_rb.setText("恒定质量 (ICQ): ")
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Veryfast", "Faster", "Fast", "Medium", "Slow", "Slower", "Veryslow"])
            self.encoder_tune_cBox.addItems(["None"])
            self.encoder_profile_cBox.addItems(["Auto", "Baseline", "Main", "High"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "1.1", "1.2", "1.3", "2.0", "2.1", "2.2", "3.0", "3.1", "3.2", "4.0", "4.1", "4.2", "5.0", "5.1", "5.2"])

        elif format == "AVC (AMF)":
            self.crf_rb.setText("恒定质量 (CQP): ")
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Speed", "Balanced", "Quality"])
            self.encoder_tune_cBox.addItems(["None"])
            self.encoder_profile_cBox.addItems(["Auto",  "Main"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "1b", "1.1", "1.2", "1.3", "2.0", "2.1", "2.2", "3.0", "3.1", "3.2", "4.0", "4.1", "4.2", "5.0", "5.1", "5.2"])

        elif format == "HEVC (x265)":
            self.crf_rb.setText("恒定质量 (CRF): ")
            self.using_preset_cBox.addItems(list(self.custom_preset_config.get("x265", {}).keys()))
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Ultrafast", "Superfast", "Veryfast", "Faster", "Fast", "Medium", "Slow", "Slower", "Veryslow", "Placebo"])
            self.encoder_tune_cBox.addItems(["None", "Animation", "Grain", "Fast Decode", "PSNR", "SSIM", "Zero Latency"])
            self.encoder_profile_cBox.addItems(["Auto", "Main", "Main10", "Main12"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "2.0", "2.1", "3.0", "3.1", "4.0", "4.1", "5.0", "5.1", "5.2", "6.0", "6.1", "6.2"])

        elif format == "HEVC (NVEnc)":
            self.crf_rb.setText("恒定质量 (CQ): ")
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Fastest", "Faster", "Fast", "Medium", "Slow", "Slower", "Slowest"])
            self.encoder_tune_cBox.addItems(["None"])
            self.encoder_profile_cBox.addItems(["Auto", "Main"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "2.0", "2.1", "3.0", "3.1", "4.0", "4.1", "5.0", "5.1", "5.2", "6.0", "6.1", "6.2"])

        elif format == "HEVC (QSV)":
            self.crf_rb.setText("恒定质量 (ICQ): ")
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Veryfast", "Faster", "Fast", "Medium", "Slow", "Slower", "Veryslow"])
            self.encoder_tune_cBox.addItems(["None"])
            self.encoder_profile_cBox.addItems(["Auto", "Main", "Main10"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "2.0", "2.1", "3.0", "3.1", "4.0", "4.1", "5.0", "5.1", "5.2"])

        elif format == "HEVC (AMF)":
            self.crf_rb.setText("恒定质量 (CQP): ")
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Speed", "Balanced", "Quality"])
            self.encoder_tune_cBox.addItems(["None"])
            self.encoder_profile_cBox.addItems(["Auto", "Main"])
            self.encoder_level_cBox.addItems(["Auto", "1.0", "2.0", "2.1", "3.0", "3.1", "4.0", "4.1", "5.0", "5.1", "5.2"])

        elif format == "AV1 (SVT)":
            self.crf_rb.setText("恒定质量 (CQ): ")
            self.crf_value_spinBox.setRange(0, 63)

            self.using_preset_cBox.addItems(list(self.custom_preset_config.get("SVTAV1", {}).keys()))
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["0 (最快)", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13 (最慢)"])
            self.encoder_tune_cBox.addItems(["Auto", "VQ", "iq", "PSNR", "SSIM", "ms-ssim"])
            self.encoder_profile_cBox.addItems(["Auto", "Main"])
            self.encoder_level_cBox.addItems(["Auto", "2.0", "2.1", "2.3", "3.0", "3.1", "4.0", "4.1", "4.3", "5.0", "5.1", "5.2", "5.3", "6.0", "6.1", "6.2", "6.3"])
        
        elif format == "VP9":
            self.crf_rb.setText("恒定质量 (CQ): ")
            self.crf_value_spinBox.setRange(0, 63)

            self.using_preset_switch.setChecked(False)
            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["Verfast", "Faster", "Fast", "Medium", "Slow", "Slower", "Veryslow", ])
            self.encoder_tune_cBox.addItems(["None", "Screen", "Film"])
            self.encoder_profile_cBox.addItems(["Auto"])
            self.encoder_level_cBox.addItems(["Auto"])
        
        elif format == "MPEG-4":
            self.crf_rb.setText("恒定质量 (QP): ")
            self.crf_value_spinBox.setRange(1, 31)

            self.slide_value_bind_label_text(self.encoder_preset_value_slider, self.encoder_preset_value_label, ["None"])
            self.encoder_tune_cBox.addItems(["None"])
            self.encoder_profile_cBox.addItems(["Auto"])
            self.encoder_level_cBox.addItems(["Auto"])


    def open_encoder_custom_area(self, checked):
        if checked:
            self.custom_encoder_settings_mainBox.setVisible(False)
            self.using_preset_cBox.setEnabled(True)
        else:
            self.custom_encoder_settings_mainBox.setVisible(True)
            self.using_preset_cBox.setEnabled(False)

    def enable_2pass_checkBox(self, button):
        if button == self.crf_rb:
            self.bitrate_control_2pass_checkBox.setEnabled(False)
            self.bitrate_control_2pass_checkBox.setChecked(False)

        elif button == self.abr_rb:
            self.bitrate_control_2pass_checkBox.setEnabled(True)

    def slide_value_bind_label_text(self, slider, label, preset_names: list):
        if not preset_names:
            label.setText("No Presets")
            slider.setEnabled(False)
            return

        slider.setRange(0, len(preset_names) - 1)

        def update_label(value):
            if 0 <= value < len(preset_names):
                label.setText(preset_names[value])
            else:
                label.setText("Invalid Preset")

        slider.setValue(int(len(preset_names) / 2))
        
        slider.valueChanged.connect(update_label)
        update_label(slider.value())  

    def get_state(self):
        """核心:将当前 UI 的所有状态打包成干净的数据字典"""
        # 判断码率控制模式的 Key (需要和刚才你写的 json 保持完全一致)
        if self.crf_rb.isChecked():
            rc_mode = "恒定质量 (CRF)"
        else:
            rc_mode = "平均码率 (ABR)"
            
        return {
            "container": self.container_select_combobox.currentText(),
            "encoder_format": self.encoder_forma_combobox.currentText(),
            "using_preset": self.using_preset_switch.isChecked(),
            "using_preset_name": self.using_preset_cBox.currentText(),
            # 码率控制
            "rc_mode": rc_mode,
            "quality_val": self.crf_value_spinBox.value(),
            "bitrate": self.abr_value_pinBox.value(),
            "is_2pass": self.bitrate_control_2pass_checkBox.isChecked(),
            # 高级选项
            "preset_val": self.encoder_preset_value_label.text().split(" ")[0].strip().lower(),
            "profile_name": self.encoder_profile_cBox.currentText().lower() if self.encoder_profile_cBox.currentText() != "" else None, 
            "level_val": self.encoder_level_cBox.currentText().lower() if self.encoder_level_cBox.currentText() != "" else None,
            "tuning_name": self.encoder_tune_cBox.currentText().lower() if self.encoder_tune_cBox.currentText() != "" else None,
            "custom_options": self.custom_options_textEdit.toPlainText()
        }

class AudioParamCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('音频编码设置')

        self.mainLayout = QVBoxLayout()
        
        # 基本控件
        self.encoder_format_label = BodyLabel("编码格式:")

        self.encoder_format_combobox = ComboBox()
        self.encoder_format_combobox.addItems(["Copy", "WAV", "FLAC", "ALAC", "AAC", "MP3", "Opus", "Vorbis", "AC3"])

        self.cbr_rb = RadioButton("CBR: ")
        self.cbr_rb.setChecked(True)
        self.cbr_value_ecombobox = EditableComboBox()
        self.cbr_value_ecombobox.setFixedWidth(80)
        self.cbr_value_ecombobox_label = BodyLabel("kbps")

        self.abr_rb = RadioButton("ABR: ")
        self.abr_value_ecombobox = EditableComboBox()
        self.abr_value_ecombobox.setFixedWidth(80)
        self.abr_value_ecombobox_label = BodyLabel("kbps")

        self.quality_rb = RadioButton("Quality: ")
        self.quality_slider = Slider(Qt.Horizontal)
        self.quality_slider.setFixedWidth(140)
        self.quality_slider.setRange(0, 10)
        self.quality_slider_label = BodyLabel("5")
        self.quality_slider_label.setFixedWidth(20)

        self.bitrate_control_button_group = QButtonGroup()
        self.bitrate_control_button_group.addButton(self.cbr_rb)
        self.bitrate_control_button_group.addButton(self.abr_rb)
        self.bitrate_control_button_group.addButton(self.quality_rb)

        
        self._initLayout()
        self._connect_signals()

    def _initLayout(self):
        # 创建布局
        self.encoder_format_box = QWidget()
        self.encoder_format_hBoxLayout = QHBoxLayout(self.encoder_format_box)


        self.bitrate_control_flowBox = QWidget()
        self.bitrate_control_flowBox_layout = FlowLayout(self.bitrate_control_flowBox, needAni=True)
        self.bitrate_control_flowBox.setVisible(False)

        self.bitrate_control_cbr_hBox = QWidget()
        self.bitrate_control_cbr_hLayout = QHBoxLayout(self.bitrate_control_cbr_hBox)

        self.bitrate_control_abr_hBox = QWidget()
        self.bitrate_control_abr_hLayout = QHBoxLayout(self.bitrate_control_abr_hBox)

        self.bitrate_control_quality_hBox = QWidget()
        self.bitrate_control_quality_hLayout = QHBoxLayout(self.bitrate_control_quality_hBox)


        # 添加布局
        self.encoder_format_hBoxLayout.addWidget(self.encoder_format_label)
        self.encoder_format_hBoxLayout.addWidget(self.encoder_format_combobox)
        self.encoder_format_hBoxLayout.addStretch(1)
        self.encoder_format_hBoxLayout.setContentsMargins(0, 0, 0, 5)

        self.bitrate_control_cbr_hLayout.addWidget(self.cbr_rb)
        self.bitrate_control_cbr_hLayout.addWidget(self.cbr_value_ecombobox)
        self.bitrate_control_cbr_hLayout.addWidget(self.cbr_value_ecombobox_label)
        self.bitrate_control_cbr_hLayout.addStretch(1)
        self.bitrate_control_cbr_hLayout.setContentsMargins(0, 0, 0, 0)

        self.bitrate_control_abr_hLayout.addWidget(self.abr_rb)
        self.bitrate_control_abr_hLayout.addWidget(self.abr_value_ecombobox)
        self.bitrate_control_abr_hLayout.addWidget(self.abr_value_ecombobox_label)
        self.bitrate_control_abr_hLayout.addStretch(1)
        self.bitrate_control_abr_hLayout.setContentsMargins(0, 0, 0, 0)

        self.bitrate_control_quality_hLayout.addWidget(self.quality_rb)
        self.bitrate_control_quality_hLayout.addWidget(self.quality_slider)
        self.bitrate_control_quality_hLayout.addWidget(self.quality_slider_label)
        self.bitrate_control_quality_hLayout.addStretch(1)
        self.bitrate_control_quality_hLayout.setContentsMargins(0, 0, 0, 0)


        self.bitrate_control_flowBox_layout.addWidget(self.bitrate_control_cbr_hBox)
        self.bitrate_control_flowBox_layout.addWidget(self.bitrate_control_abr_hBox)
        self.bitrate_control_flowBox_layout.addWidget(self.bitrate_control_quality_hBox)
        self.bitrate_control_flowBox_layout.setContentsMargins(0, 0, 0, 0)
        self.bitrate_control_flowBox_layout.setVerticalSpacing(10)
        self.bitrate_control_flowBox_layout.setHorizontalSpacing(20)

        row_height = max(
            self.bitrate_control_cbr_hBox.sizeHint().height(),
            self.bitrate_control_abr_hBox.sizeHint().height(),
            self.bitrate_control_quality_hBox.sizeHint().height(),
        )
        self.bitrate_control_cbr_hBox.setMinimumHeight(row_height)
        self.bitrate_control_abr_hBox.setMinimumHeight(row_height)
        self.bitrate_control_quality_hBox.setMinimumHeight(row_height)


        self.mainLayout.addWidget(self.encoder_format_box)
        self.mainLayout.addWidget(self.bitrate_control_flowBox)
        self.mainLayout.addStretch(1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.viewLayout.addLayout(self.mainLayout)
        self.viewLayout.setContentsMargins(20, 10, 20, 10)
    
    def _connect_signals(self):
        self.encoder_format_combobox.currentIndexChanged.connect(self.audio_encoder_select)
        self.quality_slider.valueChanged.connect(lambda value: self.quality_slider_label.setText(str(value)))

    def audio_encoder_select(self):
        format = self.encoder_format_combobox.currentText()
        if format in ["Copy", "WAV", "FLAC", "ALAC"]:
            self.bitrate_control_flowBox.setVisible(False)
        else:
            self.bitrate_control_flowBox.setVisible(True)
            self.bitrate_control_cbr_hBox.setEnabled(True)
            self.bitrate_control_abr_hBox.setEnabled(True)
            self.bitrate_control_quality_hBox.setEnabled(True)
            self.bitrate_control_quality_hBox.setVisible(True)
            self.abr_rb.setText("ABR: ")
            self.quality_rb.setVisible(True)
            self.quality_slider.setVisible(True)
            self.quality_slider_label.setVisible(True)

            self.cbr_rb.setChecked(True)

            self.cbr_value_ecombobox.clear()
            self.abr_value_ecombobox.clear()

        if format == "AAC":
            self.bitrate_control_cbr_hBox.setEnabled(False)

            self.abr_value_ecombobox.addItems(["64", "96", "128", "160", "192", "224", "256", "320", "384", "448", "512"])
            self.abr_value_ecombobox.setCurrentText("192")
            self.abr_rb.setChecked(True)

            self.quality_slider.setRange(1, 5)
            self.quality_slider.setValue(2)

        elif format == "MP3":
            self.abr_value_ecombobox.addItems(["32", "64", "96", "128", "160", "192", "224", "256", "320"])
            self.abr_value_ecombobox.setCurrentText("192")

            self.cbr_value_ecombobox.addItems(["32", "64", "96", "128", "160", "192", "224", "256", "320"])
            self.cbr_value_ecombobox.setCurrentText("192")

            self.quality_slider.setRange(1, 9)
            self.quality_slider.setValue(4)

        elif format == "Opus":
            self.cbr_value_ecombobox.addItems(["12", "24", "32", "48", "64", "96", "128", "160", "192", "256", "320", "384", "448", "512"])
            self.cbr_value_ecombobox.setCurrentText("96")

            self.abr_rb.setText("VBR: ")
            self.abr_value_ecombobox.addItems(["12", "24", "32", "48", "64", "96", "128", "160", "192", "256", "320", "384", "448", "512"])
            self.abr_value_ecombobox.setCurrentText("96")
            self.abr_rb.setChecked(True)


            self.quality_slider.setVisible(False)
            self.quality_rb.setVisible(False)
            self.quality_slider_label.setVisible(False)

        elif format == "Vorbis":
            self.bitrate_control_abr_hBox.setEnabled(False)
            self.bitrate_control_cbr_hBox.setEnabled(False)

            self.quality_slider.setRange(-1, 10)
            self.quality_slider.setValue(5)
            self.quality_rb.setChecked(True)

        elif format == "AC3":
            self.bitrate_control_abr_hBox.setEnabled(False)
            self.bitrate_control_quality_hBox.setEnabled(False)

            self.bitrate_control_quality_hBox.setVisible(False)

            self.cbr_value_ecombobox.addItems(["96", "112", "128", "160", "192", "224", "256", "320", "384", "448", "512", "576", "640"])
            self.cbr_value_ecombobox.setCurrentText("320")

    def get_state(self):
        """将音频部分的状态提取出来"""
        if self.cbr_rb.isChecked():
            rc_mode = "CBR"
            bitrate_raw = self.cbr_value_ecombobox.text()
            quality = 0
        elif self.abr_rb.isChecked():
            rc_mode = "ABR"
            bitrate_raw = self.abr_value_ecombobox.text()
            quality = 0
        else:
            rc_mode = "Quality"
            bitrate_raw = 0
            quality = self.quality_slider.value()

        bitrate_clean = str(bitrate_raw).lower().replace("kbps", "").replace("k", "").strip()
        return {
            "encoder_format": self.encoder_format_combobox.currentText(),
            "rc_mode": rc_mode,
            "bitrate": bitrate_clean if bitrate_clean else "128",
            "quality_val": quality
        }


class ImageParamCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._crop_dimension_master = "width"
        self._ratio_cw = None
        self._ratio_ch = None

        self.setTitle('图片编码设置')

        self.mainLayout = QVBoxLayout()

        # 基本控件
        self.encoder_format_label = BodyLabel("编码格式:")

        self.encoder_format_combobox = ComboBox()
        self.encoder_format_combobox.addItems(["PNG", "JPEG", "WEBP", "AVIF", "JXL", "ICO", "BMP", "TIFF"])
        self.encoder_format_combobox.setFixedWidth(80)

        self.image_Lossless_enable_label = BodyLabel("无损压缩")
        self.image_lossless_enable_switchButton = SwitchButton()
        self.image_lossless_enable_switchButton.setChecked(True)
        self.image_lossless_enable_switchButton.setOnText("")
        self.image_lossless_enable_switchButton.setOffText("")

        self.image_quality_label = BodyLabel("质量:")
        self.image_quality_slider = Slider(Qt.Horizontal)
        self.image_quality_slider.setRange(0, 10)
        self.image_quality_slider.setValue(8)
        
        self.image_quality_slider.setFixedWidth(140)
        self.image_quality_slider_label = BodyLabel("80")
        self.image_quality_slider_label.setFixedWidth(25)

        self.enable_image_base_process_label = BodyLabel("基本处理")
        self.enable_image_base_process_switchButton = SwitchButton()
        self.enable_image_base_process_switchButton.setChecked(False)
        self.enable_image_base_process_switchButton.setOnText("")
        self.enable_image_base_process_switchButton.setOffText("")


        self.image_base_process_label = StrongBodyLabel("基本处理: ")
        
        self.image_base_process_rotate_label = BodyLabel("旋转: ")
        self.image_base_process_rotate_comboBox = ComboBox()
        self.image_base_process_rotate_comboBox.setFixedWidth(130)
        self.image_base_process_rotate_comboBox.addItems(["不旋转", "顺时针90度", "逆时针90度", "旋转180度", "根据EXIF旋转"])

        self.image_base_process_mirror_label = BodyLabel("镜像: ")
        self.image_base_process_mirror_comboBox = ComboBox()
        self.image_base_process_mirror_comboBox.addItems(["不镜像", "水平镜像", "垂直镜像"])
        self.image_base_process_mirror_comboBox.setFixedWidth(100)

        self.image_base_process_crop_ratio_label = BodyLabel("裁剪比例: ")
        self.image_base_process_crop_ratio_eComboBox = EditableComboBox()
        self.image_base_process_crop_ratio_eComboBox.setFixedWidth(140)
        self.image_base_process_crop_ratio_eComboBox.addItems(["不裁剪", "原始比例", "1:1", "4:3", "16:9", "输入比例(x:y)"])


        self.image_base_process_crop_dimension_label = BodyLabel("裁剪尺寸: ")
        self.image_base_process_crop_dimension_width_lineEdit = LineEdit()
        self.image_base_process_crop_dimension_width_lineEdit.setPlaceholderText("宽度")
        self.image_base_process_crop_dimension_width_lineEdit.setFixedWidth(60)

        self.image_base_process_crop_dimension_multiply_label = BodyLabel("x")

        self.image_base_process_crop_dimension_height_lineEdit = LineEdit()
        self.image_base_process_crop_dimension_height_lineEdit.setPlaceholderText("高度")
        self.image_base_process_crop_dimension_height_lineEdit.setFixedWidth(60)


        self._initLayout()
        self._default_state()
        self._connect_signals()


    def _initLayout(self):
        # 创建布局
        self.encoder_format_box = QWidget()
        self.encoder_format_hBoxLayout = QHBoxLayout(self.encoder_format_box)

        self.image_quality_hBox = QWidget()
        self.image_quality_hBoxLayout = QHBoxLayout(self.image_quality_hBox)
        self.image_quality_hBoxLayout.setContentsMargins(0, 0, 0, 0)


        self.image_base_process_flowBox = QWidget()
        self.image_base_process_flowBoxLayout = FlowLayout(self.image_base_process_flowBox, True)

        self.image_base_process_rotate_hBox = QWidget()
        self.image_base_process_rotate_hBoxLayout = QHBoxLayout(self.image_base_process_rotate_hBox)
        self.image_base_process_rotate_hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.image_base_process_mirror_hBox = QWidget()
        self.image_base_process_mirror_hBoxLayout = QHBoxLayout(self.image_base_process_mirror_hBox)
        self.image_base_process_mirror_hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.image_base_process_crop_hBox = QWidget()
        self.image_base_process_crop_hBoxLayout = QHBoxLayout(self.image_base_process_crop_hBox)
        self.image_base_process_crop_hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.image_base_process_crop_dimension_hBox = QWidget()
        self.image_base_process_crop_dimension_hBoxLayout = QHBoxLayout(self.image_base_process_crop_dimension_hBox)
        self.image_base_process_crop_dimension_hBoxLayout.setContentsMargins(0, 0, 0, 0)



        # 添加布局
        self.image_quality_hBoxLayout.addWidget(self.image_quality_label)
        self.image_quality_hBoxLayout.addWidget(self.image_quality_slider)
        self.image_quality_hBoxLayout.addWidget(self.image_quality_slider_label)
        self.image_quality_hBoxLayout.addStretch(1)

        self.encoder_format_hBoxLayout.addWidget(self.encoder_format_label)
        self.encoder_format_hBoxLayout.addWidget(self.encoder_format_combobox)
        self.encoder_format_hBoxLayout.addSpacing(30)
        self.encoder_format_hBoxLayout.addWidget(self.image_Lossless_enable_label)
        self.encoder_format_hBoxLayout.addWidget(self.image_lossless_enable_switchButton)
        self.encoder_format_hBoxLayout.addSpacing(30)
        self.encoder_format_hBoxLayout.addWidget(self.image_quality_hBox)
        self.encoder_format_hBoxLayout.addSpacing(30)
        self.encoder_format_hBoxLayout.addWidget(self.enable_image_base_process_label)
        self.encoder_format_hBoxLayout.addWidget(self.enable_image_base_process_switchButton)
        self.encoder_format_hBoxLayout.addStretch(1)
        self.encoder_format_hBoxLayout.setContentsMargins(0, 0, 0, 0)


        self.image_base_process_rotate_hBoxLayout.addWidget(self.image_base_process_rotate_label)
        self.image_base_process_rotate_hBoxLayout.addWidget(self.image_base_process_rotate_comboBox)

        self.image_base_process_mirror_hBoxLayout.addWidget(self.image_base_process_mirror_label)
        self.image_base_process_mirror_hBoxLayout.addWidget(self.image_base_process_mirror_comboBox)

        self.image_base_process_crop_hBoxLayout.addWidget(self.image_base_process_crop_ratio_label)
        self.image_base_process_crop_hBoxLayout.addWidget(self.image_base_process_crop_ratio_eComboBox)

        self.image_base_process_crop_dimension_hBoxLayout.addWidget(self.image_base_process_crop_dimension_label)
        self.image_base_process_crop_dimension_hBoxLayout.addWidget(self.image_base_process_crop_dimension_width_lineEdit)
        self.image_base_process_crop_dimension_hBoxLayout.addWidget(self.image_base_process_crop_dimension_multiply_label)
        self.image_base_process_crop_dimension_hBoxLayout.addWidget(self.image_base_process_crop_dimension_height_lineEdit)
        

        self.image_base_process_flowBoxLayout.addWidget(self.image_base_process_rotate_hBox)
        self.image_base_process_flowBoxLayout.addWidget(self.image_base_process_mirror_hBox)
        self.image_base_process_flowBoxLayout.addWidget(self.image_base_process_crop_hBox)
        self.image_base_process_flowBoxLayout.addWidget(self.image_base_process_crop_dimension_hBox)
        self.image_base_process_flowBoxLayout.setContentsMargins(5, 0, 0, 0)
        self.image_base_process_flowBoxLayout.setHorizontalSpacing(40)
        self.image_base_process_flowBoxLayout.setVerticalSpacing(10)


        self.mainLayout.addWidget(self.encoder_format_box)
        # self.mainLayout.addWidget(self.image_base_process_label)
        self.mainLayout.addWidget(self.image_base_process_flowBox)
        self.mainLayout.addStretch(1)

        self.viewLayout.addLayout(self.mainLayout)
        self.viewLayout.setContentsMargins(20, 10, 20, 10)
    
    def _connect_signals(self):
        self.encoder_format_combobox.currentIndexChanged.connect(self.image_encoder_select)
        self.image_quality_slider.valueChanged.connect(lambda value: self.image_quality_slider_label.setText(str(value * 10)))
        self.image_lossless_enable_switchButton.checkedChanged.connect(self.image_lossless_quality_control)
        self.enable_image_base_process_switchButton.checkedChanged.connect(self.image_base_process_control)

        self.image_base_process_crop_ratio_eComboBox.currentTextChanged.connect(self.get_crop_ratio)
        self.image_base_process_crop_ratio_eComboBox.currentTextChanged.connect(self.set_crop_dimension_box)
        self.image_base_process_crop_dimension_width_lineEdit.textEdited.connect(self._on_crop_dimension_width_edited)
        self.image_base_process_crop_dimension_height_lineEdit.textEdited.connect(self._on_crop_dimension_height_edited)

    def image_lossless_quality_control(self, checked):
        if checked:
            self.image_quality_hBox.setVisible(False)
        else:
            self.image_quality_hBox.setVisible(True)

    def image_base_process_control(self, checked):
        if checked:
            self.image_base_process_flowBox.setVisible(True)
        else:
            self.image_base_process_flowBox.setVisible(False)

    def _default_state(self):
        # 默认 PNG 只开启无损, 关闭基本处理
        self.image_lossless_enable_switchButton.setEnabled(False)
        self.image_lossless_enable_switchButton.setChecked(True)

        self.image_quality_hBox.setVisible(False)

        self.image_base_process_flowBox.setVisible(False)

        self.image_base_process_crop_dimension_hBox.setEnabled(False)


    def image_encoder_select(self):
        format = self.encoder_format_combobox.currentText()
        if not format in ["ICO"]:
            # 重制无损选项和基本处理选项
            self.image_Lossless_enable_label.setEnabled(True)
            self.image_Lossless_enable_label.setVisible(True)
            self.image_lossless_enable_switchButton.setEnabled(True)
            self.image_lossless_enable_switchButton.setVisible(True)

            self.enable_image_base_process_switchButton.setEnabled(True)
            
            self.image_base_process_crop_ratio_eComboBox.setCurrentText("不裁剪")
            self.image_base_process_crop_ratio_eComboBox.setEnabled(True)

            self.image_base_process_crop_dimension_width_lineEdit.setText("")
            self.image_base_process_crop_dimension_height_lineEdit.setText("")

            
        if format in ["PNG", "TIFF", "BMP"]: 
            self.image_Lossless_enable_label.setEnabled(False)
            self.image_lossless_enable_switchButton.setEnabled(False)
            self.image_lossless_enable_switchButton.setChecked(True)

        elif format == "JPEG":
            self.image_Lossless_enable_label.setEnabled(False)
            self.image_lossless_enable_switchButton.setEnabled(False)
            self.image_lossless_enable_switchButton.setChecked(False)

        elif format == "ICO":
            self.image_Lossless_enable_label.setVisible(False)
            self.image_lossless_enable_switchButton.setVisible(False)
            self.image_quality_hBox.setVisible(False)

            self.enable_image_base_process_switchButton.setChecked(True)
            self.enable_image_base_process_switchButton.setEnabled(False)

            self.image_base_process_crop_ratio_eComboBox.setCurrentText("1:1")
            self.image_base_process_crop_ratio_eComboBox.setEnabled(False)

            self.image_base_process_crop_dimension_width_lineEdit.setText("256")
            self.image_base_process_crop_dimension_height_lineEdit.setText("256")

    def set_crop_dimension_box(self):
        """初始化裁剪尺寸输入框的状态和内容"""
        self.image_base_process_crop_dimension_hBox.setEnabled(True)
        self.image_base_process_crop_dimension_width_lineEdit.setText("")
        self.image_base_process_crop_dimension_height_lineEdit.setText("")

        ratio_text = self.image_base_process_crop_ratio_eComboBox.currentText().strip()
        if ratio_text == "不裁剪":
            self.image_base_process_crop_dimension_hBox.setEnabled(False)
        else:
            self.image_base_process_crop_dimension_hBox.setEnabled(True)

    def set_original_size(self, width, height):
        """获取加载图片的原始尺寸"""
        self._original_width = width
        self._original_height = height
        self.get_crop_ratio()

    def get_crop_ratio(self):
        """根据裁剪比例选项计算宽高比"""
        ratio_text = self.image_base_process_crop_ratio_eComboBox.currentText().strip()
        if ratio_text == "不裁剪":
            self._ratio_cw, self._ratio_ch = None, None
            return self._ratio_cw, self._ratio_ch

        elif ratio_text == "原始比例":
            width = self._original_width if hasattr(self, "_original_width") else None
            height = self._original_height if hasattr(self, "_original_height") else None
            self._ratio_cw = round(int(width) / int(height), 4)
            self._ratio_ch = round(int(height) / int(width), 4)
        else:
            ratio_text = ratio_text.replace("：", ":") or ratio_text.replace(" ", "")
            parts = ratio_text.split(":")
            if len(parts) == 2:
                try:
                    ratio_w = int(parts[0])
                    ratio_h = int(parts[1])
                    self._ratio_cw = round(ratio_w / ratio_h, 4) if ratio_w > 0 and ratio_h > 0 else None
                    self._ratio_ch = round(ratio_h / ratio_w, 4) if ratio_w > 0 and ratio_h > 0 else None
                except ValueError:
                    self._ratio_cw, self._ratio_ch = None, None
        return self._ratio_cw, self._ratio_ch

    def _on_crop_dimension_width_edited(self, _):
        self._crop_dimension_master = "width"
        self.ratio_bind_crop_dimension("width")

    def _on_crop_dimension_height_edited(self, _):
        self._crop_dimension_master = "height"
        self.ratio_bind_crop_dimension("height")

    def ratio_bind_crop_dimension(self, master=None):
        """根据 master (宽或高) 和当前的宽高比, 自动计算另一个维度的值, 并更新输入框"""
        if master is None:
            master = self._crop_dimension_master

        width_text = self.image_base_process_crop_dimension_width_lineEdit.text().strip()
        height_text = self.image_base_process_crop_dimension_height_lineEdit.text().strip()

        if master == "width":
            if not width_text:
                self.image_base_process_crop_dimension_height_lineEdit.clear()
                return

            try:
                width = int(width_text)
                if width > 0:
                    height = max(1, round(width * self._ratio_ch)) if self._ratio_ch else None
                    self.image_base_process_crop_dimension_height_lineEdit.setText(str(height))
            except ValueError:
                pass

        elif master == "height":
            if not height_text:
                self.image_base_process_crop_dimension_width_lineEdit.clear()
                return

            try:
                height = int(height_text)
                if height > 0:
                    width = max(1, round(height * self._ratio_cw)) if self._ratio_cw else None
                    self.image_base_process_crop_dimension_width_lineEdit.setText(str(width))
            except ValueError:
                pass
        

    def update_quality_slider_value(self):
        if self.image_lossless_enable_switchButton.isChecked():
            return
        format = self.encoder_format_combobox.currentText()
        value = self.image_quality_slider.value() * 10
        if format == "WEBP":
            # 获取slider的当前值
            quality_val = value
        elif format == "AVIF":
            quality_val = int(float(63 - value * 62 / 100))
        elif format == "JXL":
            quality_val = float(15 - value * 14 / 100)
        elif format == "JPEG":
            quality_val = int(float(31 - value * 29 / 100))
        else:
            quality_val = None
        return quality_val

    def get_state(self):
        quality_val = self.update_quality_slider_value()
        if quality_val is None:
            # 如果是无损等情况，fallback 到默认值或 slider 原始值
            quality_val = getattr(self, 'image_quality_slider', type('obj', (object,), {'value': lambda: 75})).value()

        # 获取裁剪相关参数
        crop_w = self.image_base_process_crop_dimension_width_lineEdit.text().strip()
        crop_h = self.image_base_process_crop_dimension_height_lineEdit.text().strip()

        return {
            "encoder_format": self.encoder_format_combobox.currentText(),
            "is_lossless": self.image_lossless_enable_switchButton.isChecked() if hasattr(self, 'image_lossless_enable_switchButton') else False,
            "quality_val": quality_val,
            "rotate": self.image_base_process_rotate_comboBox.currentText() if hasattr(self, 'image_base_process_rotate_comboBox') else "",
            "flip": self.image_base_process_mirror_comboBox.currentText() if hasattr(self, 'image_base_process_mirror_comboBox') else "",
            "crop_w": crop_w if crop_w.isdigit() else None,
            "crop_h": crop_h if crop_h.isdigit() else None
        }

class SubtitleParamCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('字幕编码设置')

        self.mainLayout = QVBoxLayout()
        self.hBoxLayout = QHBoxLayout()

        self.subtitle_format_label = BodyLabel("字幕格式:")
        self.subtitle_format_combobox = ComboBox()
        self.subtitle_format_combobox.addItems(["ASS", "SRT", "LRC", "VTT"])
        self.subtitle_format_combobox.setFixedWidth(80)

        self.hBoxLayout.addWidget(self.subtitle_format_label)
        self.hBoxLayout.addWidget(self.subtitle_format_combobox)
        self.hBoxLayout.addStretch(1)
        self.mainLayout.addLayout(self.hBoxLayout)
        self.mainLayout.addStretch(1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.viewLayout.addLayout(self.mainLayout)
        self.viewLayout.setContentsMargins(20, 10, 20, 10)

    def get_state(self):
        return {
            "encoder_format": self.subtitle_format_combobox.currentText()
        }


class OutputCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('输出设置')

        self.mainLayout = QVBoxLayout()
        self.hBoxLayout1 = QHBoxLayout()
        self.hBoxLayout2 = QHBoxLayout()

        self.custom_output_file_name_checkBox = CheckBox("自定义文件名后缀")
        self.custom_output_file_name_lineEdit = LineEdit()
        self.custom_output_file_name_lineEdit.setPlaceholderText("例如: \"_encoded\", 留空保持原文件名")
        self.custom_output_file_name_lineEdit.setFixedWidth(250)

        self.using_default_output_path_checkBox = CheckBox("使用源目录: ")

        self.output_path_label = BodyLabel("输出路径:")
        self.output_path_lineEdit = LineEdit()
        self.output_browse_button = PrimaryPushButton("浏览")

        self._initLayout()
        self._connect_signals()

    def _initLayout(self):
        self.hBoxLayout1.addWidget(self.custom_output_file_name_checkBox)
        self.hBoxLayout1.addWidget(self.custom_output_file_name_lineEdit)
        self.hBoxLayout1.addStretch(1)

        self.hBoxLayout2.addWidget(self.output_path_label)
        self.hBoxLayout2.addWidget(self.output_path_lineEdit)
        self.hBoxLayout2.addWidget(self.using_default_output_path_checkBox)
        self.hBoxLayout2.addWidget(self.output_browse_button)

        self.mainLayout.addLayout(self.hBoxLayout1)
        self.mainLayout.addLayout(self.hBoxLayout2)
        self.mainLayout.addStretch(1)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.viewLayout.addLayout(self.mainLayout)
        self.viewLayout.setContentsMargins(20, 10, 10, 10)

    def _connect_signals(self):
        self.using_default_output_path_checkBox.stateChanged.connect(self.using_default_output_path)
        self.output_browse_button.clicked.connect(self.browse_output_path)

    def using_default_output_path(self, state):
        if state == self.using_default_output_path_checkBox.isChecked():
            self.output_path_lineEdit.setEnabled(True)
            self.output_browse_button.setEnabled(True)
        else:
            self.output_path_lineEdit.setEnabled(False)
            self.output_browse_button.setEnabled(False)

    def browse_output_path(self):
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", )
        if directory:
            self.output_path_lineEdit.setText(directory)

    def get_state(self):
        return {
            "use_custom_suffix": self.custom_output_file_name_checkBox.isChecked(),
            "custom_suffix": self.custom_output_file_name_lineEdit.text().strip(),
            "use_source_dir": self.using_default_output_path_checkBox.isChecked(),
            "output_dir": self.output_path_lineEdit.text().strip()
        }
