import types
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import MkvInlineConfigButton


class MuxerMkvmergeNode(AMENodeBase):
    NODE_NAME = '封装 (mkvmerge)'
    DESCRIPTION = 'mkvmerge 封装器'
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
                # 初始计数为 1(已有的基础端口)
                if port_name in ('video', 'audio', 'subtitle'):
                    self._track_counters[port_name] = 1
                w = MkvInlineConfigButton(self.view, f'track_setting_{port_name}', port_name, mode='base')
                w.addRequested.connect(lambda t=port_name: self._add_new_track(t))
                self.add_custom_widget(w)

        self.create_property('tracks', [], widget_type=HIDDEN, tab='')

        # 调整布局以适应内嵌设置按钮
        self._patch_mkvmerge_view_layout()

    def _add_new_track(self, track_type=None):
        if track_type not in ("video", "audio", "subtitle"):
            return
        # 根据 track_type 生成新的端口名，确保唯一性
        cur = self._track_counters.get(track_type, 1)
        n = cur + 1
        self._track_counters[track_type] = n
        port_name = f'{track_type}_track{n}'
        try:
            self.add_input(port_name, color=P.get(track_type, P['any']))
        except Exception:
            # 可能在某些情况下（如端口已存在）会抛出异常，这时不添加新端口
            pass
        # 添加一个新的内联设置按钮，关联到新端口
        w = MkvInlineConfigButton(self.view, f'track_setting_{port_name}', port_name, mode='added')
        self.add_custom_widget(w)
        self.view.draw_node()

    def _patch_mkvmerge_view_layout(self):
        view = self.view

        # 覆写节点的长宽计算和组件布局方法，以适应内嵌设置按钮
        def custom_calc_size(self_view):
            p_input_h = 0.0
            # use max width of input ports rather than summing to avoid horizontal growth
            p_input_w = 0.0
            max_text_right = 0
            for p, p_text in self_view._input_items.items():
                if p.isVisible():
                    p_input_h += p.boundingRect().height() + 1
                    p_input_w = max(p_input_w, p.boundingRect().width())
                    max_text_right = max(max_text_right, p_text.pos().x() + p_text.boundingRect().width())
                    
            p_output_h = 0.0
            p_output_w = 0.0
            for port in self_view._output_items.keys():
                if port.isVisible():
                    p_output_h += port.boundingRect().height() + 1
                    p_output_w = max(p_output_w, port.boundingRect().width())
            
            port_height = max(p_input_h, p_output_h)
            
            widget_width = 0.0
            widget_height = 0.0
            for w in self_view._widgets.values():
                if w.isVisible():
                    w_name = getattr(w, '_name', '')
                    if w_name.startswith('track_setting_'):
                        pass
                    else:
                        widget_width = max(widget_width, w.boundingRect().width())
                        widget_height += w.boundingRect().height() + 4
            
            width = max(p_input_w + p_output_w + 30, widget_width + 10)
            # 节点宽度保留更宽的下限，避免端口名和内联控件挤在一起
            width = max(width, 280)

            height = port_height + widget_height + 10
            return width, height

        # 调整控件位置，特殊处理以 track_setting_ 开头的组件，使其位于对应输入端口的右侧
        def custom_align_widgets(self_view, v_offset):
            if not self_view._widgets:
                return
            
            rect = self_view.boundingRect()
            max_text_right = 0
            for p, p_text in self_view._input_items.items():
                if p.isVisible():
                    max_text_right = max(max_text_right, p_text.pos().x() + p_text.boundingRect().width())
            
            inp_h = sum([p.boundingRect().height() + 1 for p in self_view._input_items.keys() if p.isVisible()])
            out_h = sum([p.boundingRect().height() + 1 for p in self_view._output_items.keys() if p.isVisible()])
            port_height = max(inp_h, out_h)
            y = rect.y() + v_offset + port_height + 5

            for widget in self_view._widgets.values():
                if not widget.isVisible():
                    continue
                w_rect = widget.boundingRect()
                w_name = getattr(widget, '_name', '')
                
                # 拦截特殊设定的组件，置于对应端口右侧平行处
                if w_name.startswith('track_setting_'):
                    port_name = w_name.replace('track_setting_', '')
                    for p, p_text in self_view._input_items.items():
                        if p.name == port_name:
                            # 相对 Y 轴剧中于端口圆点
                            py = p.pos().y() - w_rect.height() / 2 + p.boundingRect().height() / 2
                            # 居中放置，避免遮挡右侧输出端口
                            inline_x = rect.center().x() - (w_rect.width() / 2)
                            widget.setPos(inline_x, py)
                            break
                else:
                    x = rect.center().x() - (w_rect.width() / 2)
                    if hasattr(widget.widget(), 'setTitleAlign'):
                        widget.widget().setTitleAlign('center')
                    widget.setPos(x, y)
                    y += w_rect.height() + 2

        # 覆盖 _base.py 中普通的实例方法
        view._calc_size_horizontal = types.MethodType(custom_calc_size, view)
        view._align_widgets_horizontal = types.MethodType(custom_align_widgets, view)
        view.draw_node()

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
