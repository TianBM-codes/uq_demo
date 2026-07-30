import json

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QDrag, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsScene,
    QGraphicsTextItem,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from canvas.base_node import BaseNode
from canvas.connection import Connection
from canvas.graphics_view import UQGraphicsScene, UQGraphicsView


NODE_STYLE = {
    "support": {"bg": "#ECFDF5", "edge": "#059669", "title": "#047857"},
    "functional": {"bg": "#EFF6FF", "edge": "#2563EB", "title": "#1D4ED8"},
    "propagation": {"bg": "#FFF7ED", "edge": "#D97706", "title": "#C2410C"},
    "reliability": {"bg": "#F5F3FF", "edge": "#7C3AED", "title": "#6D28D9"},
}


class WorkflowNode(BaseNode):
    def __init__(self, block):
        super().__init__(title=block["title"], node_type=block["category"])
        self.block = block
        self.width = 220
        self.height = 138
        self.title_height = 34
        self.add_input_port("输入")
        self.add_output_port("输出")
        self._apply_fixed_geometry()
        self.title_item.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.title_item.setTextWidth(self.width - 44)
        self.title_item.setPos(12, 6)

        self.summary_item = QGraphicsTextItem(self)
        self.summary_item.setDefaultTextColor(QColor("#334155"))
        self.summary_item.setFont(QFont("Microsoft YaHei", 8))
        self.summary_item.setTextWidth(self.width - 28)
        self.summary_item.setPos(14, 46)
        self.summary_item.setPlainText(self._fit_summary(block["summary"]))

        self.footer_item = QGraphicsTextItem(self)
        self.footer_item.setDefaultTextColor(QColor("#64748B"))
        self.footer_item.setFont(QFont("Microsoft YaHei", 8))
        self.footer_item.setTextWidth(self.width - 28)
        self.footer_item.setPos(14, self.height - 32)
        self.footer_item.setPlainText(block["section_title"])

    def _fit_summary(self, text):
        lines = []
        current = ""
        limit = 16
        for char in text:
            current += char
            if len(current) >= limit:
                lines.append(current)
                current = ""
            if len(lines) == 3:
                break
        if current and len(lines) < 3:
            lines.append(current)
        if len(text) > sum(len(line) for line in lines):
            lines[-1] = lines[-1].rstrip() + "…"
        return "\n".join(lines)

    def _adjust_height(self):
        # Workflow nodes use a fixed card layout rather than port-count-driven height.
        self._apply_fixed_geometry()

    def _apply_fixed_geometry(self):
        self.height = 138
        if self.input_ports:
            self.input_ports[0].setPos(0, 78)
        if self.output_ports:
            self.output_ports[0].setPos(self.width, 78)

    def _get_title_color(self):
        return QColor(NODE_STYLE[self.block["category"]]["title"])

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        style = NODE_STYLE[self.block["category"]]
        border = QColor(style["edge"]) if self.isSelected() else QColor("#CBD5E1")
        width = 2.3 if self.isSelected() else 1.5

        painter.setPen(QPen(border, width))
        painter.setBrush(QBrush(QColor(style["bg"])))
        painter.drawRoundedRect(0, 0, self.width, self.height, 18, 18)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._get_title_color()))
        painter.drawRoundedRect(0, 0, self.width, self.title_height, 18, 18)
        painter.drawRect(0, self.title_height - 10, self.width, 10)

        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.drawLine(12, self.height - 38, self.width - 12, self.height - 38)


class WorkflowScene(UQGraphicsScene):
    selection_payload_changed = Signal(object)

    def __init__(self, nodes_by_id):
        super().__init__()
        self.nodes_by_id = nodes_by_id
        self.setBackgroundBrush(QBrush(QColor("#F8FBFF")))
        self.selectionChanged.connect(self._emit_selection)

    def add_block_node(self, block, pos):
        node = WorkflowNode(block)
        self.addItem(node)
        node.setPos(pos)
        node.setSelected(True)
        self._emit_selection()
        return node

    def create_connection(self, start_node, end_node):
        if start_node == end_node:
            return None
        for connection in self.connections:
            if connection.start_port.node == start_node and connection.end_port.node == end_node:
                return connection
        connection = Connection(start_node.output_ports[0], end_node.input_ports[0])
        self.add_connection(connection)
        self._emit_selection()
        return connection

    def selected_nodes(self):
        return [item for item in self.selectedItems() if isinstance(item, WorkflowNode)]

    def delete_selected(self):
        selected = list(self.selectedItems())
        if not selected:
            return
        for item in selected:
            if isinstance(item, WorkflowNode):
                related = [
                    conn for conn in list(self.connections)
                    if conn.start_port.node == item or conn.end_port.node == item
                ]
                for conn in related:
                    if conn in self.connections:
                        self.connections.remove(conn)
                    self.removeItem(conn)
                self.removeItem(item)
            elif isinstance(item, Connection):
                if item in self.connections:
                    self.connections.remove(item)
                self.removeItem(item)
        self._emit_selection()

    def clear_workflow(self):
        for item in list(self.items()):
            self.removeItem(item)
        self.connections = []
        self._emit_selection()

    def _emit_selection(self):
        nodes = self.selected_nodes()
        if len(nodes) == 1:
            self.selection_payload_changed.emit(nodes[0].block)
            return
        if len(nodes) > 1:
            self.selection_payload_changed.emit(
                {
                    "title": "多节点选择",
                    "section_title": "流程编排",
                    "stage_hint": "已选择多个组件",
                    "goal": "可以执行“连接选中节点”，让两个组件之间通过线建立参数传递关系。",
                    "inputs": "上游节点输出",
                    "outputs": "下游节点输入",
                    "algorithms": ["建立连接线", "调整节点位置", "删除或重连"],
                    "config_items": [
                        f"当前选中节点数：{len(nodes)}",
                        "建议先选上游节点，再选下游节点",
                        "连接建立后，拖动节点时连线会自动更新",
                    ],
                    "highlight_values": [
                        f"当前连接数：{len(self.connections)}",
                        "节点位置",
                        "上下游关系",
                    ],
                }
            )
            return
        self.selection_payload_changed.emit(None)


class WorkflowView(UQGraphicsView):
    node_dropped = Signal(dict)

    def __init__(self, scene):
        super().__init__(scene)
        self.setAcceptDrops(True)
        self.setDragMode(UQGraphicsView.DragMode.RubberBandDrag)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-uq-block"):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-uq-block"):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat("application/x-uq-block"):
            raw = bytes(event.mimeData().data("application/x-uq-block")).decode("utf-8")
            payload = json.loads(raw)
            scene_pos = self.mapToScene(event.position().toPoint())
            self.node_dropped.emit({"payload": payload, "pos": scene_pos})
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class WorkflowCanvas(QWidget):
    node_selected = Signal(object)

    def __init__(self, nodes, parent=None):
        super().__init__(parent)
        self.nodes = nodes
        self.scene = WorkflowScene(nodes)
        self.view = WorkflowView(self.scene)
        self.scene.selection_payload_changed.connect(self.node_selected.emit)
        self.view.node_dropped.connect(self._on_node_dropped)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background: transparent;
                font-family: "Microsoft YaHei";
            }
            QLabel {
                color: #102A43;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("拖拽式传播建模画布")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        note = QLabel("把左侧模块拖到中央画布，节点可再次拖动。选择两个组件后执行连接，就能用线建立上下游关系。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #52606D; font-size: 13px;")
        layout.addWidget(note)

        toolbar = QFrame()
        toolbar.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #D9E2EC;
                border-radius: 16px;
            }
            QPushButton {
                background: #F8FAFC;
                border: 1px solid #D9E2EC;
                border-radius: 12px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #EFF6FF;
                border-color: #60A5FA;
            }
            """
        )
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 10, 12, 10)
        toolbar_layout.setSpacing(10)

        add_demo = QPushButton("加载演示链路")
        add_demo.clicked.connect(self.load_demo_workflow)
        connect_btn = QPushButton("连接选中节点")
        connect_btn.clicked.connect(self.connect_selected_nodes)
        delete_btn = QPushButton("删除选中项")
        delete_btn.clicked.connect(self.scene.delete_selected)
        clear_btn = QPushButton("清空画布")
        clear_btn.clicked.connect(self.scene.clear_workflow)

        toolbar_layout.addWidget(add_demo)
        toolbar_layout.addWidget(connect_btn)
        toolbar_layout.addWidget(delete_btn)
        toolbar_layout.addWidget(clear_btn)
        toolbar_layout.addStretch()
        layout.addWidget(toolbar)

        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background: white;
                border: 1px solid #D9E2EC;
                border-radius: 24px;
            }
            """
        )
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.addWidget(self.view)
        layout.addWidget(frame, 1)

    def _on_node_dropped(self, event):
        block = self.nodes[event["payload"]["node_id"]]
        self.scene.add_block_node(block, event["pos"])

    def add_node_by_id(self, node_id, pos=None):
        block = self.nodes[node_id]
        if pos is None:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            pos = QPointF(center.x() - 80, center.y() - 40)
        return self.scene.add_block_node(block, pos)

    def connect_selected_nodes(self):
        nodes = self.scene.selected_nodes()
        if len(nodes) != 2:
            return False
        nodes = sorted(nodes, key=lambda node: node.scenePos().x())
        self.scene.create_connection(nodes[0], nodes[1])
        return True

    def load_demo_workflow(self):
        self.scene.clear_workflow()
        positions = {
            "injection": QPointF(-420, -40),
            "functional": QPointF(-120, -40),
            "propagation": QPointF(180, -40),
            "reliability": QPointF(480, -40),
        }
        created = {}
        for node_id, pos in positions.items():
            created[node_id] = self.scene.add_block_node(self.nodes[node_id], pos)
            created[node_id].setSelected(False)
        self.scene.create_connection(created["injection"], created["functional"])
        self.scene.create_connection(created["functional"], created["propagation"])
        self.scene.create_connection(created["propagation"], created["reliability"])
        self.view.fit_all()

    def reset_view(self):
        self.load_demo_workflow()
