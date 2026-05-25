"""
AME 节点基类和常量定义。

═════════════════════════════════════════════════════════
节点文件 6 段模板：
─────────────────────────────────────────────────────────
# SECTION 1: Metadata — NODE_NAME, DESCRIPTION, CATEGORY, CATEGORY_COLOR, MENU_KEY
# SECTION 2: Port I/O — INPUTS, OUTPUTS (格式: [(name, color_rgb)])
# SECTION 3: __init__ — AMENodeBase 自动注册端口 + 控件
# SECTION 4: Inline Widgets — _setup_widgets() 方法
# SECTION 5: Dynamic Ports — on_input_connected() / add_output() [后续]
# SECTION 6: Execute — execute(inputs, temp_dir) -> dict | None
═════════════════════════════════════════════════════════

I/O 契约：
  execute(inputs: dict, temp_dir: str) -> {port_name: [file_paths]} | None
    inputs = {'port_name': [file_path]}  (上游节点的输出自动注入)
    返回 None = 执行失败，执行器停止后续节点
    返回 dict (包括空 {}) = 成功继续
"""
import types
from NodeGraphQt import BaseNode
from NodeGraphQt.constants import NodePropWidgetEnum as NPE

HIDDEN = NPE.HIDDEN.value

C = {
    '系统': (96, 125, 139),
    '输入': (76, 175, 80),
    '处理': (255, 152, 0),
    '编码': (244, 67, 54),
    '封装': (156, 39, 176),
    '输出': (33, 150, 243),
    'Gray': (96, 125, 139),
    'Green': (170, 255, 168),
    'Blue': (168, 217, 255),
    'Purple': (233, 168, 255),
    'Orange': (255, 221, 168),
    'Sakura': (255, 168, 168),
}

P = {
    'video': (255, 107, 107),
    'audio': (78, 205, 196),
    'subtitle': (255, 217, 61),
    'chapter': (199, 146, 234),
    'attachment': (255, 138, 101),
    'script': (108, 92, 231),
    'any': (149, 165, 166),
}


class AMENodeBase(BaseNode):
    __identifier__ = 'ame'
    CATEGORY = '系统'
    CATEGORY_COLOR = C['系统']
    INPUTS = []
    OUTPUTS = []
    DESCRIPTION = ''
    MENU_KEY = ''
    SUPPORTS_WIDGET = False
    SUPPORTS_DYNAMIC_PORTS = False

    def __init__(self):
        super().__init__()
        self.set_color(*self.CATEGORY_COLOR)
        for name, color in self.INPUTS:
            self.add_input(name, color=color)
        for name, color in self.OUTPUTS:
            self.add_output(name, color=color)
            
        self._patch_view_layout()
        self._setup_widgets()

    def _patch_view_layout(self):
        """将控件位置调整到端口下方并居中"""
        view = self.view

        # 1. 覆写节点的长宽计算
        def custom_calc_size(self_view):
            p_input_h = 0.0
            p_input_w = 0.0
            for port in self_view._input_items.keys():
                if port.isVisible():
                    p_input_h += port.boundingRect().height() + 1
                    p_input_w += port.boundingRect().width()
                    
            p_output_h = 0.0
            p_output_w = 0.0
            for port in self_view._output_items.keys():
                if port.isVisible():
                    p_output_h += port.boundingRect().height() + 1
                    p_output_w += port.boundingRect().width()
            
            # 端口占据的最大高度
            port_height = max(p_input_h, p_output_h)
            widget_width = 0.0
            widget_height = 0.0
            for widget in self_view._widgets.values():
                if widget.isVisible():
                    widget_width = max(widget_width, widget.boundingRect().width())
                    widget_height += widget.boundingRect().height() + 4
            # 整体宽度：取端口排列宽 或 控件宽 的最大值
            # 整体高度：端口高度 + 控件总高度 （上下堆叠）
            width = max(p_input_w + p_output_w + 30, widget_width + 10)
            height = port_height + widget_height + 10
            return width, height

        # 2. 覆写控件的摆放位置
        def custom_align_widgets(self_view, v_offset):
            if not self_view._widgets:
                return
            
            # 计算端口占据的总高度
            inp_h = sum([p.boundingRect().height() + 1 for p in self_view._input_items.keys() if p.isVisible()])
            out_h = sum([p.boundingRect().height() + 1 for p in self_view._output_items.keys() if p.isVisible()])
            port_height = max(inp_h, out_h)
            
            rect = self_view.boundingRect()
            y = rect.y() + v_offset + port_height + 5
            
            for widget in self_view._widgets.values():
                if not widget.isVisible():
                    continue
                widget_rect = widget.boundingRect()
                x = rect.center().x() - (widget_rect.width() / 2)
                widget.widget().setTitleAlign('center')
                widget.setPos(x, y)
                y += widget_rect.height() + 2

        # 动态绑定方法到当前的 QGraphicsItem
        view._calc_size_horizontal = types.MethodType(custom_calc_size, view)
        view._align_widgets_horizontal = types.MethodType(custom_align_widgets, view)

    def _setup_widgets(self):
        pass

    def get_inspector_widget(self):
        return None

    def execute(self, inputs: dict, temp_dir: str) -> dict:
        return None

    def property(self, key, default=None):
        try:
            v = self.get_property(key)
            return v if v is not None else default
        except Exception:
            return default


def _do_cli_encode(node, inputs, temp_dir, tool_key, ext):
    import os, subprocess, shlex
    src = (inputs.get('input') or [''])[0]
    if not src: return None
    dst = os.path.join(temp_dir, f'{tool_key}_{node.id}{ext}')
    from app.services.tool_service import ToolService
    cli = ToolService.get_tool_path(tool_key)
    if not cli or not os.path.isfile(cli): return None
    pcfg = node.property('preset_cfg', {})
    use_p = pcfg.get('use_preset', True) if isinstance(pcfg, dict) else True
    pname = pcfg.get('preset', '') if isinstance(pcfg, dict) and use_p else ''
    cli_args = node.property('custom_cli', '')
    if pname:
        enc_map = {'x264':'x264','x265':'x265','SvtAv1':'SVTAV1'}
        from app.services.setting.preset_service import preset_service
        presets = preset_service.get_presets_by_encoder(enc_map.get(tool_key, tool_key))
        cli_args = presets.get(pname, pname) if presets else pname
    try: args = shlex.split(cli_args) if cli_args else []
    except ValueError: args = cli_args.split() if cli_args else []
    cmd = [cli, '--output', dst] if tool_key == 'SvtAv1' else [cli, '-o', dst]
    cmd.extend(args); cmd.append(src)
    cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=14400)
    return {'video': [dst]} if os.path.isfile(dst) and os.path.getsize(dst) > 0 else None
