from PySide6.QtCore import Qt, QPointF, Signal

from qfluentwidgets import RoundMenu, Action

from .nodes import MENU_KEY_MAP

NODE_PALETTE_STRUCTURE = [
    ('系统', [
        ('工作区', 'workspace'),
        ('输入文件', 'input_file'),
        ('多文件输入', 'input_multi'),
        ('输出文件', 'output'),
        ('纯文本', 'text'),
    ]),
    ('工具', [
        ('分离器', 'splitter'),
        ('VapourSynth', 'vs_compound'),
        ('ffmpeg处理器', 'ffmpeg_processor'),
        ('自定义文件名', 'custom_name'),
    ]),
    ('编码', [
        ('视频编码', [
            ('x264', 'encoder_x264'),
            ('x265', 'encoder_x265'),
            ('svtav1', 'encoder_svtav1'),
            ('ffmpeg(视频)', 'encoder_ffmpeg_video'),
        ]),
        ('音频编码', [
            ('flac', 'encoder_flac'),            
            ('aac', 'encoder_aac'),
            ('opus', 'encoder_opus'),
            ('ffmpeg(音频)', 'encoder_ffmpeg_audio'),
        ]),
    ]),
    ('封装', [
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
