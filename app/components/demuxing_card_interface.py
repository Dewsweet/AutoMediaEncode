from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidgetItem

from qfluentwidgets import CardWidget, HeaderCardWidget, TreeWidget, RoundMenu, Action, BodyLabel, ComboBox, CheckBox, LineEdit, PushButton, PrimaryPushButton, FluentIcon as FIF

class InputFilesCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('输入文件')

        self.mianBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mianBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.inputFilesTree = TreeWidget()
        self.inputFilesTree.setHeaderHidden(True)
        self.inputFilesTree.setContextMenuPolicy(Qt.CustomContextMenu)

        self.mainLayout.addWidget(self.inputFilesTree)
        self.viewLayout.addWidget(self.mianBox)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)

        self.testItem()
        self._connect_signals()

    def testItem(self):
        item1 = QTreeWidgetItem(['占位文件1.mp4'])
        item2 = QTreeWidgetItem(['占位文件2.mkv'])

        item11 = [QTreeWidgetItem(['轨道 1 Video: hevc (Main 10), 1920x1080, 23.98 fps(default) ']),
            QTreeWidgetItem(['轨道 2 Audio: aac (LC), 2ch, 44100Hz '])]

        for i in item11:
            i.setCheckState(0, Qt.Unchecked)
            item1.addChild(i)

        item22 = [
            QTreeWidgetItem(['轨道 1 Video: h264 (High), 1280x720, 30 fps ']),
            QTreeWidgetItem(['轨道 2 Audio: ac3 (AC-3), 6ch, 48000Hz ']),
            QTreeWidgetItem(['轨道 3 Subtitle: ass ']),
            QTreeWidgetItem(['附件 1 font: xxxxxxxx.ttf']),
            QTreeWidgetItem(['附件 2 ……']),
            QTreeWidgetItem(['章节 n 个条目'])
        ]

        for i in item22:
            i.setCheckState(0, Qt.Unchecked)
            item2.addChild(i)
            
        self.inputFilesTree.addTopLevelItem(item1)
        self.inputFilesTree.addTopLevelItem(item2)
        self.inputFilesTree.expandAll()

    def _connect_signals(self):
        self.inputFilesTree.customContextMenuRequested.connect(self.show_context_mune)

    def updata_fiels(self, files, track_info):
        pass

    def show_context_mune(self, pos):
        mune = RoundMenu(parent=self)

        select_all = Action('全选', triggered=self.select_all_items)

        select_submune = RoundMenu("选择", self)
        select_video = Action('选择视频', triggered=self.select_video)
        select_audio = Action('选择音频', triggered=self.select_audio)
        select_sub = Action('选择字幕', triggered=self.select_sub)
        select_att = Action('选择附件', triggered=self.select_att)
        select_mune = Action('选择菜单', triggered=self.select_mune)

        select_submune.addActions([select_video, select_audio, select_sub, select_att, select_mune])

        mune.addAction(select_all)
        mune.addMenu(select_submune)
        mune.exec(self.inputFilesTree.mapToGlobal(pos))
        
    def select_all_items():
        pass
    def select_video():
        pass
    def select_audio():
        pass
    def select_sub():
        pass
    def select_att():
        pass
    def select_mune():
        pass

class MuxingOptionCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('其他选项')

        self.mainBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.contextHLayout1 = QHBoxLayout()
        # self.contextHLayout2 = QHBoxLayout()
        # self.contextHLayout3 = QHBoxLayout()

        self.chapter_suffix_label = BodyLabel('章节后缀: ')
        self.chapter_suffix_cb = ComboBox()
        self.chapter_suffix_cb.addItems(['XML', 'OGM', 'CUE', 'TXT'])

        self.sub_departition_ckeackbox = CheckBox('字幕去子集化')

        self.turehd_decore_ckeackbox = CheckBox('TrueHD 去核心')

        self.contextHLayout1.addWidget(self.chapter_suffix_label)
        self.contextHLayout1.addWidget(self.chapter_suffix_cb)
        self.contextHLayout1.addStretch(1)

        self.mainLayout.addLayout(self.contextHLayout1)
        self.mainLayout.addWidget(self.sub_departition_ckeackbox)
        self.mainLayout.addWidget(self.turehd_decore_ckeackbox)
        self.mainLayout.addStretch(1)

        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(20, 10, 10, 10)

class OutputCard(HeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle('输出设置')

        self.mainBox = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainBox)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.OutputPathLayout = QHBoxLayout()

        self.output_path_label = BodyLabel('输出路径: ')
        self.output_path_lineEdit = LineEdit()

        self.using_source_dir_checkbox = CheckBox('源目录')
        self.output_path_view_button = PrimaryPushButton('浏览')

        self.OutputPathLayout.addWidget(self.output_path_label)
        self.OutputPathLayout.addWidget(self.output_path_lineEdit)
        self.OutputPathLayout.addWidget(self.using_source_dir_checkbox)
        self.OutputPathLayout.addWidget(self.output_path_view_button)


        self.mainLayout.addLayout(self.OutputPathLayout)

        self.viewLayout.addWidget(self.mainBox)
        self.viewLayout.setContentsMargins(10, 10, 10, 10)


        







