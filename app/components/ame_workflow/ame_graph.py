from NodeGraphQt import NodeGraph
from NodeGraphQt.constants import PipeLayoutEnum
from PySide6.QtCore import Qt, QEvent, QObject, QPoint
from PySide6.QtWidgets import QGraphicsView, QGraphicsProxyWidget, QAbstractScrollArea

from qfluentwidgets import isDarkTheme, qconfig

from .nodes import ALL_NODE_CLASSES
from .ame_hotkeys import register as register_hotkeys


class _ProxyEventFilter(QObject):
    """拦截 viewer 的滚轮/鼠标事件，直接操作内嵌可滚动控件的 ScrollBar"""

    def __init__(self, viewer):
        super().__init__()
        self._viewer = viewer
        self._drag_info = None  # (scrollbar, press_scene_y, init_val, widget_scene_h)

    def eventFilter(self, obj, event):
        et = event.type()
        if et == QEvent.Type.Wheel:
            return self._forward_wheel(event)
        if et in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease, QEvent.Type.MouseMove):
            return self._forward_mouse(event, et)
        return False

    def _get_event_pos(self, event):
        """兼容获取事件的 viewport 坐标"""
        try:
            return event.position().toPoint()
        except AttributeError:
            return event.pos()

    def _find_scroll_area(self, event):
        """返回光标下第一个可滚动的 QAbstractScrollArea，以及它所在的 QGraphicsProxyWidget"""
        vp_pos = self._get_event_pos(event)
        items = self._viewer.items(vp_pos)
        for item in items:
            if isinstance(item, QGraphicsProxyWidget):
                w = item.widget()
                for sa in w.findChildren(QAbstractScrollArea):
                    return sa, item
        return None, None

    def _is_over_scrollbar(self, proxy_item, scene_pos):
        """判断场景坐标是否在代理控件的右侧滚动条区域"""
        rect = proxy_item.sceneBoundingRect()
        local = proxy_item.mapFromScene(scene_pos)
        return local.x() >= rect.width() - 18 # 滚动条在控件右侧的大致宽度

    # ── 滚轮 ──
    def _forward_wheel(self, event):
        sa, _ = self._find_scroll_area(event)
        if not sa:
            return False
        sb = sa.verticalScrollBar()
        if not sb or sb.maximum() == 0:
            return False
        delta = event.angleDelta().y()
        if delta == 0:
            return False
        
        # 将滚轮的物理滚动量转换为滚动条的值
        step = max(1, sb.singleStep())
        scroll_amount = -delta * step // 40  # 一个滚轮凹槽(通常为120) ≈ 3个step
        
        # 边界保护
        new_val = max(0, min(sb.maximum(), sb.value() + scroll_amount))
        sb.setValue(new_val)
        return True

    # ── 鼠标（拦截滚动条区域的按下/拖拽/释放） ──
    def _forward_mouse(self, event, et):
        if et == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                return self._on_press(event)
            return False

        if et == QEvent.Type.MouseMove:
            return self._on_move(event)

        if et == QEvent.Type.MouseButtonRelease:
            if self._drag_info:
                self._drag_info = None
                return True # 消费释放事件，防止触发画布的其他操作
            return False

        return False

    def _on_press(self, event):
        vp_pos = self._get_event_pos(event)
        scene_pos = self._viewer.mapToScene(vp_pos)
        
        for item in self._viewer.items(vp_pos):
            if isinstance(item, QGraphicsProxyWidget):
                w = item.widget()
                for sa in w.findChildren(QAbstractScrollArea):
                    sb = sa.verticalScrollBar()
                    # 只有当文本超出可视区域(maximum > 0) 且点在滚动条上时才拦截
                    if sb and sb.maximum() > 0 and self._is_over_scrollbar(item, scene_pos):
                        rect = item.sceneBoundingRect()
                        self._drag_info = (sb, scene_pos.y(), sb.value(), rect.height())
                        return True
                break
        return False

    def _on_move(self, event):
        if not self._drag_info:
            return False
        
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            # 每次移动时，检查鼠标左键是否还按着。如果没有，强制解除拖拽状态
            self._drag_info = None
            return False
            
        sb, press_y, init_val, widget_h = self._drag_info
        scene_pos = self._viewer.mapToScene(self._get_event_pos(event))
        dy = scene_pos.y() - press_y
        
        # 【优化计算比例】：刨除滑块本身的大致高度，让鼠标拖拽到底部时能真正滑到底
        # 真实可视比例 = pageStep / (maximum + pageStep)
        track_height = max(10, widget_h - 20) # 减去 20px 预留给上下边缘
        ratio = sb.maximum() / track_height
        
        new_val = int(init_val + (dy * ratio))
        # 边界保护
        sb.setValue(max(0, min(sb.maximum(), new_val)))
        return True

class AMEGraph:
    def __init__(self, parent=None):
        self.graph = NodeGraph(parent=parent)
        self.graph.set_pipe_style(PipeLayoutEnum.CURVED.value)

        for cls in ALL_NODE_CLASSES:
            self.graph.register_node(cls)

        w = self.graph.widget
        w.setParent(parent)
        w.show()
        w.setObjectName("ame_graph_widget")

        self._viewer = None
        for child in w.findChildren(QGraphicsView):
            self._viewer = child
            break
        if self._viewer:
            self._viewer.setContextMenuPolicy(Qt.CustomContextMenu)
            self._viewer.setFrameShape(QGraphicsView.NoFrame)
            self._viewer.setObjectName("ame_graph_viewer")
            register_hotkeys(self._viewer, self.graph)
            self._proxy_filter = _ProxyEventFilter(self._viewer)
            self._viewer.viewport().installEventFilter(self._proxy_filter)

        qconfig.themeChanged.connect(self._apply_theme)
        self._apply_theme()

    def setup_default_nodes(self):
        ws_node = self.graph.create_node('ame.WorkspaceNode', pos=[100, 80], push_undo=False)
        inp_node = self.graph.create_node('ame.InputFileNode', pos=[100, 300], push_undo=False)
        out_node = self.graph.create_node('ame.OutputNode', pos=[1000, 220], push_undo=False)
        for n in (ws_node, inp_node, out_node):
            self._fix_node_view(n)
            if isDarkTheme():
                n.set_color(45, 45, 45)
        ws_node.set_output(0, inp_node.input(0))

    def _apply_theme(self):
        dark = isDarkTheme()
        if dark:
            self.graph.set_background_color(26, 26, 26)
            self.graph.set_grid_color(51, 51, 51)
            text_c = (220, 220, 220, 255)
            border_c = (85, 85, 85, 255)
        else:
            self.graph.set_background_color(240, 240, 240)
            self.graph.set_grid_color(221, 221, 221)
            text_c = (80, 80, 80, 255)
            border_c = (200, 200, 200, 255)

        for node in self.graph.all_nodes():
            node.model.text_color = text_c
            node.model.border_color = border_c
            if dark:
                node.set_color(45, 45, 45)
            elif hasattr(node, '_original_color'):
                node.set_color(*node._original_color)
        self._fix_all_node_views()

    def viewer(self):
        return self._viewer

    def widget(self):
        return self.graph.widget

    def create_node(self, type_, name=None, pos=None):
        node = self.graph.create_node(type_, name=name, pos=pos, push_undo=False)
        self._fix_node_view(node)
        if isDarkTheme():
            node.set_color(45, 45, 45)
        return node

    def _fix_node_view(self, node):
        if not hasattr(node, 'view') or node.view is None:
            return
        v = node.view
        v.setCursor(Qt.CrossCursor)
        if hasattr(v, 'text_item') and v.text_item:
            try:
                v.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
            except Exception:
                pass

    def _fix_all_node_views(self):
        """遍历所有节点修复光标和文本交互"""
        for node in self.graph.all_nodes():
            self._fix_node_view(node)

    def selected_nodes(self):
        return self.graph.selected_nodes()

    def all_nodes(self):
        return self.graph.all_nodes()

    def save_session(self, path):
        self.graph.save_session(path)

    def load_session(self, path):
        self.graph.load_session(path)
        self._fix_all_node_views()

    def delete_node(self, node):
        self.graph.delete_node(node)

    def get_node_by_id(self, nid):
        return self.graph.get_node_by_id(nid)
