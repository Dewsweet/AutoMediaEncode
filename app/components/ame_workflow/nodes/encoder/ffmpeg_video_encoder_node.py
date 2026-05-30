from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FfmpegSimpleOptionsWidget
from .._helpers import _do_ffmpeg_video

class EncoderFFmpegVideoNode(AMENodeBase):
    NODE_NAME = 'ffmpeg 视频编码'
    DESCRIPTION = 'FFmpeg 视频编码器'
    CATEGORY = '编码'; CATEGORY_COLOR = C['Red']
    INPUTS = [('input', P['video'])]
    OUTPUTS = [('video', P['video'])]
    MENU_KEY = 'encoder_ffmpeg_video'

    def _setup_widgets(self):
        encoder_items = ['libx264', 'libx265', 'libsvtav1', 'mpeg4', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'qsv_h264', 'qsv_hevc', 'h264_amf', 'hevc_amf']
        self.add_custom_widget(FfmpegSimpleOptionsWidget(self.view, 'Video_codec', encoder_items))

    def execute(self, inputs, temp_dir):
        return _do_ffmpeg_video(self, inputs, temp_dir)
