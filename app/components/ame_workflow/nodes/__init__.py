from .system.workspace_node import WorkspaceNode

from .system.input_file_node import InputFileNode
from .system.input_files_node import InputFilesNode

from .process.splitter_node import SplitterNode
from .process.vpy_loader_node import VPYLoaderNode
from .process.vspipe_node import VSPipeNode
from .process.ffmpeg_processor_node import FFmpegProcessorNode

from .encoder.x264_encoder_node import EncoderX264Node
from .encoder.x265_encoder_node import EncoderX265Node
from .encoder.svtav1_encoder_node import EncoderSvtAv1Node
from .encoder.ffmpeg_video_encoder_node import EncoderFFmpegVideoNode
from .encoder.ffmpeg_audio_encoder_node import EncoderFFmpegAudioNode
from .encoder.aac_encoder_node import EncoderAACNode
from .encoder.flac_encoder_node import EncoderFLACNode
from .encoder.opus_encoder_node import EncoderOPUSNode

from .muxer.mkvmerge_muxer_node import MuxerMkvmergeNode
from .muxer.ffmpeg_muxer_node import MuxerFFmpegNode

from .system.output_node import OutputNode


ALL_NODE_CLASSES = [
    WorkspaceNode,
    InputFileNode, InputFilesNode,
    SplitterNode,
    VPYLoaderNode, VSPipeNode, FFmpegProcessorNode,
    EncoderX264Node, EncoderX265Node, EncoderSvtAv1Node,
    EncoderFFmpegVideoNode, EncoderFFmpegAudioNode,
    EncoderAACNode, EncoderFLACNode, EncoderOPUSNode,
    MuxerMkvmergeNode, MuxerFFmpegNode,
    OutputNode,
]

MENU_KEY_MAP = {cls.MENU_KEY: cls for cls in ALL_NODE_CLASSES if cls.MENU_KEY}
TYPE_NAME_MAP = {f'ame.{cls.__name__}': cls for cls in ALL_NODE_CLASSES}
