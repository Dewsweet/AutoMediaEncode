from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import QGraphicsObject

from .node_port import AMEPortItem
from . import (
    PortType, PortDirection, PORT_COLORS, CATEGORY_COLORS,
    NODE_HEADER_HEIGHT, NODE_PORT_SPACING, NODE_PADDING_H, NODE_PADDING_V,
    NODE_MIN_WIDTH, NODE_CORNER_RADIUS, NODE_PORT_RADIUS
)


class AMENodeItem(QGraphicsObject):
    double_clicked = Signal(object)
    moved = Signal(object)

    def __init__(self, node_data: dict, parent=None):
        super().__init__(parent)
        self._data = node_data
        self._input_ports = []
        self._output_ports = []
        self._selected = False
        self._status = "idle"
        self._initialized = False

        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setZValue(0)
        self.setAcceptHoverEvents(True)

        self._build_ports()
        self._update_size()

        self.setPos(node_data.get('x', 0), node_data.get('y', 0))
        self._initialized = True

    def node_id(self):
        return self._data.get('id', '')

    def node_type(self):
        return self._data.get('type', '')

    def node_name(self):
        return self._data.get('name', '')

    def category(self):
        return self._data.get('category', '')

    def header_color(self):
        return self._data.get('color', '#607D8B')

    def params(self):
        return self._data.get('params', {})

    def set_param(self, key, value):
        if 'params' not in self._data:
            self._data['params'] = {}
        self._data['params'][key] = value

    def input_ports(self):
        return list(self._input_ports)

    def output_ports(self):
        return list(self._output_ports)

    def set_status(self, status: str):
        self._status = status
        self.update()

    def all_ports(self):
        return self._input_ports + self._output_ports

    def find_port(self, port_name: str):
        for p in self.all_ports():
            if p.port_name() == port_name:
                return p
        return None

    def get_state(self):
        self._data['x'] = self.pos().x()
        self._data['y'] = self.pos().y()
        return self._data

    def _build_ports(self):
        input_defs = self._data.get('input_ports', [])
        output_defs = self._data.get('output_ports', [])

        port_x_in = 0
        port_x_out = self._compute_node_width()

        for i, pd in enumerate(input_defs):
            name = pd.get('name', '')
            ptype = pd.get('type', PortType.ANY)
            required = pd.get('required', False)
            y = self._port_y(i)
            port = AMEPortItem(name, ptype, PortDirection.INPUT, self, required)
            port.setPos(port_x_in, y)
            self._input_ports.append(port)

        for i, pd in enumerate(output_defs):
            name = pd.get('name', '')
            ptype = pd.get('type', PortType.ANY)
            y = self._port_y(i)
            port = AMEPortItem(name, ptype, PortDirection.OUTPUT, self)
            port.setPos(port_x_out, y)
            self._output_ports.append(port)

    def _port_y(self, index):
        return NODE_HEADER_HEIGHT + NODE_PADDING_V + NODE_PORT_RADIUS + index * NODE_PORT_SPACING

    def _compute_node_width(self):
        all_labels = [p.get('name', '') for p in self._data.get('input_ports', [])]
        all_labels += [p.get('name', '') for p in self._data.get('output_ports', [])]
        w = len(max(all_labels, key=len)) * 7 if all_labels else 40
        w = w * 2 + NODE_PADDING_H * 2 + NODE_PORT_RADIUS * 4
        return max(w + 20, NODE_MIN_WIDTH)

    def _update_size(self):
        w = self._compute_node_width()
        port_count = max(len(self._input_ports), len(self._output_ports), 1)
        h = NODE_HEADER_HEIGHT + NODE_PADDING_V * 2 + port_count * NODE_PORT_SPACING
        self._node_width = w
        self._node_height = h

    def boundingRect(self):
        return QRectF(0, 0, self._node_width, self._node_height)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        w, h = self._node_width, self._node_height
        r = NODE_CORNER_RADIUS

        header_h = NODE_HEADER_HEIGHT

        body_path = QPainterPath()
        body_path.addRoundedRect(QRectF(0, 0, w, h), r, r)

        header_path = QPainterPath()
        header_path.moveTo(r, header_h)
        header_path.lineTo(w - r, header_h)
        header_path.arcTo(QRectF(w - r * 2, 0, r * 2, r * 2), 90, -90)
        header_path.lineTo(r, 0)
        header_path.arcTo(QRectF(0, 0, r * 2, r * 2), 180, -90)
        header_path.closeSubpath()

        body_color = QColor(0x2D, 0x2D, 0x2D) if self._is_dark() else QColor(0xF5, 0xF5, 0xF5)
        painter.fillPath(body_path, body_color)

        header_color = QColor(self.header_color())
        if not header_color.isValid():
            header_color = QColor('#607D8B')
        painter.fillPath(header_path, header_color)

        if self.isSelected() or self._selected:
            pen = QPen(QColor(0x00, 0x9F, 0xAA), 2)
        else:
            pen = QPen(QColor(0x55, 0x55, 0x55), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        if self._status == "running":
            status_pen = QPen(QColor(0x00, 0x9F, 0xAA), 2.5)
            painter.setPen(status_pen)
            painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)
        elif self._status == "done":
            status_pen = QPen(QColor(0x4C, 0xAF, 0x50), 2.5)
            painter.setPen(status_pen)
            painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)
        elif self._status == "error":
            status_pen = QPen(QColor(0xF4, 0x43, 0x36), 2.5)
            painter.setPen(status_pen)
            painter.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        font = QFont("Segoe UI", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(0xFF, 0xFF, 0xFF))
        text_y = header_h // 2 + 4
        painter.drawText(QRectF(NODE_PADDING_H, 0, w - NODE_PADDING_H * 2, header_h),
                         Qt.AlignLeft | Qt.AlignVCenter, self.node_name())

        font2 = QFont("Segoe UI", 9)
        painter.setFont(font2)
        text_color = QColor(0xCC, 0xCC, 0xCC) if self._is_dark() else QColor(0x55, 0x55, 0x55)
        painter.setPen(text_color)

        for i, port in enumerate(self._input_ports):
            y = self._port_y(i)
            label_rect = QRectF(NODE_PADDING_H, y - 8, w * 0.4, 16)
            painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter, port.port_name())

        for i, port in enumerate(self._output_ports):
            y = self._port_y(i)
            label_rect = QRectF(w * 0.55, y - 8, w * 0.4 - NODE_PADDING_H, 16)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, port.port_name())

    def itemChange(self, change, value):
        if change == QGraphicsObject.ItemPositionHasChanged and self._initialized:
            self._update_all_edges()
            self.moved.emit(self)
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)

    def _update_all_edges(self):
        for port in self.all_ports():
            for edge in port.connected_edges():
                edge.update_path()

    def _is_dark(self):
        try:
            from qfluentwidgets import isDarkTheme
            return isDarkTheme()
        except ImportError:
            return True
