from PySide6.QtCore import Qt, QPointF, Signal

from qfluentwidgets import RoundMenu, Action

from .ame_nodes import NODE_CLASSES

NODE_PALETTE_STRUCTURE = [
    ("基础", [
        ("工作区", "workspace"),
        None,
        ("输入文件", [
            ("输入视频", "input_video"),
            ("输入音频", "input_audio"),
            ("输入字幕", "input_subtitle"),
            ("输入附件", "input_attachment"),
            ("输入章节", "input_chapter"),
            ("输入文件", "input_file"),
        ]),
        ("输出文件", "output"),
    ]),
    ("处理", [
        ("分离器", "splitter"),
        ("vapoursynth", [
            ("vpy加载器", "vpy_loader"),
            ("vspipe", "vspipe"),
        ]),
        ("ffmpeg", "ffmpeg_processor"),
    ]),
    ("编码", [
        ("视频编码", [
            ("x264", "encoder_x264"),
            ("x265", "encoder_x265"),
            ("svtav1", "encoder_svtav1"),
            ("ffmpeg(视频)", "encoder_ffmpeg_video"),
        ]),
        ("音频编码", [
            ("aac", "encoder_aac"),
            ("flac", "encoder_flac"),
            ("opus", "encoder_opus"),
            ("ffmpeg(音频)", "encoder_ffmpeg_audio"),
        ]),
    ]),
    ("封装", [
        ("mkvmerge", "muxer_mkvmerge"),
        ("ffmpeg", "muxer_ffmpeg"),
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
        from .ame_nodes import registry_key_to_type_name
        self._build_tree(self, NODE_PALETTE_STRUCTURE, registry_key_to_type_name)

    def _build_tree(self, parent_menu, items, key_to_type):
        for item in items:
            if item is None:
                parent_menu.addSeparator()
                continue
            label, target = item
            if isinstance(target, list):
                submenu = RoundMenu(label, parent_menu)
                self._build_tree(submenu, target, key_to_type)
                parent_menu.addMenu(submenu)
            else:
                type_name = key_to_type(target)
                action = Action(label, parent_menu)
                action.triggered.connect(
                    (lambda k: lambda: self.node_selected.emit(k, self._scene_pos))(target)
                )
                parent_menu.addAction(action)

    def exec(self, *args, **kwargs):
        self._build()
        super().exec(*args, **kwargs)
