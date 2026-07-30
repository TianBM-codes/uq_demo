import json

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsItem,
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
        self.width = 228
        self.height = 138
        self.title_height = 34
        self.add_input_port("输入")
        self.add_output_port("输出")
        self._apply_fixed_geometry()

        self.title_item.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        self.title_item.setTextWidth(self.width - 24)
        self.title_item.setPos(12, 6)
        self.title_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.title_item.setAcceptHoverEvents(False)

        self.summary_item = QGraphicsTextItem(self)
        self.summary_item.setDefaultTextColor(QColor("#334155"))
        self.summary_item.setFont(QFont("Microsoft YaHei", 8))
        self.summary_item.setTextWidth(self.width - 28)
        self.summary_item.setPos(14, 48)
        self.summary_item.setPlainText(self._fit_summary(block["summary"]))
        self.summary_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.summary_item.setAcceptHoverEvents(False)

        self.footer_item = QGraphicsTextItem(self)
        self.footer_item.setDefaultTextColor(QColor("#64748B"))
        self.footer_item.setFont(QFont("Microsoft YaHei", 8))
        self.footer_item.setTextWidth(self.width - 28)
        self.footer_item.setPos(14, self.height - 30)
        self.footer_item.setPlainText(block["section_title"])
        self.footer_item.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.footer_item.setAcceptHoverEvents(False)

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
        if len(text) > sum(len(line) for line in lines) and lines:
            lines[-1] = lines[-1].rstrip() + "…"
        return "\n".join(lines)

    def _adjust_height(self):
        self._apply_fixed_geometry()

    def _apply_fixed_geometry(self):
        self.height = 138
        if self.input_ports:
            self.input_ports[0].setPos(0, 78)
        if self.output_ports:
            self.output_ports[0].setPos(self.width, 78)

    def _get_title_color(self):
        return QColor(NODE_STYLE[self.block["category"]]["title"])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setSelected(True)
        super().mousePressEvent(event)

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
        painter.drawLine(12, self.height - 36, self.width - 12, self.height - 36)


class WorkflowConnection(Connection):
    def __init__(self, start_port, end_port, payload):
        super().__init__(start_port, end_port)
        self.payload = payload
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self._normal_color = QColor(payload.get("line_color", "#64748B"))
        self._selected_color = QColor("#DC2626")
        self._pen.setColor(self._normal_color)

    def paint(self, painter, option, widget=None):
        self._pen.setWidth(4 if self.isSelected() else 2)
        self._pen.setColor(self._selected_color if self.isSelected() else self._normal_color)
        super().paint(painter, option, widget)


class WorkflowScene(UQGraphicsScene):
    selection_payload_changed = Signal(object)

    def __init__(self):
        super().__init__()
        self.setBackgroundBrush(QBrush(QColor("#F8FBFF")))
        self.selectionChanged.connect(self._emit_selection)

    def add_block_node(self, block, pos):
        node = WorkflowNode(block)
        self.addItem(node)
        node.setPos(pos)
        node.setSelected(True)
        self._emit_selection()
        return node

    def create_connection(self, start_node, end_node, payload):
        if start_node == end_node:
            return None
        for connection in self.connections:
            if connection.start_port.node == start_node and connection.end_port.node == end_node:
                return connection
        connection = WorkflowConnection(start_node.output_ports[0], end_node.input_ports[0], payload)
        self.add_connection(connection)
        self._emit_selection()
        return connection

    def selected_nodes(self):
        return [item for item in self.selectedItems() if isinstance(item, WorkflowNode)]

    def selected_connection(self):
        for item in self.selectedItems():
            if isinstance(item, WorkflowConnection):
                return item
        return None

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
            elif isinstance(item, WorkflowConnection):
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
        connection = self.selected_connection()
        if connection:
            self.selection_payload_changed.emit(connection.payload)
            return

        nodes = self.selected_nodes()
        if len(nodes) == 1:
            self.selection_payload_changed.emit(nodes[0].block)
            return
        if len(nodes) > 1:
            self.selection_payload_changed.emit(
                {
                    "title": "多节点选择",
                    "section_title": "流程编排",
                    "stage_hint": "当前阶段内部流程",
                    "goal": "可以执行“连接选中节点”，建立当前阶段内四个步骤之间的数据流关系。",
                    "inputs": "上游模块输出",
                    "outputs": "下游模块输入",
                    "algorithms": ["建立连接线", "调整模块顺序", "删除或重连"],
                    "config_items": [
                        f"当前选中节点数：{len(nodes)}",
                        "建议先选上游模块，再选下游模块",
                        "跨阶段传递请在左侧“跨阶段设置”中配置",
                    ],
                    "highlight_values": [
                        f"当前连接数：{len(self.connections)}",
                        "模块位置",
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
        self.setDragMode(UQGraphicsView.DragMode.NoDrag)
        self._is_panning = False
        self._pan_start = None
        self._pan_h = 0
        self._pan_v = 0

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self._is_panning = True
            self._pan_start = event.position().toPoint()
            self._pan_h = self.horizontalScrollBar().value()
            self._pan_v = self.verticalScrollBar().value()
            self.viewport().setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if item is None:
                self.setDragMode(UQGraphicsView.DragMode.RubberBandDrag)
            else:
                self.setDragMode(UQGraphicsView.DragMode.NoDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_panning and (
            event.button() == Qt.MouseButton.MiddleButton
            or event.button() == Qt.MouseButton.LeftButton
        ):
            self._is_panning = False
            self._pan_start = None
            self.viewport().unsetCursor()
            event.accept()
            return

        super().mouseReleaseEvent(event)
        self.setDragMode(UQGraphicsView.DragMode.NoDrag)

    def mouseMoveEvent(self, event):
        if self._is_panning and self._pan_start is not None:
            delta = event.position().toPoint() - self._pan_start
            self.horizontalScrollBar().setValue(self._pan_h - delta.x())
            self.verticalScrollBar().setValue(self._pan_v - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)


class WorkflowCanvas(QWidget):
    node_selected = Signal(object)

    def __init__(self, nodes, parent=None):
        super().__init__(parent)
        self.nodes = nodes
        self.scene = WorkflowScene()
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

        title = QLabel("单阶段不确定性传播流程")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        note = QLabel("中央只展示当前阶段内部通用的四步流程：不确定因素注入、模型样板库、不确定性传播建模、可靠性分析与评价。跨阶段传递在左侧单独设置。")
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

        add_demo = QPushButton("加载四步流程")
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
        block = dict(self.nodes[event["payload"]["node_id"]])
        self.scene.add_block_node(block, event["pos"])

    def add_node_by_id(self, node_id, pos=None):
        block = dict(self.nodes[node_id])
        if pos is None:
            center = self.view.mapToScene(self.view.viewport().rect().center())
            pos = QPointF(center.x() - 80, center.y() - 40)
        return self.scene.add_block_node(block, pos)

    def connect_selected_nodes(self):
        nodes = self.scene.selected_nodes()
        if len(nodes) != 2:
            return False
        nodes = sorted(nodes, key=lambda node: node.scenePos().x())
        payload = self._build_connection_payload(nodes[0], nodes[1])
        self.scene.create_connection(nodes[0], nodes[1], payload)
        return True

    def _build_connection_payload(self, start_node, end_node):
        return {
            "title": f"{start_node.block['title']} -> {end_node.block['title']}",
            "section_title": "阶段内流程连接",
            "stage_hint": "当前阶段内部",
            "goal": "建立当前阶段内四个步骤之间的参数流和响应传递关系。",
            "inputs": f"{start_node.block['title']}输出：参数样本、模型响应、传播结果",
            "outputs": f"{end_node.block['title']}输入：本阶段下游分析所需变量",
            "algorithms": ["直接传递", "接口映射", "结果筛选后传递"],
            "config_items": [
                f"来源模块：{start_node.block['title']}",
                f"目标模块：{end_node.block['title']}",
                "跨阶段传递请在左侧单独设置，不在这里配置",
            ],
            "highlight_values": [
                "来源变量",
                "目标变量",
                "接口匹配关系",
            ],
            "line_color": "#64748B",
        }

    def highlight_section(self, section_key):
        for item in self.scene.items():
            if isinstance(item, WorkflowNode) and item.block["category"] == section_key:
                item.setSelected(True)
                self.scene._emit_selection()
                return

    def load_demo_workflow(self):
        self.scene.clear_workflow()
        created = {
            "injection": self.add_node_by_id("injection", QPointF(-460, -30)),
            "functional": self.add_node_by_id("functional", QPointF(-150, -30)),
            "propagation": self.add_node_by_id("propagation", QPointF(160, -30)),
            "reliability": self.add_node_by_id("reliability", QPointF(470, -30)),
        }
        for item in created.values():
            item.setSelected(False)

        self.scene.create_connection(
            created["injection"],
            created["functional"],
            self._build_connection_payload(created["injection"], created["functional"]),
        )
        self.scene.create_connection(
            created["functional"],
            created["propagation"],
            self._build_connection_payload(created["functional"], created["propagation"]),
        )
        self.scene.create_connection(
            created["propagation"],
            created["reliability"],
            self._build_connection_payload(created["propagation"], created["reliability"]),
        )
        self.view.fit_all()

    def reset_view(self):
        self.load_demo_workflow()
