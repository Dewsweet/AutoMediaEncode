from NodeGraphQt import BaseNode
from NodeGraphQt.constants import NodePropWidgetEnum as NPE

from . import PORT_COLORS, CATEGORY_COLORS

HIDDEN = NPE.HIDDEN.value


def _hex2rgb(hex_str: str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

C = {k: _hex2rgb(v) for k, v in CATEGORY_COLORS.items()}
P = {k: tuple(v) for k, v in PORT_COLORS.items()}


class WorkspaceNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '工作区'
    def __init__(self):
        super().__init__()
        self.set_color(*C['系统'])
        self.add_output('path', color=P['any'])
        self.create_property('work_dir', '', widget_type=HIDDEN, tab='')

class InputFileNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '输入文件'
    def __init__(self):
        super().__init__()
        self.set_color(*C['输入'])
        self.add_output('video', color=P['video'])
        self.add_output('audio', color=P['audio'])
        self.add_output('subtitle', color=P['subtitle'])
        self.create_property('file_path', '', widget_type=HIDDEN, tab='')
        self.create_property('file_type', 'auto', widget_type=HIDDEN, tab='')

class InputVideoNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '输入视频'
    def __init__(self):
        super().__init__()
        self.set_color(*C['输入'])
        self.add_output('video', color=P['video'])
        self.create_property('file_path', '', widget_type=HIDDEN, tab='')
        self.create_property('file_type', 'video', widget_type=HIDDEN, tab='')

class InputAudioNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '输入音频'
    def __init__(self):
        super().__init__()
        self.set_color(*C['输入'])
        self.add_output('audio', color=P['audio'])
        self.create_property('file_path', '', widget_type=HIDDEN, tab='')
        self.create_property('file_type', 'audio', widget_type=HIDDEN, tab='')

class InputSubtitleNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '输入字幕'
    def __init__(self):
        super().__init__()
        self.set_color(*C['输入'])
        self.add_output('subtitle', color=P['subtitle'])
        self.create_property('file_path', '', widget_type=HIDDEN, tab='')
        self.create_property('file_type', 'subtitle', widget_type=HIDDEN, tab='')

class InputAttachmentNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '输入附件'
    def __init__(self):
        super().__init__()
        self.set_color(*C['输入'])
        self.add_output('attachment', color=P['attachment'])
        self.create_property('file_path', '', widget_type=HIDDEN, tab='')
        self.create_property('file_type', 'attachment', widget_type=HIDDEN, tab='')

class InputChapterNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '输入章节'
    def __init__(self):
        super().__init__()
        self.set_color(*C['输入'])
        self.add_output('chapter', color=P['chapter'])
        self.create_property('file_path', '', widget_type=HIDDEN, tab='')
        self.create_property('file_type', 'chapter', widget_type=HIDDEN, tab='')

class SplitterNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '分离器'
    def __init__(self):
        super().__init__()
        self.set_color(*C['处理'])
        self.add_input('input', color=P['any'])
        self.add_output('video', color=P['video'])
        self.add_output('audio', color=P['audio'])
        self.add_output('subtitle', color=P['subtitle'])
        self.create_property('tool', 'ffmpeg', widget_type=HIDDEN, tab='')
        self.create_property('mode', 'extract', widget_type=HIDDEN, tab='')

class VPYLoaderNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'vpy加载器'
    def __init__(self):
        super().__init__()
        self.set_color(*C['处理'])
        self.add_input('input', color=P['video'])
        self.add_output('script', color=P['script'])
        self.create_property('vpy_path', '', widget_type=HIDDEN, tab='')

class VSPipeNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'vspipe'
    def __init__(self):
        super().__init__()
        self.set_color(*C['处理'])
        self.add_input('script', color=P['script'])
        self.add_output('video', color=P['video'])

class FFmpegProcessorNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'ffmpeg'
    def __init__(self):
        super().__init__()
        self.set_color(*C['处理'])
        self.add_input('input', color=P['any'])
        self.add_output('output', color=P['any'])
        self.create_property('cli_args', '', widget_type=HIDDEN, tab='')

class EncoderX264Node(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'x264 编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['video'])
        self.add_output('video', color=P['video'])
        self.create_property('use_preset', True, widget_type=HIDDEN, tab='')
        self.create_property('preset', '', widget_type=HIDDEN, tab='')
        self.create_property('custom_cli', '', widget_type=HIDDEN, tab='')

class EncoderX265Node(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'x265 编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['video'])
        self.add_output('video', color=P['video'])
        self.create_property('use_preset', True, widget_type=HIDDEN, tab='')
        self.create_property('preset', '', widget_type=HIDDEN, tab='')
        self.create_property('custom_cli', '', widget_type=HIDDEN, tab='')

class EncoderSvtAv1Node(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'SVT-AV1 编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['video'])
        self.add_output('video', color=P['video'])
        self.create_property('use_preset', True, widget_type=HIDDEN, tab='')
        self.create_property('preset', '', widget_type=HIDDEN, tab='')
        self.create_property('custom_cli', '', widget_type=HIDDEN, tab='')

class EncoderFFmpegVideoNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'ffmpeg 视频编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['video'])
        self.add_output('video', color=P['video'])
        self.create_property('codec', 'libx264', widget_type=HIDDEN, tab='')
        self.create_property('rc_mode', 'crf', widget_type=HIDDEN, tab='')
        self.create_property('quality_val', 23, widget_type=HIDDEN, tab='')
        self.create_property('bitrate', '5000k', widget_type=HIDDEN, tab='')
        self.create_property('preset', 'medium', widget_type=HIDDEN, tab='')
        self.create_property('custom_options', '', widget_type=HIDDEN, tab='')

class EncoderFFmpegAudioNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'ffmpeg 音频编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['audio'])
        self.add_output('audio', color=P['audio'])
        self.create_property('codec', 'aac', widget_type=HIDDEN, tab='')
        self.create_property('rc_mode', 'cbr', widget_type=HIDDEN, tab='')
        self.create_property('bitrate', '192k', widget_type=HIDDEN, tab='')
        self.create_property('quality_val', 5, widget_type=HIDDEN, tab='')
        self.create_property('custom_options', '', widget_type=HIDDEN, tab='')

class EncoderAACNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'AAC 编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['audio'])
        self.add_output('audio', color=P['audio'])
        self.create_property('codec', 'aac', widget_type=HIDDEN, tab='')
        self.create_property('rc_mode', 'cbr', widget_type=HIDDEN, tab='')
        self.create_property('bitrate', '192k', widget_type=HIDDEN, tab='')
        self.create_property('quality_val', 5, widget_type=HIDDEN, tab='')
        self.create_property('custom_options', '', widget_type=HIDDEN, tab='')

class EncoderFlacNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'FLAC 编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['audio'])
        self.add_output('audio', color=P['audio'])
        self.create_property('codec', 'flac', widget_type=HIDDEN, tab='')
        self.create_property('rc_mode', 'quality', widget_type=HIDDEN, tab='')
        self.create_property('bitrate', '', widget_type=HIDDEN, tab='')
        self.create_property('quality_val', 8, widget_type=HIDDEN, tab='')
        self.create_property('custom_options', '', widget_type=HIDDEN, tab='')

class EncoderOpusNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = 'Opus 编码'
    def __init__(self):
        super().__init__()
        self.set_color(*C['编码'])
        self.add_input('input', color=P['audio'])
        self.add_output('audio', color=P['audio'])
        self.create_property('codec', 'opus', widget_type=HIDDEN, tab='')
        self.create_property('rc_mode', 'cbr', widget_type=HIDDEN, tab='')
        self.create_property('bitrate', '128k', widget_type=HIDDEN, tab='')
        self.create_property('quality_val', 5, widget_type=HIDDEN, tab='')
        self.create_property('custom_options', '', widget_type=HIDDEN, tab='')

class MuxerMkvmergeNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '封装 MKV'
    def __init__(self):
        super().__init__()
        self.set_color(*C['封装'])
        self.add_input('video', color=P['video'])
        self.add_input('audio', color=P['audio'])
        self.add_input('subtitle', color=P['subtitle'])
        self.add_input('attachment', color=P['attachment'])
        self.add_output('output', color=P['any'])
        self.create_property('tracks', [], widget_type=HIDDEN, tab='')

class MuxerFFmpegNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '封装 MP4/MOV'
    def __init__(self):
        super().__init__()
        self.set_color(*C['封装'])
        self.add_input('video', color=P['video'])
        self.add_input('audio', color=P['audio'])
        self.add_output('output', color=P['any'])
        self.create_property('container', 'mp4', widget_type=HIDDEN, tab='')

class OutputNode(BaseNode):
    __identifier__ = 'ame'
    NODE_NAME = '输出文件'
    def __init__(self):
        super().__init__()
        self.set_color(*C['输出'])
        self.add_input('input', color=P['any'])
        self.create_property('output_path', '', widget_type=HIDDEN, tab='')


NODE_CLASSES = [
    WorkspaceNode,
    InputFileNode, InputVideoNode, InputAudioNode, InputSubtitleNode,
    InputAttachmentNode, InputChapterNode,
    SplitterNode,
    VPYLoaderNode, VSPipeNode, FFmpegProcessorNode,
    EncoderX264Node, EncoderX265Node, EncoderSvtAv1Node,
    EncoderFFmpegVideoNode, EncoderFFmpegAudioNode,
    EncoderAACNode, EncoderFlacNode, EncoderOpusNode,
    MuxerMkvmergeNode, MuxerFFmpegNode,
    OutputNode,
]


NODE_TYPE_MAP = {cls.__name__: cls for cls in NODE_CLASSES}


def create_node_widget(node):
    """Return the appropriate NodeBodyWidget for a BaseNode."""
    from .node_body_widgets import (
        WorkspaceBody, InputFileBody, VPYBody, VSPipeBody,
        EncoderCLIBody, EncoderFFmpegVideoBody, EncoderFFmpegAudioBody,
        FFmpegProcessorBody, MuxerMkvmergeBody, MuxerFFmpegBody, OutputBody
    )
    type_name = node.__class__.__name__
    if type_name == 'WorkspaceNode':
        return WorkspaceBody()
    elif type_name in ('InputFileNode', 'InputVideoNode', 'InputAudioNode',
                        'InputSubtitleNode', 'InputAttachmentNode', 'InputChapterNode'):
        return InputFileBody()
    elif type_name == 'SplitterNode':
        return None
    elif type_name == 'VPYLoaderNode':
        return VPYBody()
    elif type_name == 'VSPipeNode':
        return VSPipeBody()
    elif type_name in ('EncoderX264Node', 'EncoderX265Node', 'EncoderSvtAv1Node'):
        et = type_name.replace('Encoder', '').replace('Node', '').lower()
        return EncoderCLIBody(et)
    elif type_name == 'EncoderFFmpegVideoNode':
        return EncoderFFmpegVideoBody()
    elif type_name in ('EncoderFFmpegAudioNode', 'EncoderAACNode', 'EncoderFlacNode', 'EncoderOpusNode'):
        codec = 'aac'
        if type_name == 'EncoderFlacNode': codec = 'flac'
        elif type_name == 'EncoderOpusNode': codec = 'opus'
        return EncoderFFmpegAudioBody(codec)
    elif type_name == 'FFmpegProcessorNode':
        return FFmpegProcessorBody()
    elif type_name == 'MuxerMkvmergeNode':
        return MuxerMkvmergeBody()
    elif type_name == 'MuxerFFmpegNode':
        return MuxerFFmpegBody()
    elif type_name == 'OutputNode':
        return OutputBody()
    return None


def node_type_name_to_registry_key(type_name: str) -> str:
    """Convert NodeGraphQt type_ to our registry key."""
    m = {
        'ame.InputFileNode': 'input_file',
        'ame.InputVideoNode': 'input_video',
        'ame.InputAudioNode': 'input_audio',
        'ame.InputSubtitleNode': 'input_subtitle',
        'ame.InputAttachmentNode': 'input_attachment',
        'ame.InputChapterNode': 'input_chapter',
        'ame.WorkspaceNode': 'workspace',
        'ame.SplitterNode': 'splitter',
        'ame.VPYLoaderNode': 'vpy_loader',
        'ame.VSPipeNode': 'vspipe',
        'ame.FFmpegProcessorNode': 'ffmpeg_processor',
        'ame.EncoderX264Node': 'encoder_x264',
        'ame.EncoderX265Node': 'encoder_x265',
        'ame.EncoderSvtAv1Node': 'encoder_svtav1',
        'ame.EncoderFFmpegVideoNode': 'encoder_ffmpeg_video',
        'ame.EncoderFFmpegAudioNode': 'encoder_ffmpeg_audio',
        'ame.EncoderAACNode': 'encoder_aac',
        'ame.EncoderFlacNode': 'encoder_flac',
        'ame.EncoderOpusNode': 'encoder_opus',
        'ame.MuxerMkvmergeNode': 'muxer_mkvmerge',
        'ame.MuxerFFmpegNode': 'muxer_ffmpeg',
        'ame.OutputNode': 'output',
    }
    return m.get(type_name, type_name)


def registry_key_to_type_name(key: str) -> str:
    """Reverse map registry key to NodeGraphQt type_."""
    for type_name, reg_key in {
        'ame.InputFileNode': 'input_file',
        'ame.InputVideoNode': 'input_video',
        'ame.InputAudioNode': 'input_audio',
        'ame.InputSubtitleNode': 'input_subtitle',
        'ame.InputAttachmentNode': 'input_attachment',
        'ame.InputChapterNode': 'input_chapter',
        'ame.WorkspaceNode': 'workspace',
        'ame.SplitterNode': 'splitter',
        'ame.VPYLoaderNode': 'vpy_loader',
        'ame.VSPipeNode': 'vspipe',
        'ame.FFmpegProcessorNode': 'ffmpeg_processor',
        'ame.EncoderX264Node': 'encoder_x264',
        'ame.EncoderX265Node': 'encoder_x265',
        'ame.EncoderSvtAv1Node': 'encoder_svtav1',
        'ame.EncoderFFmpegVideoNode': 'encoder_ffmpeg_video',
        'ame.EncoderFFmpegAudioNode': 'encoder_ffmpeg_audio',
        'ame.EncoderAACNode': 'encoder_aac',
        'ame.EncoderFlacNode': 'encoder_flac',
        'ame.EncoderOpusNode': 'encoder_opus',
        'ame.MuxerMkvmergeNode': 'muxer_mkvmerge',
        'ame.MuxerFFmpegNode': 'muxer_ffmpeg',
        'ame.OutputNode': 'output',
    }.items():
        if reg_key == key:
            return type_name
    return key
