from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FfmpegSimpleOptionsWidget


class EncoderFFmpegAudioNode(AMENodeBase):
    NODE_NAME = 'ffmpeg 音频编码'
    DESCRIPTION = 'FFmpeg 音频编码器'
    CATEGORY = '编码'; CATEGORY_COLOR = C['编码']
    INPUTS = [('input', P['audio'])]
    OUTPUTS = [('audio', P['audio'])]
    MENU_KEY = 'encoder_ffmpeg_audio'

    def _setup_widgets(self):
        encoder_items = ['copy', 'pcm_s16le', 'pcm_s24le', 'pcm_f32le', 'flac', 'alac', 'aac', 'libmp3lame', 'libopus', 'libvorbis', 'ac3']
        self.add_custom_widget(FfmpegSimpleOptionsWidget(self.view, 'codec', encoder_items))

    def execute(self, inputs, temp_dir):
        src = (inputs.get('input') or [''])[0]
        if not src: return None
        import os, subprocess, shlex
        from app.services.tool_service import ToolService
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff: return None
        codec = self.property('codec','aac')
        em = {'aac':'.aac','libmp3lame':'.mp3','flac':'.flac','opus':'.opus','libvorbis':'.ogg','ac3':'.ac3'}
        dst = os.path.join(temp_dir, f'a_{self.id}{em.get(codec,".m4a")}')
        cmd = [ff,'-i',src,'-c:a',codec,'-vn',dst,'-y']
        rc = self.property('rc_mode','cbr')
        br = self.property('bitrate','')
        if rc in ('cbr','abr') and br: cmd.insert(-3,'-b:a'); cmd.insert(-3,br)
        elif rc=='quality': cmd.insert(-3,'-q:a'); cmd.insert(-3,str(self.property('quality_val',5)))
        cu = self.property('custom_options','')
        if cu:
            try: cmd[-3:-3] = shlex.split(cu)
            except ValueError: cmd[-3:-3] = cu.split()
        cf = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=14400)
        return {'audio': [dst]} if os.path.isfile(dst) else None
