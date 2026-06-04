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
    'Green': (65, 195, 59),
    'Blue': (88, 169, 220),
    'Purple': (103, 88, 220),
    'Orange': (220, 150, 88),
    'Red': (220, 88, 88),
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
        self._status = 'idle'
        self.set_color(*self.CATEGORY_COLOR)
        for name, color in self.INPUTS:
            self.add_input(name, color=color)
        for name, color in self.OUTPUTS:
            self.add_output(name, color=color)
            
        self._patch_view_layout()
        self._setup_widgets()

    def set_status(self, status: str):
        self._status = status
        if status == 'running':
            self.set_selected(True)
        else:
            self.set_selected(False)

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
                    p_input_w = max(p_input_w, port.boundingRect().width())

            p_output_h = 0.0
            p_output_w = 0.0
            for port in self_view._output_items.keys():
                if port.isVisible():
                    p_output_h += port.boundingRect().height() + 1
                    p_output_w = max(p_output_w, port.boundingRect().width())

            port_height = max(p_input_h, p_output_h)
            widget_width = 0.0
            widget_height = 0.0
            for widget in self_view._widgets.values():
                if widget.isVisible():
                    widget_width = max(widget_width, widget.boundingRect().width())
                    widget_height += widget.boundingRect().height() + 4
            width = max(p_input_w + p_output_w + 30, widget_width + 10, 200)
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
