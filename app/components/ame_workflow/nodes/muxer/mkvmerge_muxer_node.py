from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import mkvmergeWidget


class MuxerMkvmergeNode(AMENodeBase):
    NODE_NAME = '封装 MKV'
    DESCRIPTION = 'mkvmerge 封装器'
    CATEGORY = '封装'; CATEGORY_COLOR = C['封装']
    INPUTS = [('video', P['video']), 
              ('audio', P['audio']),
              ('subtitle', P['subtitle']), 
              ('chapter', P['chapter']),
              ('attachment', P['attachment'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'muxer_mkvmerge'

    def _setup_widgets(self):
        self.add_custom_widget(mkvmergeWidget(self.view, 'mkvmerge设置'))
        self.create_property('tracks', [], widget_type=HIDDEN, tab='')

    def execute(self, inputs, temp_dir):
        import os, subprocess, uuid
        from app.services.tool_service import ToolService
        mk = ToolService.get_tool_path('mkvmerge')
        if not mk: return None
        vf = inputs.get('video') or []
        af = inputs.get('audio') or []
        sf = inputs.get('subtitle') or []
        atf = inputs.get('attachment') or []
        out = self._resolve_out(temp_dir)
        cmd = [mk, '-o', out]
        for f in vf: cmd.extend(['-d','0',f])
        for f in af: cmd.extend(['-a','0',f])
        for f in sf: cmd.extend(['-s','0',f])
        for f in atf: cmd.extend(['--attach-file',f])
        if not vf and not af and not sf:
            for f in vf+af+sf: cmd.append(f)
        cf = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=14400)
        return {'output': [out]} if os.path.isfile(out) else None

    def _resolve_out(self, temp_dir): 
        pass
