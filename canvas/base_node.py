from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem


class Port(QGraphicsItem):
    def __init__(self, node, port_type="output", name="out"):
        super().__init__(node)
        self.node = node
        self.port_type = port_type
        self.name = name
        self.radius = 6
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, self.radius * 2, self.radius * 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#3498DB") if self.port_type == "output" else QColor("#E67E22")
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor("#2C3E50"), 1))
        painter.drawEllipse(-self.radius, -self.radius, self.radius * 2, self.radius * 2)

    def get_scene_pos(self):
        return self.mapToScene(QPointF(0, 0))


class BaseNode(QGraphicsItem):
    def __init__(self, title="节点", node_type="base"):
        super().__init__()
        self.title = title
        self.node_type = node_type
        self.params = {}
        self.input_ports = []
        self.output_ports = []
        self.is_running = False

        self.width = 140
        self.height = 80
        self.title_height = 28

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.title_item = QGraphicsTextItem(title, self)
        self.title_item.setDefaultTextColor(QColor("#FFFFFF"))
        self.title_item.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.title_item.setPos(8, 4)

    def add_input_port(self, name="in"):
        port = Port(self, "input", name)
        port.setPos(0, self.title_height + 15 + len(self.input_ports) * 22)
        self.input_ports.append(port)
        self._adjust_height()
        return port

    def add_output_port(self, name="out"):
        port = Port(self, "output", name)
        port.setPos(self.width, self.title_height + 15 + len(self.output_ports) * 22)
        self.output_ports.append(port)
        self._adjust_height()
        return port

    def _adjust_height(self):
        max_ports = max(len(self.input_ports), len(self.output_ports), 1)
        self.height = self.title_height + 20 + max_ports * 22

    def boundingRect(self):
        return QRectF(-2, -2, self.width + 4, self.height + 4)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.is_running:
            painter.setPen(QPen(QColor("#FF6F00"), 3))
            painter.setBrush(QBrush(QColor("#FFF3E0")))
        elif self.isSelected():
            painter.setPen(QPen(QColor("#FF6F00"), 2))
            painter.setBrush(QBrush(QColor("#FAFAFA")))
        else:
            painter.setPen(QPen(QColor("#BDC3C7"), 1.5))
            painter.setBrush(QBrush(QColor("#FFFFFF")))

        painter.drawRoundedRect(0, 0, self.width, self.height, 6, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._get_title_color()))
        painter.drawRoundedRect(0, 0, self.width, self.title_height, 6, 6)
        painter.drawRect(0, self.title_height - 6, self.width, 6)

    def _get_title_color(self):
        return QColor("#34495E")

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged and self.scene():
            for conn in getattr(self.scene(), "connections", []):
                if conn.start_port.node == self or conn.end_port.node == self:
                    conn.update_path()
        return super().itemChange(change, value)

    def set_running(self, running):
        self.is_running = running
        self.update()
