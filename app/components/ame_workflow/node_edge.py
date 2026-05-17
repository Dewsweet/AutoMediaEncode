from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainter, QBrush
from PySide6.QtWidgets import QGraphicsPathItem

from . import PortType, PORT_COLORS, NODE_PORT_RADIUS


class AMEEdge(QGraphicsPathItem):
    def __init__(self, source_port, target_port=None, parent=None):
        super().__init__(parent)
        self._source_port = source_port
        self._target_port = target_port
        self._temp_end = None
        self.setZValue(-1)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, False)
        self._color = QColor(*PORT_COLORS.get(source_port.port_type(), (0x95, 0xA5, 0xA6)))
        self._update_path()

    def source_port(self):
        return self._source_port

    def target_port(self):
        return self._target_port

    def set_temp_end(self, scene_pos: QPointF):
        self._temp_end = scene_pos
        self._update_path()

    def commit_target(self, target_port):
        self._target_port = target_port
        self._temp_end = None
        self._color = QColor(*PORT_COLORS.get(self._source_port.port_type(), (0x95, 0xA5, 0xA6)))
        self._update_path()

    def update_path(self):
        self._update_path()

    def _update_path(self):
        if self._source_port is None:
            return
        start = self._source_port.center_scene_pos()
        if self._target_port:
            end = self._target_port.center_scene_pos()
        elif self._temp_end:
            end = self._temp_end
        else:
            end = start

        path = QPainterPath()
        path.moveTo(start)
        dx = abs(end.x() - start.x()) * 0.5
        if dx < 50:
            dx = 50
        ctrl1 = QPointF(start.x() + dx, start.y())
        ctrl2 = QPointF(end.x() - dx, end.y())
        path.cubicTo(ctrl1, ctrl2, end)
        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None):
        pen = QPen(self._color, 2, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPath(self.path())


class TempEdge(QGraphicsPathItem):
    def __init__(self, start_pos: QPointF, parent=None):
        super().__init__(parent)
        self._start = start_pos
        self._end = start_pos
        self.setZValue(-1)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, False)

    def set_end(self, pos: QPointF):
        self._end = pos
        path = self._build_path()
        self.setPath(path)

    def _build_path(self):
        path = QPainterPath()
        path.moveTo(self._start)
        dx = abs(self._end.x() - self._start.x()) * 0.5
        if dx < 50:
            dx = 50
        ctrl1 = QPointF(self._start.x() + dx, self._start.y())
        ctrl2 = QPointF(self._end.x() - dx, self._end.y())
        path.cubicTo(ctrl1, ctrl2, self._end)
        return path

    def paint(self, painter: QPainter, option, widget=None):
        pen = QPen(QColor(0xAA, 0xAA, 0xAA), 2, Qt.DashLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPath(self.path())
