from .._base import AMENodeBase, C, P, HIDDEN


class MuxerFFmpegNode(AMENodeBase):
    NODE_NAME = '封装 MP4/MOV'
    DESCRIPTION = 'FFmpeg 封装器'
    CATEGORY = '封装'; CATEGORY_COLOR = C['封装']
    INPUTS = [('video', P['video']), ('audio', P['audio'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'muxer_ffmpeg'

    def _setup_widgets(self):
        self.add_combo_menu('container', '容器', items=['mp4','mov'])

    def execute(self, inputs, temp_dir):
        import os, subprocess, uuid
        from app.services.tool_service import ToolService
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff: return None
        vf = inputs.get('video') or []
        af = inputs.get('audio') or []
        cont = self.property('container','mp4')
        out = os.path.join(temp_dir, f'muxed_{self.id}.{cont}')
        cmd = [ff]
        for s in vf: cmd.extend(['-i',s])
        for s in af: cmd.extend(['-i',s])
        si = 0
        for _ in vf: cmd.extend(['-map',str(si)]); si+=1
        for _ in af: cmd.extend(['-map',str(si)]); si+=1
        cmd.extend(['-c','copy',out,'-y'])
        cf = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=14400)
        return {'output': [out]} if os.path.isfile(out) else None
