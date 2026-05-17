from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem

from . import PortType, PortDirection, PORT_COLORS, NODE_PORT_RADIUS


class AMEPortItem(QGraphicsEllipseItem):

    def __init__(self, port_name: str, port_type: str, direction: str, node_item, required: bool = False):
        r = NODE_PORT_RADIUS
        super().__init__(-r, -r, r * 2, r * 2, node_item)
        self._port_name = port_name
        self._port_type = port_type
        self._direction = direction
        self._node = node_item
        self._required = required
        self._connected_edges = []
        self._highlight = False
        self._hovered = False
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        self._update_appearance()

    def port_name(self):
        return self._port_name

    def port_type(self):
        return self._port_type

    def direction(self):
        return self._direction

    def is_input(self):
        return self._direction == PortDirection.INPUT

    def is_output(self):
        return self._direction == PortDirection.OUTPUT

    def node(self):
        return self._node

    def is_required(self):
        return self._required

    def connected_edges(self):
        return list(self._connected_edges)

    def add_edge(self, edge):
        if edge not in self._connected_edges:
            self._connected_edges.append(edge)

    def remove_edge(self, edge):
        if edge in self._connected_edges:
            self._connected_edges.remove(edge)

    def set_highlight(self, on: bool):
        if self._highlight != on:
            self._highlight = on
            self._update_appearance()

    def can_connect(self, other) -> bool:
        if other is None or other is self:
            return False
        if self._node is other._node:
            return False
        if self._direction == other._direction:
            return False
        source = self if self.is_output() else other
        target = other if self.is_output() else self
        return target._port_type in {PortType.ANY, source._port_type}

    def hoverEnterEvent(self, event):
        self._hovered = True
        self._update_appearance()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self._update_appearance()
        super().hoverLeaveEvent(event)

    def center_scene_pos(self):
        return self.scenePos()

    def _update_appearance(self):
        r, g, b = PORT_COLORS.get(self._port_type, (0x95, 0xA5, 0xA6))
        if self._highlight:
            r, g, b = 0xFF, 0xFF, 0xFF
            pen = QPen(QColor(0, 0xFF, 0), 2)
            brush = QBrush(QColor(0, 0xFF, 0))
        elif self._hovered:
            pen = QPen(QColor(r, g, b, 220), 2)
            brush = QBrush(QColor(r, g, b, 220))
        else:
            pen = QPen(QColor(r, g, b), 1.5)
            brush = QBrush(QColor(r, g, b))
        self.setPen(pen)
        self.setBrush(brush)
