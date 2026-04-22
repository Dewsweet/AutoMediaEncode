# coding: utf-8
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QAbstractItemView, QGroupBox, QCompleter

from qfluentwidgets import (HeaderCardWidget, SimpleCardWidget, TableWidget, ScrollArea, HorizontalSeparator, SmoothMode,
                            CheckBox, BodyLabel, ComboBox, LineEdit, PrimaryPushButton, StrongBodyLabel, EditableComboBox, PushButton, ToolButton, IconWidget, RadioButton)
from qfluentwidgets import FluentIcon as FIF

class InputFilesCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('输入文件')

        self.mainBox = QWidget()
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.table = TableWidget(self)

        self.table.setBorderVisible(False)
        # self.table.setBorderRadius(5)
        self.table.setColumnCount(4)
        self.table.setRowCount(3)
        self.table.setHorizontalHeaderLabels(["文件名", "容器", "文件大小", "文件路径"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().hide()

        testInfo = [
            ['Placeholder1.mkv', 'Matroska', '500 MiB', r'C:\Users\Dewsweet\Desktop\.Temp\Placeholder1.mkv'],
            ['ph2.265', 'HEVC/H.265', '1.2 GiB', r'C:\Users\Dewsweet\Desktop\.Temp\ph2.265'],
            ['ph3.aac', 'AAC', '200 MiB', r'C:\Users\Dewsweet\Desktop\.Temp\ph3.aac']
        ]

        for i, row in enumerate(testInfo):
            for j in range(len(row)):
                self.table.setItem(i, j, QTableWidgetItem(row[j]))


        self.mainLayout.addWidget(self.table)
        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(0, 5, 0, 0)

class TrackCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('确认轨道')

        self.mainBox = QWidget(self)

        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.table = TableWidget(self)
        self.hearderItems = ['编码格式', '类型', '复制项目', '语言', '名称', 'ID', '默认轨道', '文件路径', '延迟']

        self.table.setBorderVisible(False)
        # self.table.setBorderRadius(5)
        self.table.setColumnCount(len(self.hearderItems))
        self.table.setRowCount(3)
        self.table.setHorizontalHeaderLabels(self.hearderItems)
        self.table.horizontalHeader().setStretchLastSection(True) 
        self.table.verticalHeader().hide()

        testInfo = [
            ['HEVC/H.265', '视频', '是', 'und', '', '0', '是', r'C:\Users\Dewsweet\Desktop\.Temp\Placeholder1.mkv', ''],
            ['AAC', '音频', '是', 'und', '', '1', '是', r'C:\Users\Dewsweet\Desktop\.Temp\ph3.aac', ''],
            ['ASS', '字幕', '是', 'und', '', '2', '是', r'C:\Users\Dewsweet\Desktop\.Temp\ph4.ass', '']
        ]

        for i, row in enumerate(testInfo):
            for j in range(len(row)):
                self.table.setItem(i, j, QTableWidgetItem(row[j]))

        self.mainLayout.addWidget(self.table)
        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(0, 5, 0, 0)


class GroupExpandBox(QWidget):
    def __init__(self, title:str, parent=None):
        super().__init__(parent)
        self.is_expanded = True

        self.mainBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.headerBox = QWidget(self)
        self.headerLayout = QHBoxLayout(self.headerBox)
        self.headerLayout.setContentsMargins(0, 0, 0, 0)

        self.titleIcon = IconWidget(FIF.CHEVRON_DOWN_MED, self)
        self.titleIcon.setFixedSize(10, 10)
        self.titleLabel = BodyLabel(title, self)

        self.headerLayout.addWidget(self.titleIcon)
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch(1)

        self.view = QWidget(self)
        self.view.setObjectName("view")
        self.view.setStyleSheet("""#view {border: 1px solid #CCCCCC; border-radius: 6px; background-color: #F9F9F9;}""")
        self.viewLayout = QVBoxLayout(self.view)
        self.viewLayout.setContentsMargins(10, 10, 10, 10)
        self.viewLayout.setSpacing(5)

        self.mainLayout.addWidget(self.headerBox)
        self.mainLayout.addWidget(self.view)
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)

        self.headerBox.mouseReleaseEvent = lambda e: self.toggle_expand()

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        # self.view.setVisible(self.is_expanded)
        if self.is_expanded:
            self.titleIcon.setIcon(FIF.CHEVRON_DOWN_MED)
            self.view.setFixedHeight(self.view.sizeHint().height())

        else:
            self.titleIcon.setIcon(FIF.CHEVRON_RIGHT_MED)
            self.view.setFixedHeight(2)

    def addWidget(self, widget):
        self.viewLayout.addWidget(widget)
    
    def addLayout(self, layout):
        self.viewLayout.addLayout(layout)

class OptionCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("选项与属性")

        self.mainBox = QWidget()
        self.mainBox.setStyleSheet("background-color: transparent;")
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(20, 10, 20, 10)

        self.scrollArea = ScrollArea()
        self.scrollArea.setObjectName("scrollArea")
        self.scrollArea.setStyleSheet("""#scrollArea {background-color: transparent; border: none;}""")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.mainBox)
        # self.scrollArea.setSmoothMode(SmoothMode.NO_SMOOTH)

        self._initWidget()
        self._generalOptionsArea()
        self._timestempOptionsArea()
        self._video_properties_area()
        self._initLayout()
        self._connectSignals()

    def _initWidget(self):
        self.containerLayout = QHBoxLayout()
        self.containerLayout.setContentsMargins(0, 0, 0, 0)

        self.containerLabel = BodyLabel('选择容器: ', self)
        self.containerCb = ComboBox()
        self.containerCb.addItems(['MKV', 'MP4', 'MOV'])

        self.using_hard_sub_checkbox = CheckBox('编码硬字幕', self)

        self.separator = HorizontalSeparator(self)

        self.containerLayout.addWidget(self.containerLabel)
        self.containerLayout.addWidget(self.containerCb)
        self.containerLayout.addStretch(1)

    def _generalOptionsArea(self):
        self.go_text_vLayout = QVBoxLayout()
        self.go_edit_vLayout = QVBoxLayout()
        self.go_hLayout = QHBoxLayout()

        self.general_options_group = GroupExpandBox('通用选项', self)

        self.track_enabled_label = BodyLabel('启用轨道: ', self)
        self.track_enabled_cb = ComboBox()
        self.track_enabled_cb.addItems(['是', '否'])

        self.track_name_label = BodyLabel('轨道名称: ', self)
        self.track_name_lineEdit = LineEdit()

        self.track_language_label = BodyLabel('轨道语言: ', self)
        self.track_language_lineEdit = EditableComboBox()
        self.language_items = ['und', 'zh', 'en', 'jpn', 'kor']
        self.track_language_lineEdit.addItems(self.language_items)
        self.language_completer = QCompleter(self.language_items, self.track_language_lineEdit)
        self.language_completer.setMaxVisibleItems(3)
        self.track_language_lineEdit.setCompleter(self.language_completer)

        self.track_flag_label = BodyLabel('轨道标记: ', self)
        self.track_flag_cb = ComboBox()
        self.flag_Items = ['无', '默认轨道', '强制显示', '听觉障碍', '视觉障碍', '文字描述', '原始语言', '评论轨道']
        self.track_flag_cb.addItems(self.flag_Items)
        self.track_flag_add_btn = ToolButton(FIF.ADD, self)
        self.track_falg_layout = QHBoxLayout()
        self.track_falg_layout.addWidget(self.track_flag_cb)
        self.track_falg_layout.addWidget(self.track_flag_add_btn)

        self.track_flag_add1_Label = BodyLabel(' ', self)
        self.track_flag_add1_cb = ComboBox()
        self.track_flag_add1_cb.addItems(self.flag_Items)
        self.track_flag_remve1_btn = ToolButton(FIF.REMOVE, self)
        self.track_flag_add1_layout = QHBoxLayout()
        self.track_flag_add1_layout.addWidget(self.track_flag_add1_cb)
        self.track_flag_add1_layout.addWidget(self.track_flag_remve1_btn)

        self.compression_method = BodyLabel('压缩方法: ', self)
        self.compression_method_cb = ComboBox()
        self.compression_method_cb.addItems(['自动决定', '不做额外压缩', 'zlib'])

        self.track_label_lable = BodyLabel('标签: ', self)
        self.track_label_lineEdit = LineEdit()

        
        self.go_text_vLayout.addWidget(self.track_enabled_label, alignment=Qt.AlignVCenter)
        self.go_text_vLayout.addWidget(self.track_name_label, alignment=Qt.AlignVCenter)
        self.go_text_vLayout.addWidget(self.track_language_label, alignment=Qt.AlignVCenter)
        self.go_text_vLayout.addWidget(self.track_flag_label, alignment=Qt.AlignVCenter)
        self.go_text_vLayout.addWidget(self.track_flag_add1_Label, alignment=Qt.AlignVCenter)
        self.go_text_vLayout.addWidget(self.compression_method, alignment=Qt.AlignVCenter)
        self.go_text_vLayout.addWidget(self.track_label_lable, alignment=Qt.AlignVCenter)

        self.go_edit_vLayout.addWidget(self.track_enabled_cb)
        self.go_edit_vLayout.addWidget(self.track_name_lineEdit)
        self.go_edit_vLayout.addWidget(self.track_language_lineEdit)
        self.go_edit_vLayout.addLayout(self.track_falg_layout)
        self.go_edit_vLayout.addLayout(self.track_flag_add1_layout)
        self.go_edit_vLayout.addWidget(self.compression_method_cb)
        self.go_edit_vLayout.addWidget(self.track_label_lineEdit)

        self.go_hLayout.addLayout(self.go_text_vLayout)
        self.go_hLayout.addLayout(self.go_edit_vLayout)

    def _timestempOptionsArea(self):
        self.to_text_vLayout = QVBoxLayout()
        self.to_edit_vLayout = QVBoxLayout()
        self.to_hLayout = QHBoxLayout()

        self.timestemp_options_group = GroupExpandBox('时间戳和默认帧时长', self)

        self.delay_label = BodyLabel('延迟(毫秒): ', self)
        self.delay_lineEdit = LineEdit()

        self.timestemp_extend_label = BodyLabel('延展比例: ', self)
        self.timestemp_extend_lineEdit = LineEdit()

        self.default_frame_duration_label = BodyLabel('默认帧时长和帧率: ', self)
        self.default_frame_duration_lineEdit = EditableComboBox()
        self.frame_duration_items = ['24p', '25p', '30p', '48p', '50i', '50p', '60i', '60p', '24000/1001p', '30000/1001p', '48000/1001p', '60000/1001i', '60000/1001p']
        self.default_frame_duration_lineEdit.addItems(self.frame_duration_items)

        self.timestemp_files_label = BodyLabel('时间戳文件: ', self)
        self.timestemp_files_lineEdit = LineEdit()
        self.timestemp_files_view_btn = PushButton('...', self)
        self.timestemp_files_layout = QHBoxLayout()
        self.timestemp_files_layout.addWidget(self.timestemp_files_lineEdit)
        self.timestemp_files_layout.addWidget(self.timestemp_files_view_btn)

        self.corrent_timestemp_checkbox = CheckBox('校正时间戳', self)

        self.to_text_vLayout.addWidget(self.delay_label, alignment=Qt.AlignVCenter)
        self.to_text_vLayout.addWidget(self.timestemp_extend_label, alignment=Qt.AlignVCenter)
        self.to_text_vLayout.addWidget(self.default_frame_duration_label, alignment=Qt.AlignVCenter)
        self.to_text_vLayout.addWidget(self.timestemp_files_label, alignment=Qt.AlignVCenter)

        self.to_edit_vLayout.addWidget(self.delay_lineEdit)
        self.to_edit_vLayout.addWidget(self.timestemp_extend_lineEdit)
        self.to_edit_vLayout.addWidget(self.default_frame_duration_lineEdit)
        self.to_edit_vLayout.addLayout(self.timestemp_files_layout)

        self.to_hLayout.addLayout(self.to_text_vLayout)
        self.to_hLayout.addLayout(self.to_edit_vLayout)

    def _video_properties_area(self):
        self.vp_text_vLayout = QVBoxLayout()
        self.vp_edit_vLayout = QVBoxLayout()
        self.vp_hLayout = QHBoxLayout()

        self.display_aspect_edit_Hlayout = QHBoxLayout()

        self.video_properties_group = GroupExpandBox('视频属性', self)

        self.setting_aspect_ratio_rb = RadioButton('设置宽高比: ', self)
        self.aspect_ratio_cb = EditableComboBox()
        self.aspect_ratio_items = ['1/1', '4/3', '16/9', '21/9', '1.66', '1.85', '2.00', '2.21', '2.35', '2.40']
        self.aspect_ratio_cb.addItems(self.aspect_ratio_items)

        self.setting_display_aspect_rb = RadioButton('显示宽度/高度: ', self)
        self.display_aspect_width_lineEdit = LineEdit()
        self.display_aspect_height_x_label = BodyLabel('x', self)
        self.display_aspect_height_lineEdit = LineEdit()
        self.display_aspect_edit_Hlayout.addWidget(self.display_aspect_width_lineEdit)
        self.display_aspect_edit_Hlayout.addWidget(self.display_aspect_height_x_label)
        self.display_aspect_edit_Hlayout.addWidget(self.display_aspect_height_lineEdit)

        self.video_crop_label = BodyLabel('画面裁剪: ', self)
        self.video_crop_lineEdit = LineEdit()

        self.vp_text_vLayout.addWidget(self.setting_aspect_ratio_rb, alignment=Qt.AlignVCenter)
        self.vp_text_vLayout.addWidget(self.setting_display_aspect_rb, alignment=Qt.AlignVCenter)
        self.vp_text_vLayout.addWidget(self.video_crop_label, alignment=Qt.AlignVCenter)

        self.vp_edit_vLayout.addWidget(self.aspect_ratio_cb)
        self.vp_edit_vLayout.addLayout(self.display_aspect_edit_Hlayout)
        self.vp_edit_vLayout.addWidget(self.video_crop_lineEdit)

        self.vp_hLayout.addLayout(self.vp_text_vLayout)
        self.vp_hLayout.addLayout(self.vp_edit_vLayout)

    def _initLayout(self):
        # General options layout
        self.general_options_group.addLayout(self.go_hLayout)

        # TimeStemp options layout
        self.timestemp_options_group.addLayout(self.to_hLayout)
        self.timestemp_options_group.addWidget(self.corrent_timestemp_checkbox)

        # Video properties layout
        self.video_properties_group.addLayout(self.vp_hLayout)


        self.mainLayout.addLayout(self.containerLayout)
        self.mainLayout.addWidget(self.using_hard_sub_checkbox)
        self.mainLayout.addWidget(self.separator)
        self.mainLayout.addWidget(self.general_options_group, alignment=Qt.AlignTop)
        self.mainLayout.addWidget(self.timestemp_options_group, alignment=Qt.AlignTop)
        self.mainLayout.addWidget(self.video_properties_group, alignment=Qt.AlignTop)
        self.mainLayout.addStretch(1)

        self.viewLayout.addWidget(self.scrollArea)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

    def _connectSignals(self):
        pass

class OutputCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(10, 10, 10, 10)

        self.mainBox = QWidget()
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.OutputPathLayout = QHBoxLayout()

        self.output_path_label = BodyLabel('输出路径: ')
        self.output_path_lineEdit = LineEdit()

        self.output_path_view_button = PrimaryPushButton('浏览')

        self.OutputPathLayout.addWidget(self.output_path_label)
        self.OutputPathLayout.addWidget(self.output_path_lineEdit)
        self.OutputPathLayout.addWidget(self.output_path_view_button)


        self.mainLayout.addLayout(self.OutputPathLayout)


