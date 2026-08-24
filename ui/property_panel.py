from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PropertyPanel(QWidget):
    model_configured = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model_options = []
        self._updating_model_combo = False
        self._current_payload = {}
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
                font-size: 14px;
                font-weight: 700;
                color: #102A43;
                border: 1px solid #D9E2EC;
                border-radius: 8px;
                margin-top: 10px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QComboBox {
                min-height: 30px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background: white;
                padding: 4px 8px;
                font-size: 13px;
            }
            QTableWidget {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                gridline-color: #E2E8F0;
                font-size: 12px;
            }
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        root.addWidget(area)

        container = QWidget()
        area.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("详细设置")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        self.current_group = QGroupBox("当前选择")
        current_layout = QVBoxLayout(self.current_group)
        self.current_label = QLabel("请选择画布中的块或子项")
        self.current_label.setWordWrap(True)
        self.current_label.setStyleSheet("font-size: 13px; color: #334E68;")
        current_layout.addWidget(self.current_label)
        layout.addWidget(self.current_group)

        self.basic_group = QGroupBox("参数设置")
        form = QFormLayout(self.basic_group)
        form.setContentsMargins(12, 18, 12, 12)
        form.setVerticalSpacing(9)
        self.model_selector = QComboBox()
        self.model_selector.currentIndexChanged.connect(self._on_model_selected)
        self.param_name = QLineEdit()
        self.var_type = QComboBox()
        self.var_type.addItems(["随机变量", "区间变量", "模糊变量", "随机过程", "随机场"])
        self.dist_type = QComboBox()
        self.dist_type.addItems(["Normal", "Weibull", "Interval", "Empirical", "Gaussian Process"])
        self.mean_value = QLineEdit()
        self.std_value = QLineEdit()
        self.source_value = QLineEdit()
        form.addRow("具体模型", self.model_selector)
        form.addRow("参数名称", self.param_name)
        form.addRow("变量类型", self.var_type)
        form.addRow("分布/算法", self.dist_type)
        form.addRow("均值/中值", self.mean_value)
        form.addRow("标准差/宽度", self.std_value)
        form.addRow("来源", self.source_value)
        layout.addWidget(self.basic_group)

        self.io_group = QGroupBox("输入 / 输出")
        io_layout = QVBoxLayout(self.io_group)
        self.io_table = QTableWidget(0, 3)
        self.io_table.setHorizontalHeaderLabels(["方向", "参数", "说明"])
        self.io_table.verticalHeader().setVisible(False)
        self.io_table.horizontalHeader().setStretchLastSection(True)
        io_layout.addWidget(self.io_table)
        layout.addWidget(self.io_group)

        self.mapping_group = QGroupBox("连接映射")
        mapping_layout = QVBoxLayout(self.mapping_group)
        self.mapping_table = QTableWidget(0, 3)
        self.mapping_table.setHorizontalHeaderLabels(["来源子项", "目标子项", "传递内容"])
        self.mapping_table.verticalHeader().setVisible(False)
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        mapping_layout.addWidget(self.mapping_table)
        layout.addWidget(self.mapping_group)

        layout.addStretch()
        self.show_payload(None)

    def show_payload(self, payload):
        if not payload:
            self._current_payload = {}
            self.current_label.setText("请选择画布中的块或子项")
            self._set_model_options([], "")
            self._set_form({})
            self._fill_io([])
            self._fill_mapping([])
            return

        self._current_payload = dict(payload)
        self._set_model_options(payload.get("model_options", []), payload.get("param_name", ""))
        self.current_label.setText(payload.get("title", payload.get("name", "当前对象")))
        self._set_form(payload)
        self._fill_io(payload.get("io", []))
        self._fill_mapping(payload.get("mapping", []))
        self._emit_configured_model(payload)

    def _set_model_options(self, options, selected_name):
        self._updating_model_combo = True
        self._model_options = [self._normalize_model_option(option) for option in options]
        self.model_selector.clear()
        if self._model_options:
            self.model_selector.setEnabled(True)
            for option in self._model_options:
                self.model_selector.addItem(option.get("param_name", option.get("name", option.get("title", "模型"))), option)
            names = [option.get("param_name", option.get("name", option.get("title", ""))) for option in self._model_options]
            if selected_name in names:
                self.model_selector.setCurrentIndex(names.index(selected_name))
            else:
                self.model_selector.setCurrentIndex(0)
        else:
            self.model_selector.setEnabled(False)
            self.model_selector.addItem("无可切换模型")
        self._updating_model_combo = False

    def _normalize_model_option(self, option):
        option = dict(option)
        name = option.get("param_name", option.get("name", option.get("title", "模型")))
        scope = option.get("scope", "")
        category = option.get("category", "模型")
        option["param_name"] = name
        option.setdefault("title", f"{scope} - {category} - {name}" if scope else name)
        option.setdefault("var_type", "随机变量" if "不确定" in category else "区间变量")
        option.setdefault("dist_type", "Normal" if "不确定" in category else "Interval")
        option.setdefault("source", "跨层级跨阶段模型输入输出表")
        option.setdefault(
            "io",
            [
                ("输入", option.get("inputs") or "关键输入参数", "模型输入定义"),
                ("输出", option.get("outputs") or "关键输出参数", "模型输出定义"),
            ],
        )
        option.setdefault("mapping", [(option["title"], "画布节点", "模型配置")])
        return option

    def _on_model_selected(self, index):
        if self._updating_model_combo or index < 0 or not self._model_options:
            return
        payload = self.model_selector.itemData(index)
        if not payload:
            return
        payload = dict(payload)
        payload["config_context"] = self._current_payload.get("config_context", payload.get("config_context", {}))
        self.current_label.setText(payload.get("title", payload.get("name", "当前对象")))
        self._set_form(payload)
        self._fill_io(payload.get("io", []))
        self._fill_mapping(payload.get("mapping", []))
        self._emit_configured_model(payload)

    def _emit_configured_model(self, payload):
        context = payload.get("config_context", {})
        if not context or not self._model_options:
            return
        self.model_configured.emit(
            {
                "context": context,
                "model_name": payload.get("param_name", payload.get("title", "")),
            }
        )

    def _set_form(self, payload):
        self.param_name.setText(payload.get("param_name", payload.get("title", "")))
        self.mean_value.setText(payload.get("mean", "210000"))
        self.std_value.setText(payload.get("std", "10000"))
        self.source_value.setText(payload.get("source", "材料测试"))
        self.var_type.setCurrentText(payload.get("var_type", "随机变量"))
        self.dist_type.setCurrentText(payload.get("dist_type", "Normal"))

    def _fill_io(self, rows):
        if not rows:
            rows = [
                ("输入", "弹性模量 / 泊松比 / 载荷", "作为本子项计算或传播输入"),
                ("输出", "响应均值 / 响应方差 / 失效概率", "传递给下游子项"),
            ]
        self.io_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.io_table.setItem(row_index, col_index, item)

    def _fill_mapping(self, rows):
        if not rows:
            rows = [
                ("设计-材料参数", "制造-材料状态", "材料参数分布"),
                ("制造-不确定性定义", "试验-数据处理/校准", "偏差与修正系数"),
            ]
        self.mapping_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.mapping_table.setItem(row_index, col_index, item)
