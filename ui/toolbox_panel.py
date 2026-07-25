from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


METHOD_LIBRARY = {
    "quantification": {
        "title": "不确定因素量化",
        "items": ["概率模型", "区间模型", "模糊模型", "证据理论"],
        "color": "#1D4ED8",
    },
    "propagation": {
        "title": "不确定性传播建模",
        "items": ["代理模型", "混合不确定性传播模型", "概率传播模型", "区间传播模型"],
        "color": "#D97706",
    },
    "analysis": {
        "title": "不确定性分析",
        "items": ["概率响应", "区间响应", "模糊响应", "可靠性指标"],
        "color": "#7C3AED",
    },
}


class ToolboxPanel(QWidget):
    method_selected = Signal(str, str)
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(330)
        self._buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QScrollArea, QWidget {
                background: #EEF4FA;
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

        title = QLabel("方法流程总览")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #0F172A;")
        layout.addWidget(title)

        subtitle = QLabel("纵向展示方法流程，横向联动阶段对象。点击左侧方法可高亮对应矩阵行。")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #486581; font-size: 13px; line-height: 1.45;")
        layout.addWidget(subtitle)

        for key, section in METHOD_LIBRARY.items():
            group = QGroupBox(section["title"])
            group.setStyleSheet(
                f"""
                QGroupBox {{
                    font-size: 15px;
                    font-weight: 700;
                    color: {section['color']};
                    border: 1px solid #DCE8F3;
                    border-radius: 18px;
                    margin-top: 10px;
                    background: rgba(255, 255, 255, 0.94);
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

            head_btn = self._create_button(section["title"], key, section["title"], large=True)
            head_btn.setStyleSheet(self._button_style(section["color"], large=True))
            group_layout.addWidget(head_btn)

            for item in section["items"]:
                btn = self._create_button(item, key, item)
                btn.setStyleSheet(self._button_style(section["color"], large=False))
                group_layout.addWidget(btn)

            layout.addWidget(group)

        quick_group = QGroupBox("展示控制")
        quick_group.setStyleSheet(
            """
            QGroupBox {
                font-size: 15px;
                font-weight: 700;
                color: #0F172A;
                border: 1px solid #DCE8F3;
                border-radius: 18px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.94);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            """
        )
        quick_layout = QVBoxLayout(quick_group)
        quick_layout.setContentsMargins(14, 18, 14, 14)
        quick_layout.setSpacing(12)

        reset_btn = QPushButton("重置展示视图")
        reset_btn.setMinimumHeight(48)
        reset_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0284C7, stop:1 #38BDF8
                );
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 700;
                padding: 10px 14px;
            }
            QPushButton:hover { background: #0369A1; }
            """
        )
        reset_btn.clicked.connect(self.reset_requested.emit)
        quick_layout.addWidget(reset_btn)

        help_text = QLabel(
            "建议汇报路径：先点阶段，再看对象矩阵，最后点击运行传播查看下方曲线和对比图。"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #52606D; font-size: 13px;")
        quick_layout.addWidget(help_text)
        layout.addWidget(quick_group)
        layout.addStretch()

    def _create_button(self, text, key, label, large=False):
        btn = QPushButton(text)
        btn.setMinimumHeight(52 if large else 44)
        btn.clicked.connect(lambda: self.method_selected.emit(key, label))
        self._buttons[(key, label)] = btn
        return btn

    @staticmethod
    def _button_style(color, large):
        size = 15 if large else 14
        pad = "12px 14px" if large else "10px 12px"
        return f"""
            QPushButton {{
                text-align: left;
                background: rgba(248, 250, 252, 0.95);
                color: #102A43;
                border: 1px solid #D9E2EC;
                border-radius: 14px;
                font-size: {size}px;
                font-weight: 600;
                padding: {pad};
            }}
            QPushButton:hover {{
                border-color: {color};
                background: white;
            }}
        """
