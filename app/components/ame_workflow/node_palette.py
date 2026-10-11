from PySide6.QtCore import Qt, QPointF, Signal, QCoreApplication, QT_TRANSLATE_NOOP

from qfluentwidgets import RoundMenu, Action

from .nodes import MENU_KEY_MAP

NODE_PALETTE_STRUCTURE = [
    (QT_TRANSLATE_NOOP("AMENodePalette", '系统'), [
        (QT_TRANSLATE_NOOP("AMENodePalette", '工作区'), 'workspace'),
        (QT_TRANSLATE_NOOP("AMENodePalette", '纯文本'), 'text'),
        (QT_TRANSLATE_NOOP("AMENodePalette", '自定义文件名'), 'custom_name'),
    ]),
    (QT_TRANSLATE_NOOP("AMENodePalette", '工具'), [
        (QT_TRANSLATE_NOOP("AMENodePalette", '分离器'), 'splitter'),
        ('VapourSynth', 'vs_compound'),
        (QT_TRANSLATE_NOOP("AMENodePalette", 'ffmpeg处理器'), 'ffmpeg_processor'),
    ]),
    (QT_TRANSLATE_NOOP("AMENodePalette", '输入/输出'), [
        (QT_TRANSLATE_NOOP("AMENodePalette", '普通输入'), 'input_file'),
        (QT_TRANSLATE_NOOP("AMENodePalette", '多文件输入'), 'input_multi'),
        (QT_TRANSLATE_NOOP("AMENodePalette", '视频规范化输入'), 'input_video_normalizer'),
        (QT_TRANSLATE_NOOP("AMENodePalette", 'BD 规范化输入'), 'input_bd_normalizer'),
        (QT_TRANSLATE_NOOP("AMENodePalette", '普通输出'), 'output'),
    ]),
    (QT_TRANSLATE_NOOP("AMENodePalette", '视频编码'), [
        ('x264', 'encoder_x264'),
        ('x265', 'encoder_x265'),
        ('svtav1', 'encoder_svtav1'),
        (QT_TRANSLATE_NOOP("AMENodePalette", 'ffmpeg (视频)'), 'encoder_ffmpeg_video'),
        ]),
    (QT_TRANSLATE_NOOP("AMENodePalette", '音频编码'), [
        ('flac', 'encoder_flac'),            
        ('aac', 'encoder_aac'),
        ('opus', 'encoder_opus'),
        (QT_TRANSLATE_NOOP("AMENodePalette", 'ffmpeg (音频)'), 'encoder_ffmpeg_audio'),
        ]),
    (QT_TRANSLATE_NOOP("AMENodePalette", '封装'), [
        ('mkvmerge', 'muxer_mkvmerge'),
        ('ffmpeg', 'muxer_ffmpeg'),
    ]),
]


class NodePaletteMenu(RoundMenu):
    node_selected = Signal(str, QPointF)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._scene_pos = QPointF(0, 0)

    def set_scene_pos(self, pos: QPointF):
        self._scene_pos = pos

    def _build(self):
        self.clear()
        self._build_tree(self, NODE_PALETTE_STRUCTURE)

    def _build_tree(self, parent_menu, items):
        for item in items:
            if item is None:
                parent_menu.addSeparator()
                continue
            label, target = item
            label = QCoreApplication.translate("AMENodePalette", label)
            if isinstance(target, list):
                submenu = RoundMenu(label, parent_menu)
                self._build_tree(submenu, target)
                parent_menu.addMenu(submenu)
            else:
                if target in MENU_KEY_MAP:
                    action = Action(label, parent_menu)
                    action.triggered.connect(
                        (lambda k: lambda: self.node_selected.emit(k, self._scene_pos))(target)
                    )
                    parent_menu.addAction(action)

    def exec(self, *args, **kwargs):
        self._build()
        super().exec(*args, **kwargs)
