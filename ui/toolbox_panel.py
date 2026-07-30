import json

from PySide6.QtCore import QByteArray, QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


LIBRARY_SECTIONS = [
    {
        "key": "functional",
        "title": "功能性模型",
        "color": "#2563EB",
        "description": "覆盖设计、制造、试验、服役四类场景，作为不确定性传播的承载模型。",
        "items": [
            "弹性静力学模型",
            "刚柔耦合动力学模型",
            "机电耦合模型",
            "密封性能分析模型",
            "装配模型",
            "退化模型",
        ],
    },
    {
        "key": "propagation",
        "title": "不确定性传播模型",
        "color": "#D97706",
        "description": "突出参数如何注入、如何传播、如何形成跨阶段响应。",
        "items": [
            "概率传播模型",
            "区间传播模型",
            "概率-区间混合传播模型",
            "随机过程传播模型",
            "随机场传播模型",
            "模糊传播模型",
        ],
    },
    {
        "key": "reliability",
        "title": "可靠性分析模型",
        "color": "#7C3AED",
        "description": "支持零组件级与系统级可靠性分析算法切换。",
        "items": [
            "一次二阶矩模型",
            "响应面模型",
            "蒙特卡洛模型",
            "代理模型",
            "故障树模型",
            "贝叶斯网络模型",
        ],
    },
    {
        "key": "support",
        "title": "支撑模块",
        "color": "#059669",
        "description": "用于参数注入、模型修正、数据闭环和结果评估。",
        "items": [
            "不确定因素注入",
            "参数映射与接口配置",
            "模型修正与贝叶斯校准",
            "敏感性分析",
            "寿命预测与风险评价",
        ],
    },
]


class ToolboxPanel(QWidget):
    section_selected = Signal(str, str)
    item_selected = Signal(dict)
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(360)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #F4F7FB;
                color: #102A43;
                font-family: "Microsoft YaHei";
            }
            """
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(area)

        container = QWidget()
        area.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        title = QLabel("样板库与模块库")
        title.setFont(QFont("Microsoft YaHei", 17, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("左侧按业务语义组织模块。点击模块可在中央高亮链路，并在右侧查看算法与参数配置。")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #52606D; font-size: 13px; line-height: 1.45;")
        layout.addWidget(subtitle)

        for section in LIBRARY_SECTIONS:
            group = QGroupBox(section["title"])
            group.setStyleSheet(
                f"""
                QGroupBox {{
                    font-size: 15px;
                    font-weight: 700;
                    color: {section['color']};
                    border: 1px solid #D9E2EC;
                    border-radius: 18px;
                    margin-top: 10px;
                    background: rgba(255, 255, 255, 0.97);
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                }}
                """
            )
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(14, 18, 14, 14)
            group_layout.setSpacing(10)

            desc = QLabel(section["description"])
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #52606D; font-size: 12px;")
            group_layout.addWidget(desc)

            head_btn = QPushButton("聚焦该类模块")
            head_btn.setMinimumHeight(42)
            head_btn.setStyleSheet(self._button_style(section["color"], accent=True))
            head_btn.clicked.connect(
                lambda checked=False, key=section["key"], title=section["title"]: self.section_selected.emit(key, title)
            )
            group_layout.addWidget(head_btn)

            for item in section["items"]:
                btn = DraggableToolButton(item, section["key"], section["title"])
                btn.setMinimumHeight(42)
                btn.setStyleSheet(self._button_style(section["color"], accent=False))
                btn.set_payload({"section": section["key"], "section_title": section["title"], "item": item})
                btn.clicked.connect(
                    lambda checked=False, payload={"section": section["key"], "section_title": section["title"], "item": item}: self.item_selected.emit(payload)
                )
                group_layout.addWidget(btn)

            layout.addWidget(group)

        helper = QGroupBox("演示控制")
        helper.setStyleSheet(
            """
            QGroupBox {
                font-size: 15px;
                font-weight: 700;
                color: #102A43;
                border: 1px solid #D9E2EC;
                border-radius: 18px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.97);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            """
        )
        helper_layout = QVBoxLayout(helper)
        helper_layout.setContentsMargins(14, 18, 14, 14)
        helper_layout.setSpacing(12)

        reset_btn = QPushButton("恢复默认链路")
        reset_btn.setMinimumHeight(46)
        reset_btn.setStyleSheet(self._button_style("#0F766E", accent=True))
        reset_btn.clicked.connect(self.reset_requested.emit)
        helper_layout.addWidget(reset_btn)

        note = QLabel("建议汇报顺序：先看参数注入，再看传播模型，再落到可靠性分析与模型修正闭环。")
        note.setWordWrap(True)
        note.setStyleSheet("color: #52606D; font-size: 12px;")
        helper_layout.addWidget(note)
        layout.addWidget(helper)
        layout.addStretch()

    @staticmethod
    def _button_style(color, accent):
        if accent:
            return f"""
                QPushButton {{
                    text-align: left;
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 14px;
                    padding: 11px 14px;
                    font-size: 14px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: {color};
                }}
            """
        return f"""
            QPushButton {{
                text-align: left;
                background: #F8FAFC;
                color: #102A43;
                border: 1px solid #D9E2EC;
                border-radius: 14px;
                padding: 10px 12px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {color};
                background: white;
            }}
        """


class DraggableToolButton(QPushButton):
    def __init__(self, text, section_key, section_title, parent=None):
        super().__init__(text, parent)
        self.section_key = section_key
        self.section_title = section_title
        self.payload = None
        self._drag_start = QPoint()

    def set_payload(self, payload):
        self.payload = payload

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return super().mouseMoveEvent(event)
        if (event.position().toPoint() - self._drag_start).manhattanLength() < 10:
            return super().mouseMoveEvent(event)
        if not self.payload:
            return super().mouseMoveEvent(event)

        drag = QDrag(self)
        mime = QMimeData()
        node_id = self._to_node_id(self.payload["item"], self.payload["section"])
        mime.setData(
            "application/x-uq-block",
            QByteArray(json.dumps({"node_id": node_id, "payload": self.payload}, ensure_ascii=False).encode("utf-8")),
        )
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

    @staticmethod
    def _to_node_id(item, section):
        mapping = {
            "support": "injection",
            "functional": "functional",
            "propagation": "propagation",
            "reliability": "reliability",
        }
        item_mapping = {
            "不确定因素注入": "injection",
            "参数映射与接口配置": "injection",
            "模型修正与贝叶斯校准": "reliability",
            "敏感性分析": "reliability",
            "寿命预测与风险评价": "reliability",
        }
        return item_mapping.get(item, mapping.get(section, "propagation"))
