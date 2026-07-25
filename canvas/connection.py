from PySide6.QtCore import QEasingCurve, QPointF, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsPathItem


class Connection(QGraphicsPathItem):
    def __init__(self, start_port, end_port):
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1)

        self._color = QColor("#7F8C8D")
        self._pen = QPen(self._color, 2)
        self.setPen(self._pen)

        self._anim_progress = 0.0
        self._animation = None
        self.update_path()

    def update_path(self):
        start = self.start_port.get_scene_pos()
        end = self.end_port.get_scene_pos()
        dx = (end.x() - start.x()) * 0.5
        ctrl1 = QPointF(start.x() + dx, start.y())
        ctrl2 = QPointF(end.x() - dx, end.y())

        path = QPainterPath(start)
        path.cubicTo(ctrl1, ctrl2, end)
        self.setPath(path)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen)
        painter.drawPath(self.path())

        if self._anim_progress > 0:
            point = self.path().pointAtPercent(self._anim_progress)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#FF6F00"))
            painter.drawEllipse(point, 4, 4)

    def start_flow_animation(self, duration=800):
        if self._animation:
            self._animation.stop()

        self._anim_progress = 0.0
        self._animation = QVariantAnimation()
        self._animation.setDuration(duration)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._animation.valueChanged.connect(self._on_value_changed)
        self._animation.finished.connect(self._on_animation_finished)
        self._animation.start()

    def _on_value_changed(self, value):
        self._anim_progress = float(value)
        self.update()

    def _on_animation_finished(self):
        self._anim_progress = 0.0
        self.update()
