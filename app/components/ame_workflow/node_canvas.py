from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QWheelEvent, QKeyEvent, QFont
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene

from qfluentwidgets import isDarkTheme

from .node_item import AMENodeItem
from .node_port import AMEPortItem
from .node_edge import AMEEdge, TempEdge
from . import PORT_COLORS, PortDirection, PortType

GRID_SIZE = 20
GRID_SIZE_MINOR = 10


class AMENodeCanvas(QGraphicsView):
    node_added = Signal(object)
    node_removed = Signal(str)
    edge_created = Signal(object)
    edge_removed = Signal(object)
    context_menu_requested = Signal(QPointF)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._scene.setSceneRect(-5000, -5000, 10000, 10000)

        self._pan_start = QPointF()
        self._is_panning = False
        self._pan_button = Qt.MiddleButton

        self._edge_start_port = None
        self._temp_edge = None

        self._zoom_level = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 3.0

        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setAcceptDrops(False)
        self.setFrameShape(QGraphicsView.NoFrame)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def scene(self):
        return self._scene

    def add_node(self, node_data: dict, x: float = 0, y: float = 0):
        node_data['x'] = x
        node_data['y'] = y
        node = AMENodeItem(node_data)
        self._scene.addItem(node)
        node.double_clicked.connect(self._on_node_double_clicked)
        node.moved.connect(self._on_node_moved)
        self.node_added.emit(node)
        return node

    def add_edge(self, source_port, target_port):
        if source_port.is_output():
            src = source_port
            tgt = target_port
        else:
            src = target_port
            tgt = source_port

        existing_edges = list(src.connected_edges())
        for edge in existing_edges:
            if edge.target_port() is tgt:
                return None

        edge = AMEEdge(src, tgt)
        self._scene.addItem(edge)
        src.add_edge(edge)
        tgt.add_edge(edge)
        self.edge_created.emit(edge)
        return edge

    def remove_node(self, node: AMENodeItem):
        self._disconnect_all_ports(node)
        self._scene.removeItem(node)
        self.node_removed.emit(node.node_id())

    def remove_edge(self, edge: AMEEdge):
        sp = edge.source_port()
        tp = edge.target_port()
        if sp:
            sp.remove_edge(edge)
        if tp:
            tp.remove_edge(edge)
        self._scene.removeItem(edge)
        self.edge_removed.emit(edge)

    def delete_selected(self):
        for item in self._scene.selectedItems():
            if isinstance(item, AMENodeItem):
                self.remove_node(item)
        selected_edges = [i for i in self._scene.selectedItems() if isinstance(i, AMEEdge)]
        for edge in selected_edges:
            self.remove_edge(edge)

    def get_nodes(self):
        return [item for item in self._scene.items() if isinstance(item, AMENodeItem)]

    def get_edges(self):
        return [item for item in self._scene.items() if isinstance(item, AMEEdge)]

    def reset_view(self):
        self.resetTransform()
        self._zoom_level = 1.0
        self.centerOn(0, 0)

    def zoom_in(self):
        self._apply_zoom(1.15)

    def zoom_out(self):
        self._apply_zoom(1 / 1.15)

    def _apply_zoom(self, factor):
        new_zoom = self._zoom_level * factor
        if self._min_zoom <= new_zoom <= self._max_zoom:
            self.scale(factor, factor)
            self._zoom_level = new_zoom

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta > 0:
            self._apply_zoom(1.1)
        else:
            self._apply_zoom(1 / 1.1)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == self._pan_button:
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.position().toPoint())
            port = self._find_port_at(item)
            if isinstance(port, AMEPortItem) and port.is_output():
                self._edge_start_port = port
                self._temp_edge = TempEdge(port.center_scene_pos())
                self._scene.addItem(self._temp_edge)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
            return

        if self._temp_edge:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._temp_edge.set_end(scene_pos)

            hover_item = self._find_port_at(self.itemAt(event.position().toPoint()))
            self._clear_port_highlights()
            if hover_item and hover_item.is_input():
                if self._edge_start_port.can_connect(hover_item):
                    hover_item.set_highlight(True)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == self._pan_button and self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if self._temp_edge:
            hover_item = self._find_port_at(self.itemAt(event.position().toPoint()))
            self._clear_port_highlights()
            if hover_item and hover_item.is_input() and self._edge_start_port.can_connect(hover_item):
                self.add_edge(self._edge_start_port, hover_item)
            self._scene.removeItem(self._temp_edge)
            self._temp_edge = None
            self._edge_start_port = None
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self.delete_selected()
        elif event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            for item in self.get_nodes():
                item.setSelected(True)
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.save()
        dark = isDarkTheme()

        if dark:
            bg_color = QColor(0x1A, 0x1A, 0x1A)
            grid_major = QColor(0x33, 0x33, 0x33)
            grid_minor = QColor(0x25, 0x25, 0x25)
        else:
            bg_color = QColor(0xF0, 0xF0, 0xF0)
            grid_major = QColor(0xDD, 0xDD, 0xDD)
            grid_minor = QColor(0xE8, 0xE8, 0xE8)

        painter.fillRect(rect, bg_color)

        scale = self.transform().m11()
        if scale < 0.3:
            painter.restore()
            return

        left = int(rect.left()) - (int(rect.left()) % GRID_SIZE_MINOR)
        top = int(rect.top()) - (int(rect.top()) % GRID_SIZE_MINOR)

        lines_minor = []
        lines_major = []
        step = GRID_SIZE_MINOR
        x = left
        while x < rect.right():
            if x % GRID_SIZE == 0:
                lines_major.append((x, rect.top(), x, rect.bottom()))
            else:
                lines_minor.append((x, rect.top(), x, rect.bottom()))
            x += step
        y = top
        while y < rect.bottom():
            if y % GRID_SIZE == 0:
                lines_major.append((rect.left(), y, rect.right(), y))
            else:
                lines_minor.append((rect.left(), y, rect.right(), y))
            y += step

        if scale > 0.5:
            pen_minor = QPen(grid_minor, 0.5)
            painter.setPen(pen_minor)
            for x1, y1, x2, y2 in lines_minor:
                painter.drawLine(x1, y1, x2, y2)

        pen_major = QPen(grid_major, 1)
        painter.setPen(pen_major)
        for x1, y1, x2, y2 in lines_major:
            painter.drawLine(x1, y1, x2, y2)

        painter.restore()

    def _find_port_at(self, item):
        while item:
            if isinstance(item, AMEPortItem):
                return item
            item = item.parentItem() if hasattr(item, 'parentItem') else None
        return None

    def _clear_port_highlights(self):
        for port_item in self._find_all_ports():
            port_item.set_highlight(False)

    def _find_all_ports(self):
        ports = []
        for node in self.get_nodes():
            ports.extend(node.all_ports())
        return ports

    def _disconnect_all_ports(self, node: AMENodeItem):
        for port in node.all_ports():
            for edge in port.connected_edges():
                self.remove_edge(edge)

    def _on_node_double_clicked(self, node: AMENodeItem):
        pass

    def _on_node_moved(self, node: AMENodeItem):
        pass

    def _on_context_menu(self, pos):
        scene_pos = self.mapToScene(pos)
        self.context_menu_requested.emit(scene_pos)
