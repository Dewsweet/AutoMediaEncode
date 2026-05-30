import subprocess, types
from pathlib import Path
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import MkvInlineConfigButton
from app.services.tool_service import ToolService
from app.common.logger import logger


class MuxerMkvmergeNode(AMENodeBase):
    NODE_NAME = '封装 (mkvmerge)'
    DESCRIPTION = 'mkvmerge 封装器，支持多轨道动态添加'
    CATEGORY = '封装'; CATEGORY_COLOR = C['Green']
    INPUTS = [('video', P['video']),
              ('audio', P['audio']),
              ('subtitle', P['subtitle']),
              ('chapter', P['chapter']),
              ('attachment', P['attachment'])]
    OUTPUTS = [('output', P['any'])]
    MENU_KEY = 'muxer_mkvmerge'

    def _setup_widgets(self):
        self._track_counters = {}
        for port_name, _ in self.INPUTS:
            if port_name not in ['chapter', 'attachment']:
                if port_name in ('video', 'audio', 'subtitle'):
                    self._track_counters[port_name] = 1
                w = MkvInlineConfigButton(self.view, f'track_setting_{port_name}', port_name, mode='base')
                w.addRequested.connect(lambda t=port_name: self._add_new_track(t))
                self.add_custom_widget(w)
        self.create_property('tracks', [], widget_type=HIDDEN, tab='')
        self._patch_mkvmerge_view_layout()

    def _add_new_track(self, track_type=None):
        if track_type not in ('video', 'audio', 'subtitle'):
            return
        cur = self._track_counters.get(track_type, 1)
        n = cur + 1
        self._track_counters[track_type] = n
        port_name = f'{track_type}_{n}'
        try:
            self.add_input(port_name, color=P.get(track_type, P['any']))
        except Exception:
            pass
        w = MkvInlineConfigButton(self.view, f'track_setting_{port_name}', port_name, mode='added')
        self.add_custom_widget(w)
        self.view.draw_node()

    def _patch_mkvmerge_view_layout(self):
        view = self.view

        def custom_calc_size(self_view):
            p_input_h = 0.0; p_input_w = 0.0
            for p, p_text in self_view._input_items.items():
                if p.isVisible():
                    p_input_h += p.boundingRect().height() + 1
                    p_input_w = max(p_input_w, p.boundingRect().width())
            p_output_h = 0.0; p_output_w = 0.0
            for port in self_view._output_items.keys():
                if port.isVisible():
                    p_output_h += port.boundingRect().height() + 1
                    p_output_w = max(p_output_w, port.boundingRect().width())
            port_height = max(p_input_h, p_output_h)
            widget_height = 0.0; widget_width = 0.0
            for w in self_view._widgets.values():
                if w.isVisible():
                    w_name = getattr(w, '_name', '')
                    if not w_name.startswith('track_setting_'):
                        widget_width = max(widget_width, w.boundingRect().width())
                        widget_height += w.boundingRect().height() + 4
            width = max(p_input_w + p_output_w + 30, widget_width + 10, 280)
            height = port_height + widget_height + 10
            return width, height

        def custom_align_widgets(self_view, v_offset):
            if not self_view._widgets: return
            rect = self_view.boundingRect()
            inp_h = sum(p.boundingRect().height() + 1 for p in self_view._input_items if p.isVisible())
            out_h = sum(p.boundingRect().height() + 1 for p in self_view._output_items if p.isVisible())
            port_height = max(inp_h, out_h)
            y = rect.y() + v_offset + port_height + 5
            for widget in self_view._widgets.values():
                if not widget.isVisible(): continue
                w_rect = widget.boundingRect()
                w_name = getattr(widget, '_name', '')
                if w_name.startswith('track_setting_'):
                    port_name = w_name.replace('track_setting_', '')
                    for p, p_text in self_view._input_items.items():
                        if p.name == port_name:
                            py = p.pos().y() - w_rect.height()/2 + p.boundingRect().height()/2
                            inline_x = rect.center().x() - w_rect.width()/2
                            widget.setPos(inline_x, py)
                            break
                else:
                    x = rect.center().x() - w_rect.width()/2
                    widget.setPos(x, y)
                    y += w_rect.height() + 2

        view._calc_size_horizontal = types.MethodType(custom_calc_size, view)
        view._align_widgets_horizontal = types.MethodType(custom_align_widgets, view)
        view.draw_node()

    def _resolve_out(self, inputs, temp_dir):
        has_v = any(v for pn, v in inputs.items() if v and pn.startswith('video'))
        has_a = any(v for pn, v in inputs.items() if v and pn.startswith('audio'))
        ext = '.mkv' if has_v else '.mka' if has_a else '.mks'
        return str(Path(temp_dir) / f'muxed_{self.id}{ext}')

    def execute(self, inputs, temp_dir):
        mk = ToolService.get_tool_path('mkvmerge')
        if not mk:
            logger.error('[MuxerMKV] 找不到 mkvmerge')
            return None
        out = self._resolve_out(inputs, temp_dir)
        cmd = [str(mk), '-o', out]
        has_input = False

        for pname, port in self.inputs().items():
            files = inputs.get(pname, [])
            if not files:
                continue

            settings = self.get_property(f'track_setting_{pname}') or {}
            lang = settings.get('track_language', '')
            name = settings.get('track_name', '')
            default = settings.get('default_track')
            custom = settings.get('track_custom', '')

            for f in files:
                f_path = str(Path(f))
                
                if pname.startswith('chapter'):
                    cmd.extend(['--chapters', f_path])
                    has_input = True
                    continue
                if pname.startswith('attachment'):
                    cmd.extend(['--attach-file', f_path])
                    has_input = True
                    continue

                if pname.startswith('video'):
                    cmd.extend(['-d', '0', '-A', '-S'])
                elif pname.startswith('audio'):
                    cmd.extend(['-a', '0', '-D', '-S'])
                elif pname.startswith('subtitle'):
                    cmd.extend(['-s', '0', '-D', '-A'])

                if lang:
                    cmd.extend(['--language', f'0:{lang}'])
                if name:
                    cmd.extend(['--track-name', f'0:{name}'])
                if default is True:
                    cmd.extend(['--default-track', '0:yes'])
                elif default is False:
                    cmd.extend(['--default-track', '0:no'])
                
                if custom:
                    cmd.extend(custom.split())

                cmd.append(f_path)
                has_input = True

        if not has_input:
            logger.error('[MuxerMKV] 没有任何轨道输入')
            return None

        logger.info(f'[MuxerMKV] 命令: {" ".join(cmd)}')
        r = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, timeout=14400)
        if r.returncode not in (0, 1):
            logger.error(f'[MuxerMKV] 失败: {r.stderr}')
            return None
        if not Path(out).is_file():
            return None
        logger.info(f'[MuxerMKV] 封装成功: {out}')
        return {'output': [out]}
