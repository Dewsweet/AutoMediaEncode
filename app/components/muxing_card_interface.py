# coding: utf-8
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidgetItem, QAbstractItemView, QGroupBox, QCompleter, QDialog, QTableWidget, QMenu

from qfluentwidgets import (HeaderCardWidget, SimpleCardWidget, TableWidget, ScrollArea, HorizontalSeparator, SmoothMode, RoundMenu, Action, CheckableMenu, 
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

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)  # 禁止自动换行，保持单行显示
        self.table.setColumnCount(4)
        self.table.setRowCount(3)

        self.table.setHorizontalHeaderLabels(["文件名", "容器", "文件大小", "文件路径"])
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 400)

        testInfo = [
            ['Placeholder1.mkv', 'Matroska', '500 MiB', r'C:\Users\Dewsweet\Desktop\.Temp\Placeholder1.mkv'],
            ['ph2.265', 'HEVC/H.265', '1.2 GiB', r'C:\Users\Dewsweet\Desktop\.Temp\ph2.265'],
            ['ph3.aac', 'AAC', '200 MiB', r'C:\Users\Dewsweet\Desktop\.Temp\ph3.aac']
        ]
        for i, row in enumerate(testInfo):
            for j in range(len(row)):
                self.table.setItem(i, j, QTableWidgetItem(row[j]))

        # self.table.resizeColumnsToContents() 
        self.header = self.table.horizontalHeader()
        self.header.setStretchLastSection(True) 
        self.header.setSectionsMovable(True) 
        self.header.setTextElideMode(Qt.ElideRight) 
        self.header.setContextMenuPolicy(Qt.CustomContextMenu) 

        self.table.verticalHeader().hide()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.mainLayout.addWidget(self.table)
        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(0, 5, 0, 0)

        self._connectSignals()

    def _connectSignals(self):
        self.header.customContextMenuRequested.connect(self.show_header_menu)
        self.table.customContextMenuRequested.connect(self.show_content_menu)

    def show_header_menu(self, pos):
        menu = CheckableMenu(parent=self)
        
        reset_action = Action("重置所有列", self)
        reset_action.triggered.connect(self.reset_columns)
        menu.addAction(reset_action)
        menu.addSeparator()
        for i in range(1, self.table.columnCount()):
            col_name = self.table.horizontalHeaderItem(i).text()
            action = Action(col_name, self)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))

            action.triggered.connect(lambda checked, col_index=i: self.table.setColumnHidden(col_index, not checked))
            menu.addAction(action)

        menu.exec(self.header.mapToGlobal(pos))

    def reset_columns(self):
        """恢复所有列的原始顺序和宽度, 并全部显示"""
        for logical_index in range(1, self.table.columnCount()):
            self.table.setColumnHidden(logical_index, False)
            current_visual_index = self.header.visualIndex(logical_index)
            self.header.moveSection(current_visual_index, logical_index)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 400)

    def show_content_menu(self, pos):
        menu = RoundMenu(parent=self)
        add_files_action = Action(FIF.ADD, "添加文件", self, triggered=lambda: print("添加文件"))
        remove_file_action = Action(FIF.REMOVE, "移除文件", self, triggered=lambda: print("移除文件"))
        remove_all_action = Action("移除所有文件", self, triggered=lambda: print("清空列表"))
        menu.addActions([add_files_action, remove_file_action, remove_all_action])
        menu.exec(self.table.viewport().mapToGlobal(pos))

class TrackCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('确认轨道')

        self.mainBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.table = TableWidget(self)
        self.hearderItems = ['编码格式', '类型', '语言', '名称', 'ID', '默认轨道', '属性', '输入文件', '延迟']

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)  # 禁止自动换行，保持单行显示
        self.table.setColumnCount(len(self.hearderItems))
        self.table.setRowCount(3)
        self.table.setHorizontalHeaderLabels(self.hearderItems)
        self.table.setColumnWidth(0, 115)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 65)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 30)
        self.table.setColumnWidth(5, 65)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 180)
        self.table.setColumnWidth(8, 40)

        testInfo = [
            ['HEVC/H.265', '🎬 视频', 'und', '', '0', '是', '1920x1080 px', 'Placeholder1.mkv', ''],
            ['AAC', '🎧 音频', 'und', '', '1', '是', '48000 Hz 2 ch','ph3.aac', ''],
            ['ASS', '📚 字幕', 'und', '', '2', '是', '','ph4.ass', '']
        ]

        for i, row in enumerate(testInfo):
            for j in range(len(row)):
                self.table.setItem(i, j, QTableWidgetItem(row[j]))

        # self.table.resizeColumnsToContents() 
        self.header = self.table.horizontalHeader()
        self.header.setStretchLastSection(True) 
        self.header.setSectionsMovable(True) 
        self.header.setTextElideMode(Qt.ElideRight) 
        self.header.setContextMenuPolicy(Qt.CustomContextMenu) 

        self.table.verticalHeader().hide()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.mainLayout.addWidget(self.table)
        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(0, 5, 0, 0)

        self._connectSignals()

    def _connectSignals(self):
        self.header.customContextMenuRequested.connect(self.show_header_menu)
        self.table.customContextMenuRequested.connect(self.show_content_menu)

    def show_header_menu(self, pos):
        menu = CheckableMenu(parent=self)
        
        reset_action = Action("重置所有列", self)
        reset_action.triggered.connect(self.reset_columns)
        menu.addAction(reset_action)
        menu.addSeparator()
        for i in range(1, self.table.columnCount()):
            col_name = self.table.horizontalHeaderItem(i).text()
            action = Action(col_name, self)
            action.setCheckable(True)
            action.setChecked(not self.table.isColumnHidden(i))

            action.triggered.connect(lambda checked, col_index=i: self.table.setColumnHidden(col_index, not checked))
            menu.addAction(action)

        menu.exec(self.header.mapToGlobal(pos))

    def reset_columns(self):
        """恢复所有列的原始顺序和宽度, 并全部显示"""
        for logical_index in range(1, self.table.columnCount()):
            self.table.setColumnHidden(logical_index, False)
            current_visual_index = self.header.visualIndex(logical_index)
            self.header.moveSection(current_visual_index, logical_index)
        self.table.setColumnWidth(0, 115)
        self.table.setColumnWidth(1, 95)
        self.table.setColumnWidth(2, 65)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 30)
        self.table.setColumnWidth(5, 65)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 180)
        self.table.setColumnWidth(8, 40)

    def show_content_menu(self, pos):
        menu = RoundMenu(parent=self)
        select_all_action = Action("全选", self, triggered=lambda: print("全选"))

        submenu = RoundMenu("快速选择", self)
        select_video_action = Action("所有视频", self, triggered=lambda: print("所有视频轨道"))
        select_audio_action = Action("所有音频", self, triggered=lambda: print("所有音频轨道"))
        select_subtitle_action = Action("所有字幕", self, triggered=lambda: print("所有字幕轨道"))
        submenu.addActions([select_video_action, select_audio_action, select_subtitle_action])
        
        enabel_all_action = Action("全部启用", self, triggered=lambda: print("全部启用"))
        disable_all_action = Action("全部禁用", self, triggered=lambda: print("全部禁用"))
        menu.addAction(select_all_action)
        menu.addMenu(submenu)
        menu.addActions([enabel_all_action, disable_all_action])
        menu.exec(self.table.viewport().mapToGlobal(pos))


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

class DynamicComboList(QWidget):
    def __init__(self, parent=None, items:list=[], text:str=''):
        super().__init__(parent)
        self.vLayout = QVBoxLayout(self)
        self.vLayout.setContentsMargins(0, 0, 0, 0)

        self.options = items
        self.label_text = text
        self._add_initial_row()

    def _create_row(self, is_initial=False):
        row_widget = QWidget()
        hLayout = QHBoxLayout(row_widget)
        hLayout.setContentsMargins(0, 0, 0, 0)
        # hLayout.setSpacing(0)

        if self.label_text and is_initial:
            self.deflaut_label = BodyLabel(self.label_text, self)
            hLayout.addWidget(self.deflaut_label)
        if self.deflaut_label and not is_initial:
            label = BodyLabel('', self)
            label.setFixedWidth(self.deflaut_label.sizeHint().width())
            hLayout.addWidget(label)

        combo = ComboBox()
        combo.addItems(self.options)
        hLayout.addWidget(combo, 1)

        return row_widget, hLayout, combo

    def _add_initial_row(self):
        row_widget, hLayout, combo = self._create_row(is_initial=True)

        add_btn = ToolButton(FIF.ADD, self)

        hLayout.addWidget(add_btn)
        self.vLayout.addWidget(row_widget)

        add_btn.clicked.connect(self._add_new_row)

    
    def _add_new_row(self):
        row_widget, hLayout, combo = self._create_row()

        remove_btn = ToolButton(FIF.REMOVE, self)

        hLayout.addWidget(remove_btn)
        self.vLayout.addWidget(row_widget)

        remove_btn.clicked.connect(lambda: row_widget.deleteLater())


    def get_values(self):
        values = []
        for combo in self.findChildren(EditableComboBox):
            values.append(combo.currentText())
        return values
    
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
        self.go_hLayout1 = QHBoxLayout()
        self.go_hLayout2 = QHBoxLayout()
        self.go_hLayout3 = QHBoxLayout()
        self.go_hLayout4 = QHBoxLayout()
        self.go_hLayout5 = QHBoxLayout()

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

        self.flag_Items = ['', '默认轨道', '强制显示', '听觉障碍', '视觉障碍', '文字描述', '原始语言', '评论轨道']
        self.track_flag = DynamicComboList(items=self.flag_Items, text='轨道标记: ')

        self.compression_method = BodyLabel('压缩方法: ', self)
        self.compression_method_cb = ComboBox()
        self.compression_method_cb.addItems(['自动决定', '不做额外压缩', 'zlib'])

        self.track_label_lable = BodyLabel('标签: ', self)
        self.track_label_lable.setFixedWidth(self.track_enabled_label.sizeHint().width())
        self.track_label_lineEdit = LineEdit()

        
        self.go_hLayout1.addWidget(self.track_enabled_label)
        self.go_hLayout1.addWidget(self.track_enabled_cb, 1)

        self.go_hLayout2.addWidget(self.track_name_label)
        self.go_hLayout2.addWidget(self.track_name_lineEdit, 1)

        self.go_hLayout3.addWidget(self.track_language_label)
        self.go_hLayout3.addWidget(self.track_language_lineEdit, 1)

        self.go_hLayout4.addWidget(self.compression_method)
        self.go_hLayout4.addWidget(self.compression_method_cb, 1)

        self.go_hLayout5.addWidget(self.track_label_lable)
        self.go_hLayout5.addWidget(self.track_label_lineEdit, 1)

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
        self.frame_duration_items = ['', '24p', '25p', '30p', '48p', '50i', '50p', '60i', '60p', '24000/1001p', '30000/1001p', '48000/1001p', '60000/1001i', '60000/1001p']
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
        self.aspect_ratio_items = ['', '1/1', '4/3', '16/9', '21/9', '1.66', '1.85', '2.00', '2.21', '2.35', '2.40']
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
        self.general_options_group.addLayout(self.go_hLayout1)
        self.general_options_group.addLayout(self.go_hLayout2)
        self.general_options_group.addLayout(self.go_hLayout3)
        self.general_options_group.addWidget(self.track_flag)
        self.general_options_group.addLayout(self.go_hLayout4)
        self.general_options_group.addLayout(self.go_hLayout5)


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


