from .base_node import BaseNodeData


class WorkspaceNode(BaseNodeData):
    NODE_TYPE = "workspace"
    NODE_NAME = "工作区"
    CATEGORY = "系统"
    COLOR = "#607D8B"
    INPUT_PORTS = []
    OUTPUT_PORTS = [{"name": "path", "type": "any"}]
    DEFAULT_PARAMS = {"work_dir": ""}


class InputFileNode(BaseNodeData):
    NODE_TYPE = "input_file"
    NODE_NAME = "输入文件"
    CATEGORY = "输入"
    COLOR = "#4CAF50"
    INPUT_PORTS = [{"name": "path", "type": "any", "required": False}]
    OUTPUT_PORTS = [
        {"name": "video", "type": "video"},
        {"name": "audio", "type": "audio"},
        {"name": "subtitle", "type": "subtitle"},
        {"name": "chapter", "type": "chapter"},
    ]
    DEFAULT_PARAMS = {"file_path": "", "file_type": "auto"}


class SplitterNode(BaseNodeData):
    NODE_TYPE = "splitter"
    NODE_NAME = "分离器"
    CATEGORY = "处理"
    COLOR = "#FF9800"
    INPUT_PORTS = [{"name": "input", "type": "any", "required": True}]
    OUTPUT_PORTS = [
        {"name": "video", "type": "video"},
        {"name": "audio", "type": "audio"},
        {"name": "subtitle", "type": "subtitle"},
        {"name": "chapter", "type": "chapter"},
    ]
    DEFAULT_PARAMS = {"tool": "ffmpeg", "mode": "extract"}


class EncoderX264Node(BaseNodeData):
    NODE_TYPE = "encoder_x264"
    NODE_NAME = "x264 编码"
    CATEGORY = "编码"
    COLOR = "#F44336"
    INPUT_PORTS = [{"name": "input", "type": "video", "required": True}]
    OUTPUT_PORTS = [{"name": "video", "type": "video"}]
    DEFAULT_PARAMS = {"preset": "", "custom_cli": ""}


class EncoderX265Node(BaseNodeData):
    NODE_TYPE = "encoder_x265"
    NODE_NAME = "x265 编码"
    CATEGORY = "编码"
    COLOR = "#F44336"
    INPUT_PORTS = [{"name": "input", "type": "video", "required": True}]
    OUTPUT_PORTS = [{"name": "video", "type": "video"}]
    DEFAULT_PARAMS = {"preset": "", "custom_cli": ""}


class EncoderSvtAv1Node(BaseNodeData):
    NODE_TYPE = "encoder_svtav1"
    NODE_NAME = "SVT-AV1 编码"
    CATEGORY = "编码"
    COLOR = "#F44336"
    INPUT_PORTS = [{"name": "input", "type": "video", "required": True}]
    OUTPUT_PORTS = [{"name": "video", "type": "video"}]
    DEFAULT_PARAMS = {"preset": "", "custom_cli": ""}


class EncoderFFmpegVideoNode(BaseNodeData):
    NODE_TYPE = "encoder_ffmpeg_video"
    NODE_NAME = "FFmpeg 视频编码"
    CATEGORY = "编码"
    COLOR = "#F44336"
    INPUT_PORTS = [{"name": "input", "type": "video", "required": True}]
    OUTPUT_PORTS = [{"name": "video", "type": "video"}]
    DEFAULT_PARAMS = {
        "codec": "libx264",
        "rc_mode": "crf",
        "quality_val": 23,
        "bitrate": "5000k",
        "preset": "medium",
        "profile": "",
        "level": "",
        "tune": "",
        "custom_options": "",
    }


class EncoderFFmpegAudioNode(BaseNodeData):
    NODE_TYPE = "encoder_ffmpeg_audio"
    NODE_NAME = "FFmpeg 音频编码"
    CATEGORY = "编码"
    COLOR = "#F44336"
    INPUT_PORTS = [{"name": "input", "type": "audio", "required": True}]
    OUTPUT_PORTS = [{"name": "audio", "type": "audio"}]
    DEFAULT_PARAMS = {
        "codec": "aac",
        "rc_mode": "cbr",
        "bitrate": "192k",
        "quality_val": 5,
        "custom_options": "",
    }


class MuxerMkvmergeNode(BaseNodeData):
    NODE_TYPE = "muxer_mkvmerge"
    NODE_NAME = "封装 MKV"
    CATEGORY = "封装"
    COLOR = "#9C27B0"
    INPUT_PORTS = [
        {"name": "video", "type": "video", "required": False},
        {"name": "audio", "type": "audio", "required": False},
        {"name": "subtitle", "type": "subtitle", "required": False},
        {"name": "chapter", "type": "chapter", "required": False},
        {"name": "attachment", "type": "attachment", "required": False},
    ]
    OUTPUT_PORTS = [{"name": "output", "type": "any"}]
    DEFAULT_PARAMS = {"container": "mkv", "tracks": []}


class MuxerFFmpegNode(BaseNodeData):
    NODE_TYPE = "muxer_ffmpeg"
    NODE_NAME = "封装 MP4/MOV"
    CATEGORY = "封装"
    COLOR = "#9C27B0"
    INPUT_PORTS = [
        {"name": "video", "type": "video", "required": False},
        {"name": "audio", "type": "audio", "required": False},
    ]
    OUTPUT_PORTS = [{"name": "output", "type": "any"}]
    DEFAULT_PARAMS = {"container": "mp4", "faststart": False}


class OutputNode(BaseNodeData):
    NODE_TYPE = "output"
    NODE_NAME = "输出"
    CATEGORY = "输出"
    COLOR = "#2196F3"
    INPUT_PORTS = [{"name": "input", "type": "any", "required": True}]
    OUTPUT_PORTS = []
    DEFAULT_PARAMS = {"output_path": "", "filename_template": "{input_name}_encoded"}


NODE_REGISTRY = {
    "workspace": WorkspaceNode,
    "input_file": InputFileNode,
    "splitter": SplitterNode,
    "encoder_x264": EncoderX264Node,
    "encoder_x265": EncoderX265Node,
    "encoder_svtav1": EncoderSvtAv1Node,
    "encoder_ffmpeg_video": EncoderFFmpegVideoNode,
    "encoder_ffmpeg_audio": EncoderFFmpegAudioNode,
    "muxer_mkvmerge": MuxerMkvmergeNode,
    "muxer_ffmpeg": MuxerFFmpegNode,
    "output": OutputNode,
}


def get_node_meta(node_type: str) -> dict:
    cls = NODE_REGISTRY.get(node_type)
    if cls:
        return cls.get_meta()
    return None


def get_all_node_types():
    return list(NODE_REGISTRY.keys())


def get_nodes_by_category():
    result = {}
    for ntype, cls in NODE_REGISTRY.items():
        cat = cls.CATEGORY
        if cat not in result:
            result[cat] = []
        result[cat].append(cls.get_meta())
    return result


def create_node_data(node_type: str, node_id: str = "", x: float = 0, y: float = 0) -> dict:
    cls = NODE_REGISTRY.get(node_type)
    if cls:
        inst = cls(node_id=node_id, x=x, y=y)
        return inst.to_dict()
    return None
