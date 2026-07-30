from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PropertyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(390)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #F4F7FB;
                color: #102A43;
                font-family: "Microsoft YaHei";
            }
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
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("模块配置与算法设置")
        title.setFont(QFont("Microsoft YaHei", 17, QFont.Weight.Bold))
        layout.addWidget(title)

        self.selection_card = QGroupBox("当前对象")
        card_layout = QVBoxLayout(self.selection_card)
        card_layout.setContentsMargins(14, 18, 14, 14)
        card_layout.setSpacing(8)
        self.name_label = QLabel("未选择对象")
        self.name_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.path_label = QLabel("点击左侧模块、跨阶段设置项，或中央流程节点查看配置。")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #52606D; font-size: 13px;")
        card_layout.addWidget(self.name_label)
        card_layout.addWidget(self.path_label)
        layout.addWidget(self.selection_card)

        self.goal_group = QGroupBox("设计意图")
        goal_layout = QVBoxLayout(self.goal_group)
        goal_layout.setContentsMargins(14, 18, 14, 14)
        self.goal_label = QLabel("-")
        self.goal_label.setWordWrap(True)
        self.goal_label.setStyleSheet("color: #334E68; font-size: 13px; line-height: 1.5;")
        goal_layout.addWidget(self.goal_label)
        layout.addWidget(self.goal_group)

        self.io_group = QGroupBox("输入 / 输出")
        io_layout = QVBoxLayout(self.io_group)
        io_layout.setContentsMargins(14, 18, 14, 14)
        self.inputs_label = QLabel("-")
        self.inputs_label.setWordWrap(True)
        self.outputs_label = QLabel("-")
        self.outputs_label.setWordWrap(True)
        io_layout.addWidget(self.inputs_label)
        io_layout.addWidget(self.outputs_label)
        layout.addWidget(self.io_group)

        self.algorithm_group = QGroupBox("算法候选")
        algo_layout = QVBoxLayout(self.algorithm_group)
        algo_layout.setContentsMargins(14, 18, 14, 14)
        algo_layout.setSpacing(10)
        self.algorithm_hint = QLabel("每个块下都可以选择适合的算法类型。")
        self.algorithm_hint.setWordWrap(True)
        self.algorithm_hint.setStyleSheet("color: #52606D; font-size: 12px;")
        algo_layout.addWidget(self.algorithm_hint)
        self.algorithm_list = QVBoxLayout()
        self.algorithm_list.setSpacing(8)
        algo_layout.addLayout(self.algorithm_list)
        layout.addWidget(self.algorithm_group)

        self.config_group = QGroupBox("建议配置项")
        config_layout = QVBoxLayout(self.config_group)
        config_layout.setContentsMargins(14, 18, 14, 14)
        self.config_label = QLabel("-")
        self.config_label.setWordWrap(True)
        self.config_label.setStyleSheet("color: #334E68; font-size: 13px; line-height: 1.55;")
        config_layout.addWidget(self.config_label)
        layout.addWidget(self.config_group)

        self.value_group = QGroupBox("界面上要强调的值")
        value_layout = QVBoxLayout(self.value_group)
        value_layout.setContentsMargins(14, 18, 14, 14)
        self.value_label = QLabel("-")
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet("color: #334E68; font-size: 13px; line-height: 1.55;")
        value_layout.addWidget(self.value_label)
        layout.addWidget(self.value_group)

        self.mapping_group = QGroupBox("跨阶段传递设置")
        mapping_layout = QVBoxLayout(self.mapping_group)
        mapping_layout.setContentsMargins(14, 18, 14, 14)
        self.mapping_label = QLabel("选择左侧跨阶段设置项后，这里显示阶段之间的来源参数与目标参数映射。")
        self.mapping_label.setWordWrap(True)
        self.mapping_label.setStyleSheet("color: #334E68; font-size: 13px; line-height: 1.55;")
        mapping_layout.addWidget(self.mapping_label)
        layout.addWidget(self.mapping_group)
        layout.addStretch()
        self.mapping_group.hide()

    def set_block(self, block):
        self.name_label.setText(block["title"])
        self.path_label.setText(f"{block['section_title']} / {block['stage_hint']}")
        self.goal_label.setText(block["goal"])
        self.inputs_label.setText(f"输入：{block['inputs']}")
        self.outputs_label.setText(f"输出：{block['outputs']}")
        self.config_label.setText("；\n".join(block["config_items"]))
        self.value_label.setText("；\n".join(block["highlight_values"]))

        while self.algorithm_list.count():
            item = self.algorithm_list.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for index, algorithm in enumerate(block["algorithms"]):
            row = QFrame()
            row.setStyleSheet(
                """
                QFrame {
                    background: #F8FAFC;
                    border: 1px solid #E2E8F0;
                    border-radius: 14px;
                }
                """
            )
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(10)

            tag = QLabel("推荐" if index == 0 else "可选")
            tag.setStyleSheet(
                """
                background: #DBEAFE;
                color: #1D4ED8;
                border-radius: 10px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 700;
                """
            )
            name = QLabel(algorithm)
            name.setWordWrap(True)
            name.setStyleSheet("font-size: 13px; font-weight: 600; color: #102A43;")
            row_layout.addWidget(tag)
            row_layout.addWidget(name, 1)
            self.algorithm_list.addWidget(row)

        mapping_rows = block.get("mapping_rows")
        if mapping_rows:
            self.mapping_group.show()
            self.mapping_label.setText("；\n".join(mapping_rows))
        else:
            self.mapping_group.hide()
            self.mapping_label.setText("选择左侧跨阶段设置项后，这里显示阶段之间的来源参数与目标参数映射。")
