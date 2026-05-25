from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FfmpegSimpleOptionsWidget


class EncoderFFmpegVideoNode(AMENodeBase):
    NODE_NAME = 'ffmpeg 视频编码'
    DESCRIPTION = 'FFmpeg 视频编码器'
    CATEGORY = '编码'; CATEGORY_COLOR = C['Red']
    INPUTS = [('input', P['video'])]
    OUTPUTS = [('video', P['video'])]
    MENU_KEY = 'encoder_ffmpeg_video'

    def _setup_widgets(self):
        encoder_items = ['libx264', 'libx265', 'libsvtav1', 'libaom-av1', 'mpeg4', 'h264_nvenc', 'hevc_nvenc', 'qsv_h264', 'qsv_hevc']
        self.add_custom_widget(FfmpegSimpleOptionsWidget(self.view, 'Video_codec', encoder_items))

    def execute(self, inputs, temp_dir):
        src = (inputs.get('input') or [''])[0]
        if not src: return None
        import os, subprocess, shlex
        from app.services.tool_service import ToolService
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff: return None
        codec = self.property('codec','libx264')
        ext = '.h264' if 'x264' in codec else '.h265' if 'x265' in codec or 'hevc' in codec else '.mkv'
        dst = os.path.join(temp_dir, f'v_{self.id}{ext}')
        cmd = [ff,'-i',src,'-c:v',codec,'-an',dst,'-y']
        rc = self.property('rc_mode','crf')
        if rc=='crf': cmd.insert(-3,'-crf'); cmd.insert(-3,str(self.property('quality_val',23)))
        elif rc=='abr': cmd.insert(-3,'-b:v'); cmd.insert(-3,self.property('bitrate','5000k'))
        p = self.property('preset','')
        if p: cmd.insert(-3,'-preset'); cmd.insert(-3,p)
        cu = self.property('custom_options','')
        if cu:
            try: cmd[-3:-3] = shlex.split(cu)
            except ValueError: cmd[-3:-3] = cu.split()
        cf = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=14400)
        return {'video': [dst]} if os.path.isfile(dst) else None
