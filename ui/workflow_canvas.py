import json

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QFont, QKeySequence, QPainter, QPainterPath, QPen, QShortcut
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QInputDialog,
    QMenu,
    QVBoxLayout,
    QWidget,
)


WORKFLOW_MIME = "application/x-uq-workflow-payload"

STAGE_COLORS = {
    "设计": "#2F73D8",
    "制造": "#24A66A",
    "试验": "#E77832",
    "服役": "#8362D6",
    "零部件": "#0EA5A4",
    "组件": "#14B8A6",
    "子系统": "#06B6D4",
    "系统": "#0284C7",
    "装备": "#2563EB",
    "模型": "#64748B",
    "不确定性分析": "#22A7B8",
}


STAGE_BLOCKS = [
    {
        "code": "A",
        "title": "设计",
        "scope": "设计阶段",
        "rows": ["基本信息", "几何模型", "材料参数", "载荷 / 边界条件", "不确定性定义", "功能模型分析", "可靠性评价"],
    },
    {
        "code": "B",
        "title": "制造",
        "scope": "制造阶段",
        "rows": ["基本信息", "工艺参数", "材料状态", "边界条件", "不确定性定义", "制造仿真分析", "可靠性评价"],
    },
    {
        "code": "C",
        "title": "试验",
        "scope": "试验阶段",
        "rows": ["基本信息", "试验对象", "试验设置", "测量与数据", "不确定性定义", "数据处理 / 校准", "可靠性评价"],
    },
    {
        "code": "D",
        "title": "服役",
        "scope": "服役阶段",
        "rows": ["基本信息", "服役工况", "环境条件", "初始状态", "不确定性定义", "寿命 / 可靠性分析", "结果数据"],
    },
]


LEVEL_BLOCKS = [
    {
        "code": "L1",
        "title": "零部件",
        "scope": "零部件",
        "rows": ["基本信息", "功能性能模型", "不确定性定义", "传播模型", "零组件可靠性评价", "结果数据"],
    },
    {
        "code": "L2",
        "title": "组件",
        "scope": "组件",
        "rows": ["基本信息", "组件接口", "不确定性汇聚", "传播模型", "组件可靠性评价", "结果数据"],
    },
    {
        "code": "L3",
        "title": "子系统",
        "scope": "子系统",
        "rows": ["基本信息", "子系统结构", "不确定性汇聚", "传播模型", "系统可靠性模型", "结果数据"],
    },
    {
        "code": "L4",
        "title": "系统",
        "scope": "系统",
        "rows": ["基本信息", "系统结构", "跨层级参数", "传播模型", "系统可靠性评价", "结果数据"],
    },
    {
        "code": "L5",
        "title": "装备",
        "scope": "装备",
        "rows": ["基本信息", "任务剖面", "环境 / 工况", "不确定性传播", "装备可靠性评价", "结果数据"],
    },
]


ROW_CATEGORY_KEYWORDS = [
    ("功能", "功能性能模型"),
    ("仿真", "功能性能模型"),
    ("不确定", "不确定性传播模型"),
    ("传播", "不确定性传播模型"),
    ("零组件可靠", "零组件可靠性模型"),
    ("可靠", "系统可靠性模型"),
]


class SubItemPort:
    def __init__(self, block, row_index, side):
        self.block = block
        self.row_index = row_index
        self.side = side

    @property
    def node(self):
        return self.block

    def get_scene_pos(self):
        return self.block.port_scene_pos(self.row_index, self.side)


class WorkbenchBlock(QGraphicsItem):
    def __init__(self, block_data):
        super().__init__()
        self.data = block_data
        self.width = 228
        self.header_height = 48
        self.row_height = 37
        self.footer_height = 34
        self.height = self.header_height + len(self.data["rows"]) * self.row_height + self.footer_height
        self.selected_row = None
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

    def boundingRect(self):
        return QRectF(-8, -8, self.width + 16, self.height + 16)

    def row_rect(self, row_index):
        y = self.header_height + row_index * self.row_height
        return QRectF(0, y, self.width, self.row_height)

    def port_scene_pos(self, row_index, side):
        rect = self.row_rect(row_index)
        x = 0 if side == "in" else self.width
        return self.mapToScene(QPointF(x, rect.center().y()))

    def port_at_scene_pos(self, scene_pos, radius=10):
        local = self.mapFromScene(scene_pos)
        for index in range(len(self.data["rows"])):
            for side in ("in", "out"):
                port_pos = self.mapFromScene(self.port_scene_pos(index, side))
                if (local - port_pos).manhattanLength() <= radius:
                    return SubItemPort(self, index, side)
        return None

    def row_payload(self, row_index):
        row_name = self.data["rows"][row_index]
        if self.data.get("kind") == "model":
            return self._model_payload(row_name, row_index)
        category = self._category_for_row(row_name)
        scope = self.data.get("scope", self.data["title"])
        catalog = self.data.get("catalog", {}).get(scope, {})
        model_options = []
        if category:
            model_options = catalog.get(category, [])
        return {
            "title": f"{self.data['title']} - {row_index + 1} {row_name}",
            "param_name": row_name,
            "var_type": "随机变量" if "不确定" in row_name or "材料" in row_name else "区间变量",
            "dist_type": "Normal" if "材料" in row_name or "不确定" in row_name else "Interval",
            "mean": "210000" if "材料" in row_name else "",
            "std": "10000" if "材料" in row_name else "",
            "source": "材料测试" if "材料" in row_name else "模型/阶段输入",
            "model_options": model_options,
            "model_catalog": catalog,
            "config_context": {
                "workflow": self.data.get("workflow", ""),
                "scope": scope,
                "category": category or row_name,
            },
            "io": [
                ("输入", "关键输入参数", f"{self.data['title']}阶段：{row_name}的输入"),
                ("输出", "关键输出参数", f"{row_name}输出给下游子项"),
            ],
            "mapping": [
                (f"{self.data['title']}-{row_name}", "下游子项", "参数/响应/可靠性结果"),
            ],
        }

    def block_payload(self):
        if self.data.get("kind") == "model":
            return self._model_payload(self.data["title"], None)
        scope = self.data.get("scope", self.data["title"])
        catalog = self.data.get("catalog", {}).get(scope, {})
        model_options = []
        for category, models in catalog.items():
            for model in models:
                model_options.append({**model, "category": category})
        return {
            "title": self.data.get("label", self.data["title"]),
            "param_name": self.data.get("label", self.data["title"]),
            "source": "模型树",
            "model_options": model_options,
            "model_catalog": catalog,
            "config_context": {
                "workflow": self.data.get("workflow", ""),
                "scope": scope,
                "category": model_options[0].get("category", "节点总体配置") if model_options else "节点总体配置",
            },
            "io": [
                ("输入", "上游阶段或层级数据", "作为阶段块输入"),
                ("输出", "阶段结果数据", "供下游阶段或层级使用"),
            ],
            "mapping": [
                (self.data.get("label", self.data["title"]), "下一阶段", "结果数据与不确定性参数"),
            ],
        }

    def _category_for_row(self, row_name):
        for keyword, category in ROW_CATEGORY_KEYWORDS:
            if keyword in row_name:
                return category
        return ""

    def _model_payload(self, row_name, row_index):
        title = self.data["title"] if row_index is None else f"{self.data['title']} - {row_index + 1} {row_name}"
        return {
            "title": title,
            "param_name": self.data.get("model_name", self.data["title"]),
            "model_id": self.data.get("model_id", ""),
            "var_type": "随机变量" if "不确定" in self.data.get("category", "") else "区间变量",
            "dist_type": "Normal" if "不确定" in self.data.get("category", "") else "Interval",
            "mean": "",
            "std": "",
            "source": "画布拖拽模型",
            "model_options": self.data.get("model_options", []),
            "io": [
                ("输入", self.data.get("inputs") or "关键输入参数", "模型输入定义"),
                ("输出", self.data.get("outputs") or "关键输出参数", "模型输出定义"),
            ],
            "mapping": [
                (self.data["title"], "下游流程子项", row_name if row_index is not None else "模型输入输出参数"),
            ],
        }

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(STAGE_COLORS.get(self.data["title"], "#2F73D8"))
        border = color if self.isSelected() else QColor("#D8E1EE")
        painter.setPen(QPen(border, 2 if self.isSelected() else 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(0, 0, self.width, self.height, 8, 8)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color.lighter(175)))
        painter.drawRoundedRect(0, 0, self.width, self.header_height, 8, 8)
        painter.drawRect(0, self.header_height - 8, self.width, 8)

        painter.setPen(QPen(QColor("#102A43")))
        painter.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        painter.drawText(QRectF(12, 0, self.width - 24, self.header_height), Qt.AlignmentFlag.AlignVCenter, f"{self.data['code']}  {self.data.get('label', self.data['title'])}")

        painter.setFont(QFont("Microsoft YaHei", 9))
        for index, row in enumerate(self.data["rows"]):
            rect = self.row_rect(index)
            if index == self.selected_row:
                painter.fillRect(rect.adjusted(1, 1, -1, -1), QColor("#DBEAFE"))
            painter.setPen(QPen(QColor("#E2E8F0")))
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            painter.setPen(QPen(QColor("#64748B")))
            painter.drawRoundedRect(rect.x() + 10, rect.y() + 8, 22, 22, 4, 4)
            painter.drawText(QRectF(rect.x() + 10, rect.y(), 22, rect.height()), Qt.AlignmentFlag.AlignCenter, str(index + 1))
            painter.setPen(QPen(QColor("#102A43")))
            painter.drawText(QRectF(rect.x() + 42, rect.y(), self.width - 70, rect.height()), Qt.AlignmentFlag.AlignVCenter, row)
            self._draw_port(painter, index, "in", color)
            self._draw_port(painter, index, "out", color)

        painter.setPen(QPen(QColor("#CBD5E1")))
        footer_top = self.header_height + len(self.data["rows"]) * self.row_height
        painter.drawLine(0, footer_top, self.width, footer_top)
        painter.setPen(QPen(QColor("#64748B")))
        painter.setFont(QFont("Microsoft YaHei", 8))
        footer_text = f"标签：{self.data.get('label', self.data['title'])}  |  双击修改"
        painter.drawText(QRectF(6, footer_top, self.width - 12, self.footer_height), Qt.AlignmentFlag.AlignCenter, footer_text)

    def _draw_port(self, painter, row_index, side, color):
        pos = self.port_scene_pos(row_index, side)
        local = self.mapFromScene(pos)
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawEllipse(local, 5, 5)

    def mousePressEvent(self, event):
        self.selected_row = None
        for index in range(len(self.data["rows"])):
            if self.row_rect(index).contains(event.pos()):
                self.selected_row = index
                break
        self.update()
        scene = self.scene()
        if hasattr(scene, "emit_block_selection"):
            scene.emit_block_selection(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self._update_attached_connections()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._update_attached_connections()

    def mouseDoubleClickEvent(self, event):
        footer_top = self.header_height + len(self.data["rows"]) * self.row_height
        if event.pos().y() >= footer_top:
            old_label = self.data.get("label", self.data["title"])
            label, ok = QInputDialog.getText(None, "修改标签", "请输入部件标签：", text=old_label)
            if ok and label.strip():
                self.data["label"] = label.strip()
                self.update()
                scene = self.scene()
                if hasattr(scene, "block_label_changed"):
                    scene.block_label_changed.emit(
                        {
                            "workflow": self.data.get("workflow", ""),
                            "scope": self.data.get("scope", self.data["title"]),
                            "old_label": old_label,
                            "new_label": self.data["label"],
                        }
                    )
                if hasattr(scene, "emit_block_selection"):
                    scene.emit_block_selection(self)
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        actions = []
        scope = self.data.get("scope", self.data["title"])
        catalog = self.data.get("catalog", {})
        for category in ["功能性能模型", "不确定性传播模型", "零组件可靠性模型", "系统可靠性模型"]:
            models = catalog.get(scope, {}).get(category, [])
            action = menu.addAction(f"添加{category}")
            action.setEnabled(bool(models))
            actions.append((action, category, models))
        chosen = menu.exec(event.screenPos())
        for action, category, models in actions:
            if chosen == action and models:
                self._configure_model(category, models[0])
                break

    def _configure_model(self, category, model):
        self.data.setdefault("configured_models", {})[category] = model.get("name", "模型")
        payload = {
            "title": f"{self.data.get('label', self.data['title'])} - {category} - {model.get('name', '模型')}",
            "param_name": model.get("name", "模型"),
            "var_type": "随机变量" if "不确定" in category else "区间变量",
            "dist_type": "Normal" if "不确定" in category else "Interval",
            "mean": "",
            "std": "",
            "source": "右键添加模型",
            "model_options": models_to_payloads(self.data.get("catalog", {}).get(self.data.get("scope", ""), {}).get(category, [])),
            "model_catalog": self.data.get("catalog", {}).get(self.data.get("scope", ""), {}),
            "config_context": {
                "workflow": self.data.get("workflow", ""),
                "scope": self.data.get("scope", self.data["title"]),
                "category": category,
            },
            "io": [
                ("输入", model.get("inputs") or "关键输入参数", "模型输入定义"),
                ("输出", model.get("outputs") or "关键输出参数", "模型输出定义"),
            ],
            "mapping": [
                (self.data.get("label", self.data["title"]), model.get("name", "模型"), "添加到节点模型配置"),
            ],
        }
        scene = self.scene()
        if hasattr(scene, "selection_payload_changed"):
            scene.selection_payload_changed.emit(payload)
        if hasattr(scene, "model_configured"):
            scene.model_configured.emit(
                {
                    "context": payload["config_context"],
                    "model_name": payload["param_name"],
                }
            )

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._update_attached_connections()
        return super().itemChange(change, value)

    def _update_attached_connections(self):
        if not self.scene():
            return
        for connection in getattr(self.scene(), "connections", []):
            if connection.start_port.block == self or connection.end_port.block == self:
                connection.update_path()


def models_to_payloads(models):
    payloads = []
    for model in models:
        name = model.get("name", model.get("param_name", "模型"))
        scope = model.get("scope", "")
        category = model.get("category", "模型")
        payloads.append(
            {
                "title": f"{scope} - {category} - {name}",
                "param_name": name,
                "model_id": model.get("model_id", ""),
                "var_type": "随机变量" if "不确定" in category else "区间变量",
                "dist_type": "Normal" if "不确定" in category else "Interval",
                "mean": "",
                "std": "",
                "source": "跨层级跨阶段模型输入输出表",
                "io": [
                    ("输入", model.get("inputs") or "关键输入参数", "模型输入定义"),
                    ("输出", model.get("outputs") or "关键输出参数", "模型输出定义"),
                ],
                "mapping": [(f"{scope} - {category} - {name}", "画布节点", "模型配置")],
            }
        )
    return payloads


class WorkbenchConnection(QGraphicsPathItem):
    def __init__(self, start_port, end_port, color="#2F73D8", dashed=False):
        super().__init__()
        self.start_port = start_port
        self.end_port = end_port
        self.color = QColor(color)
        self.dashed = dashed
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.update_path()

    def update_path(self):
        start = self.start_port.get_scene_pos()
        end = self.end_port.get_scene_pos()
        dx = max(80, abs(end.x() - start.x()) * 0.45)
        path = QPainterPath(start)
        path.cubicTo(QPointF(start.x() + dx, start.y()), QPointF(end.x() - dx, end.y()), end)
        self.setPath(path)
        self.update()

    def paint(self, painter, option, widget=None):
        pen = QPen(QColor("#DC2626") if self.isSelected() else self.color, 3 if self.isSelected() else 2)
        if self.dashed:
            pen.setStyle(Qt.PenStyle.DashLine)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.drawPath(self.path())

    def payload(self):
        return {
            "title": "子项连接",
            "param_name": "连接映射",
            "source": "画布连线",
            "io": [
                ("输出", self.start_port.block.data["rows"][self.start_port.row_index], "来源子项"),
                ("输入", self.end_port.block.data["rows"][self.end_port.row_index], "目标子项"),
            ],
            "mapping": [
                (
                    f"{self.start_port.block.data['title']}-{self.start_port.block.data['rows'][self.start_port.row_index]}",
                    f"{self.end_port.block.data['title']}-{self.end_port.block.data['rows'][self.end_port.row_index]}",
                    "关键输入/输出参数",
                )
            ],
        }


class WorkbenchScene(QGraphicsScene):
    selection_payload_changed = Signal(object)
    block_label_changed = Signal(dict)
    model_configured = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setSceneRect(QRectF(-1200, -700, 2400, 1400))
        self.connections = []
        self.selectionChanged.connect(self._emit_selection)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor("#F6F8FB"))
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        grid = 28
        left = int(rect.left()) - int(rect.left()) % grid
        top = int(rect.top()) - int(rect.top()) % grid
        x = left
        while x < rect.right():
            painter.drawLine(x, rect.top(), x, rect.bottom())
            x += grid
        y = top
        while y < rect.bottom():
            painter.drawLine(rect.left(), y, rect.right(), y)
            y += grid

    def emit_block_selection(self, block):
        payload = block.row_payload(block.selected_row) if block.selected_row is not None else block.block_payload()
        self.selection_payload_changed.emit(payload)

    def _emit_selection(self):
        selected = self.selectedItems()
        if len(selected) == 1 and isinstance(selected[0], WorkbenchConnection):
            self.selection_payload_changed.emit(selected[0].payload())
        elif len(selected) == 1 and isinstance(selected[0], WorkbenchBlock):
            self.emit_block_selection(selected[0])
        elif not selected:
            self.selection_payload_changed.emit(None)

    def add_connection(self, connection):
        self.connections.append(connection)
        self.addItem(connection)

    def delete_selected_items(self):
        selected = list(self.selectedItems())
        if not selected:
            return False

        items_to_remove = set()
        for item in selected:
            if isinstance(item, WorkbenchBlock):
                for connection in list(self.connections):
                    if connection.start_port.block == item or connection.end_port.block == item:
                        items_to_remove.add(connection)
                items_to_remove.add(item)
            elif isinstance(item, WorkbenchConnection):
                items_to_remove.add(item)

        for item in items_to_remove:
            if isinstance(item, WorkbenchConnection) and item in self.connections:
                self.connections.remove(item)
            self.removeItem(item)

        self.selection_payload_changed.emit(None)
        return True

    def create_connection_between_ports(self, first_port, second_port):
        if not first_port or not second_port or first_port.block == second_port.block:
            return None
        if first_port.side == second_port.side:
            return None

        start_port = first_port if first_port.side == "out" else second_port
        end_port = second_port if second_port.side == "in" else first_port
        for connection in self.connections:
            if (
                connection.start_port.block == start_port.block
                and connection.start_port.row_index == start_port.row_index
                and connection.end_port.block == end_port.block
                and connection.end_port.row_index == end_port.row_index
            ):
                return connection

        color = STAGE_COLORS.get(start_port.block.data["title"], "#2F73D8")
        connection = WorkbenchConnection(start_port, end_port, color)
        self.add_connection(connection)
        self.clearSelection()
        connection.setSelected(True)
        self.selection_payload_changed.emit(connection.payload())
        return connection


class WorkbenchView(QGraphicsView):
    item_dropped = Signal(dict)

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self._is_panning = False
        self._pan_start = None
        self._pan_h = 0
        self._pan_v = 0
        self._zoom = 1.0
        self._start_port = None
        self._preview_connection = None
        self.setAcceptDrops(True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self)
        delete_shortcut.activated.connect(self._delete_selected)
        backspace_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
        backspace_shortcut.activated.connect(self._delete_selected)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(WORKFLOW_MIME):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(WORKFLOW_MIME):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(WORKFLOW_MIME):
            raw = bytes(event.mimeData().data(WORKFLOW_MIME)).decode("utf-8")
            payload = json.loads(raw)
            self.item_dropped.emit({"payload": payload, "pos": self.mapToScene(event.position().toPoint())})
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self._is_panning = True
            self._pan_start = event.position().toPoint()
            self._pan_h = self.horizontalScrollBar().value()
            self._pan_v = self.verticalScrollBar().value()
            self.viewport().setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            port = self._port_at_view_pos(event.position().toPoint())
            if port:
                self._start_port = port
                self._preview_connection = QGraphicsPathItem()
                self._preview_connection.setZValue(-0.5)
                self._preview_connection.setPen(QPen(QColor("#64748B"), 2, Qt.PenStyle.DashLine))
                self.scene().addItem(self._preview_connection)
                self._update_preview_connection(self.mapToScene(event.position().toPoint()))
                self.viewport().setCursor(QCursor(Qt.CursorShape.CrossCursor))
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_port and self._preview_connection:
            self._update_preview_connection(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        if self._is_panning and self._pan_start is not None:
            delta = event.position().toPoint() - self._pan_start
            self.horizontalScrollBar().setValue(self._pan_h - delta.x())
            self.verticalScrollBar().setValue(self._pan_v - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._start_port:
            end_port = self._port_at_view_pos(event.position().toPoint())
            if self._preview_connection:
                self.scene().removeItem(self._preview_connection)
                self._preview_connection = None
            if hasattr(self.scene(), "create_connection_between_ports"):
                self.scene().create_connection_between_ports(self._start_port, end_port)
            self._start_port = None
            self.viewport().unsetCursor()
            event.accept()
            return
        if self._is_panning:
            self._is_panning = False
            self._pan_start = None
            self.viewport().unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.zoom_by(factor)
            event.accept()
            return
        super().wheelEvent(event)

    def zoom_by(self, factor):
        next_zoom = self._zoom * factor
        if not 0.35 <= next_zoom <= 2.8:
            return
        self._zoom = next_zoom
        self.scale(factor, factor)

    def zoom_in(self):
        self.zoom_by(1.18)

    def zoom_out(self):
        self.zoom_by(1 / 1.18)

    def reset_zoom(self):
        self.resetTransform()
        self._zoom = 1.0

    def fit_all(self):
        rect = self.scene().itemsBoundingRect().adjusted(-120, -90, 120, 170)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = self.transform().m11()

    def _port_at_view_pos(self, view_pos):
        scene_pos = self.mapToScene(view_pos)
        for item in self.scene().items(scene_pos):
            block = item if isinstance(item, WorkbenchBlock) else None
            if block:
                port = block.port_at_scene_pos(scene_pos)
                if port:
                    return port
        for item in self.scene().items():
            if isinstance(item, WorkbenchBlock):
                port = item.port_at_scene_pos(scene_pos)
                if port:
                    return port
        return None

    def _update_preview_connection(self, end_pos):
        start = self._start_port.get_scene_pos()
        dx = max(80, abs(end_pos.x() - start.x()) * 0.45)
        path = QPainterPath(start)
        path.cubicTo(QPointF(start.x() + dx, start.y()), QPointF(end_pos.x() - dx, end_pos.y()), end_pos)
        self._preview_connection.setPath(path)

    def _delete_selected(self):
        if hasattr(self.scene(), "delete_selected_items"):
            self.scene().delete_selected_items()


class WorkflowCanvas(QWidget):
    selection_changed = Signal(object)
    block_added = Signal(dict)
    block_renamed = Signal(dict)
    model_configured = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = WorkbenchScene()
        self.view = WorkbenchView(self.scene)
        self.blocks = {}
        self.current_workflow = "cross_level"
        self.catalog = {}
        self.scene.selection_payload_changed.connect(self.selection_changed.emit)
        self.scene.block_label_changed.connect(self.block_renamed.emit)
        self.scene.model_configured.connect(self.model_configured.emit)
        self.view.item_dropped.connect(self._on_item_dropped)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view)

    def set_catalog(self, catalog):
        self.catalog = catalog or {}

    def load_demo_workflow(self, workflow=None):
        if workflow:
            self.current_workflow = workflow
        self.scene.clear()
        self.scene.connections = []
        self.blocks = {}
        self.add_route_workflow(self.current_workflow, QPointF(-520, -140))
        self.view.fit_all()

    def clear_workflow(self, workflow=None):
        if workflow:
            self.current_workflow = workflow
        self.scene.clear()
        self.scene.connections = []
        self.blocks = {}
        self.selection_changed.emit(None)

    def add_route_workflow(self, workflow, origin):
        block_defs = STAGE_BLOCKS if workflow == "cross_stage" else LEVEL_BLOCKS
        route_blocks = {}
        for index, block_data in enumerate(block_defs):
            block_data = {
                **block_data,
                "workflow": workflow,
                "label": block_data["title"],
                "catalog": self.catalog.get(workflow, {}),
            }
            block = WorkbenchBlock(block_data)
            self.scene.addItem(block)
            pos = QPointF(origin.x() + index * 290, origin.y())
            block.setPos(pos)
            route_blocks[block_data["title"]] = block
            self.blocks[self._unique_block_key(block_data["title"])] = block
            self.block_added.emit(
                {
                    "workflow": workflow,
                    "scope": block_data.get("scope", block_data["title"]),
                    "label": block_data["label"],
                }
            )

        if workflow == "cross_stage":
            self._connect(route_blocks, "设计", 1, "制造", 1, STAGE_COLORS["设计"])
            self._connect(route_blocks, "设计", 2, "制造", 2, STAGE_COLORS["制造"])
            self._connect(route_blocks, "设计", 4, "制造", 4, STAGE_COLORS["设计"], dashed=True)
            self._connect(route_blocks, "制造", 2, "试验", 2, STAGE_COLORS["制造"], dashed=True)
            self._connect(route_blocks, "制造", 4, "试验", 5, STAGE_COLORS["制造"])
            self._connect(route_blocks, "试验", 1, "服役", 1, STAGE_COLORS["设计"])
            self._connect(route_blocks, "试验", 3, "服役", 3, STAGE_COLORS["试验"], dashed=True)
        else:
            names = [block["title"] for block in LEVEL_BLOCKS]
            for index in range(len(names) - 1):
                self._connect(route_blocks, names[index], 1, names[index + 1], 1, STAGE_COLORS[names[index]])
                self._connect(route_blocks, names[index], 3, names[index + 1], 3, STAGE_COLORS[names[index]], dashed=True)
        return route_blocks

    def add_scope_block(self, payload, pos):
        workflow = payload.get("workflow", self.current_workflow)
        block_defs = STAGE_BLOCKS if workflow == "cross_stage" else LEVEL_BLOCKS
        scope = payload.get("scope", payload.get("name", ""))
        block_data = next(
            (dict(item) for item in block_defs if item.get("scope") == scope or item.get("title") == scope),
            None,
        )
        if block_data is None:
            return None
        block_data.update({"workflow": workflow, "label": block_data["title"], "catalog": self.catalog.get(workflow, {})})
        block = WorkbenchBlock(block_data)
        self.scene.addItem(block)
        block.setPos(pos)
        self.blocks[self._unique_block_key(block_data["title"])] = block
        self.block_added.emit(
            {
                "workflow": workflow,
                "scope": block_data.get("scope", block_data["title"]),
                "label": block_data["label"],
            }
        )
        self.scene.clearSelection()
        block.setSelected(True)
        self.scene.emit_block_selection(block)
        return block

    def add_model_block(self, payload, pos):
        if payload.get("kind") == "category" and payload.get("model_options"):
            model = dict(payload["model_options"][0])
            model["model_options"] = [self._model_payload(option) for option in payload["model_options"]]
        else:
            model = dict(payload)
            if payload.get("model_options"):
                model["model_options"] = [self._model_payload(option) for option in payload["model_options"]]

        block_data = {
            "kind": "model",
            "code": "M",
            "title": model.get("name", payload.get("name", "模型")),
            "model_name": model.get("name", payload.get("name", "模型")),
            "model_id": model.get("model_id", payload.get("model_id", "")),
            "category": model.get("category", payload.get("name", "")),
            "inputs": model.get("inputs", ""),
            "outputs": model.get("outputs", ""),
            "model_options": model.get("model_options", []),
            "rows": ["模型选择", "关键输入参数", "不确定性设置", "算法 / 求解设置", "关键输出参数"],
        }
        block = WorkbenchBlock(block_data)
        self.scene.addItem(block)
        block.setPos(pos)
        self.blocks[self._unique_block_key(block_data["title"])] = block
        self.scene.clearSelection()
        block.setSelected(True)
        self.scene.emit_block_selection(block)
        return block

    def _connect(self, block_map, start_block, start_row, end_block, end_row, color, dashed=False):
        connection = WorkbenchConnection(
            SubItemPort(block_map[start_block], start_row, "out"),
            SubItemPort(block_map[end_block], end_row, "in"),
            color,
            dashed,
        )
        self.scene.add_connection(connection)

    def _on_item_dropped(self, event):
        payload = event["payload"]
        pos = event["pos"]
        if payload.get("kind") == "route":
            self.add_route_workflow(payload.get("workflow", "cross_stage"), pos)
            self.view.fit_all()
        elif payload.get("kind") in {"stage", "level"}:
            self.add_scope_block(payload, pos)

    def _unique_block_key(self, title):
        if title not in self.blocks:
            return title
        index = 2
        while f"{title}#{index}" in self.blocks:
            index += 1
        return f"{title}#{index}"

    def _model_payload(self, payload):
        name = payload.get("name", "模型")
        scope = payload.get("scope", "")
        category = payload.get("category", "模型")
        title = f"{scope} - {category} - {name}"
        return {
            "title": title,
            "param_name": name,
            "model_id": payload.get("model_id", ""),
            "var_type": "随机变量" if "不确定" in category else "区间变量",
            "dist_type": "Normal" if "不确定" in category else "Interval",
            "mean": "",
            "std": "",
            "source": "跨层级跨阶段模型输入输出表",
            "io": [
                ("输入", payload.get("inputs") or "关键输入参数", "模型输入定义"),
                ("输出", payload.get("outputs") or "关键输出参数", "模型输出定义"),
            ],
            "mapping": [
                (title, "画布下游子项", "关键输入/输出参数"),
            ],
        }

    def zoom_in(self):
        self.view.zoom_in()

    def zoom_out(self):
        self.view.zoom_out()

    def reset_zoom(self):
        self.view.reset_zoom()

    def fit_all(self):
        self.view.fit_all()

    def delete_selected(self):
        selected_blocks = {item for item in self.scene.selectedItems() if isinstance(item, WorkbenchBlock)}
        deleted = self.scene.delete_selected_items()
        if deleted and selected_blocks:
            self.blocks = {
                key: block
                for key, block in self.blocks.items()
                if block not in selected_blocks and block.scene() is not None
            }
        return deleted
