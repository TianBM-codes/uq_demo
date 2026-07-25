from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen

from .base_node import BaseNode


class ContainerNode(BaseNode):
    LEVEL_COLORS = {
        "系统层": "#8E44AD",
        "子系统层": "#2980B9",
        "部件层": "#27AE60",
        "材料层": "#D35400",
    }

    def __init__(self, name="子系统", level="子系统层"):
        super().__init__(title=name, node_type="container")
        self.level = level
        self.params = {
            "name": name,
            "level": level,
            "amplification": 1.5,
            "std_dev": 0.5,
            "child_stages": [],
        }
        self.width = 190
        self.height = 126
        self.title_height = 32
        self.add_input_port("In")
        self.add_output_port("Out")
        self._hint_text = "双击查看内部传播"
        self.output_dist = None

    def _get_title_color(self):
        return QColor(self.LEVEL_COLORS.get(self.level, "#34495E"))

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.is_running:
            painter.setPen(QPen(QColor("#FF6F00"), 3))
        elif self.isSelected():
            painter.setPen(QPen(QColor("#FF6F00"), 2))
        else:
            painter.setPen(QPen(QColor("#95A5A6"), 1.5))

        gradient = QLinearGradient(0, 0, 0, self.height)
        gradient.setColorAt(0, QColor("#F8F9FA"))
        gradient.setColorAt(1, QColor("#ECF0F1"))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._get_title_color()))
        painter.drawRoundedRect(0, 0, self.width, self.title_height, 8, 8)
        painter.drawRect(0, self.title_height - 8, self.width, 8)

        painter.setPen(QPen(QColor("#7F8C8D"), 1))
        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.drawText(
            QRectF(10, self.title_height + 12, self.width - 20, self.height - self.title_height - 22),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.level}\n放大系数: {self.params.get('amplification', 1.5):.2f}\n{self._hint_text}",
        )

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if hasattr(scene, "container_double_clicked") and scene.container_double_clicked:
                scene.container_double_clicked(self)
        super().mouseDoubleClickEvent(event)


class InportNode(BaseNode):
    def __init__(self, name="In"):
        super().__init__(title=name, node_type="inport")
        self.params = {"port_name": name}
        self.width = 70
        self.height = 44
        self.title_height = 24
        self.add_output_port("out")

    def _get_title_color(self):
        return QColor("#E67E22")


class OutportNode(BaseNode):
    def __init__(self, name="Out"):
        super().__init__(title=name, node_type="outport")
        self.params = {"port_name": name}
        self.width = 70
        self.height = 44
        self.title_height = 24
        self.add_input_port("in")

    def _get_title_color(self):
        return QColor("#3498DB")
