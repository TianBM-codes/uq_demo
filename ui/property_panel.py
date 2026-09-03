from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
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
        self._model_catalog = {}
        self._updating_model_combo = False
        self._updating_category_combo = False
        self._current_payload = {}
        self._qbhk_fields = {}
        self._uq_fields = {}
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
        self.category_selector = QComboBox()
        self.category_selector.currentIndexChanged.connect(self._on_category_selected)
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
        form.addRow("模型类别", self.category_selector)
        form.addRow("具体模型", self.model_selector)
        form.addRow("参数名称", self.param_name)
        form.addRow("变量类型", self.var_type)
        form.addRow("分布/算法", self.dist_type)
        form.addRow("均值/中值", self.mean_value)
        form.addRow("标准差/宽度", self.std_value)
        form.addRow("来源", self.source_value)
        layout.addWidget(self.basic_group)

        self.qbhk_group = QGroupBox("曲柄滑块动力学模型")
        qbhk_layout = QFormLayout(self.qbhk_group)
        qbhk_layout.setContentsMargins(12, 18, 12, 12)
        qbhk_layout.setVerticalSpacing(9)
        for key, label, value in [
            ("E", "弹性模量 E (Pa)", "2e9"),
            ("L1", "曲柄长度 L1 (m)", "0.2"),
            ("L2", "连杆长度 L2 (m)", "0.6"),
            ("rho", "密度 rho (kg/m3)", "7850"),
            ("d", "截面直径 d (m)", "0.02"),
            ("g", "重力 g (m/s2)", "9.81"),
            ("m_slider", "滑块质量 (kg)", "0.5"),
            ("omega", "角速度 omega (rad/s)", "3.1415926"),
            ("F", "滑块外力 F (N)", "-10"),
            ("T", "总时间 T (s)", "1"),
            ("dt", "时间步长 dt (s)", "0.01"),
            ("Ne", "ANCF 单元数 Ne", "4"),
            ("alpha_m", "alpha_m", "0.2"),
            ("alpha_f", "alpha_f", "0.4"),
            ("tol", "残差容差", "1e-6"),
            ("max_iter", "最大迭代次数", "15"),
        ]:
            edit = QLineEdit(value)
            self._qbhk_fields[key] = edit
            qbhk_layout.addRow(label, edit)
        layout.addWidget(self.qbhk_group)

        self.uq_group = QGroupBox("不确定性传播")
        uq_layout = QVBoxLayout(self.uq_group)
        self.enable_uq = QCheckBox("启用 Monte Carlo 不确定性传播")
        self.enable_uq.setChecked(True)
        uq_layout.addWidget(self.enable_uq)
        count_row = QFormLayout()
        self.sample_count = QSpinBox()
        self.sample_count.setRange(1, 500)
        self.sample_count.setValue(5)
        count_row.addRow("样本数", self.sample_count)
        uq_layout.addLayout(count_row)
        self.uq_table = QTableWidget(0, 5)
        self.uq_table.setHorizontalHeaderLabels(["启用", "变量", "分布", "均值", "标准差"])
        self.uq_table.verticalHeader().setVisible(False)
        self.uq_table.horizontalHeader().setStretchLastSection(True)
        uq_layout.addWidget(self.uq_table)
        self._fill_uq_defaults()
        layout.addWidget(self.uq_group)

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
            self._set_model_catalog({}, "", "")
            self._set_form({})
            self._set_qbhk_visible(False)
            self._fill_io([])
            self._fill_mapping([])
            return

        self._current_payload = dict(payload)
        self._set_model_catalog(
            payload.get("model_catalog", {}),
            payload.get("config_context", {}).get("category", ""),
            payload.get("param_name", ""),
            payload.get("model_options", []),
        )
        self.current_label.setText(payload.get("title", payload.get("name", "当前对象")))
        self._set_form(payload)
        self._set_qbhk_visible(self._is_qbhk_payload(payload))
        self._fill_io(payload.get("io", []))
        self._fill_mapping(payload.get("mapping", []))

    def _set_model_catalog(self, catalog, selected_category, selected_name, fallback_options=None):
        self._updating_category_combo = True
        self._model_catalog = {
            category: [self._normalize_model_option(option) for option in options]
            for category, options in (catalog or {}).items()
            if options
        }
        if not self._model_catalog and fallback_options:
            fallback = [self._normalize_model_option(option) for option in fallback_options]
            for option in fallback:
                self._model_catalog.setdefault(option.get("category", "模型"), []).append(option)

        self.category_selector.clear()
        if self._model_catalog:
            self.category_selector.setEnabled(True)
            for category in self._model_catalog:
                self.category_selector.addItem(category)
            if selected_category in self._model_catalog:
                self.category_selector.setCurrentText(selected_category)
            else:
                self.category_selector.setCurrentIndex(0)
        else:
            self.category_selector.setEnabled(False)
            self.category_selector.addItem("无可切换类别")
        self._updating_category_combo = False

        current_category = self.category_selector.currentText() if self._model_catalog else ""
        self._set_model_options(self._model_catalog.get(current_category, []), selected_name)

    def _set_model_options(self, options, selected_name):
        self._updating_model_combo = True
        self._model_options = [self._normalize_model_option(option) for option in options]
        self.model_selector.clear()
        if self._model_options:
            self.model_selector.setEnabled(True)
            for option in self._model_options:
                self.model_selector.addItem(self._model_display_text(option), option)
            names = [option.get("param_name", option.get("name", option.get("title", ""))) for option in self._model_options]
            if selected_name in names:
                self.model_selector.setCurrentIndex(names.index(selected_name))
            else:
                self.model_selector.setCurrentIndex(0)
        else:
            self.model_selector.setEnabled(False)
            self.model_selector.addItem("无可切换模型")
        self._updating_model_combo = False

    def _on_category_selected(self, index):
        if self._updating_category_combo or index < 0:
            return
        category = self.category_selector.currentText()
        self._set_model_options(self._model_catalog.get(category, []), "")
        if self._model_options:
            self._on_model_selected(self.model_selector.currentIndex())

    def _normalize_model_option(self, option):
        option = dict(option)
        name = option.get("param_name", option.get("name", option.get("title", "模型")))
        scope = option.get("scope", "")
        category = option.get("category", "模型")
        option["param_name"] = name
        option.setdefault("title", f"{scope} - {category} - {name}" if scope else name)
        option.setdefault(
            "config_context",
            {
                "workflow": option.get("workflow", ""),
                "scope": scope,
                "category": category,
            },
        )
        option.setdefault("var_type", "随机变量" if "不确定" in category else "区间变量")
        option.setdefault("dist_type", "Normal" if "不确定" in category else "Interval")
        option.setdefault("source", "跨层级跨阶段模型输入输出表")
        option.setdefault("model_id", option.get("model_id", ""))
        option.setdefault(
            "io",
            [
                ("输入", option.get("inputs") or "关键输入参数", "模型输入定义"),
                ("输出", option.get("outputs") or "关键输出参数", "模型输出定义"),
            ],
        )
        option.setdefault("mapping", [(option["title"], "画布节点", "模型配置")])
        return option

    def _model_display_text(self, option):
        name = option.get("param_name", option.get("name", option.get("title", "模型")))
        category = option.get("category", "")
        if category and category != "模型":
            return f"{category} - {name}"
        return name

    def _on_model_selected(self, index):
        if self._updating_model_combo or index < 0 or not self._model_options:
            return
        payload = self.model_selector.itemData(index)
        if not payload:
            return
        payload = dict(payload)
        option_context = payload.get("config_context", {})
        if option_context.get("scope") and option_context.get("category"):
            payload["config_context"] = option_context
        else:
            payload["config_context"] = self._current_payload.get("config_context", {})
        self.current_label.setText(payload.get("title", payload.get("name", "当前对象")))
        self._set_form(payload)
        self._set_qbhk_visible(self._is_qbhk_payload(payload))
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

    def _set_qbhk_visible(self, visible):
        self.qbhk_group.setVisible(visible)
        self.uq_group.setVisible(visible)

    def _is_qbhk_payload(self, payload):
        text = " ".join(
            str(payload.get(key, ""))
            for key in ("model_id", "title", "param_name", "name")
        )
        return "qbhk" in text.lower() or "曲柄滑块" in text

    def _fill_uq_defaults(self):
        rows = [
            (True, "E", "Normal", "2e9", "1e8"),
            (True, "F", "Normal", "-10", "1"),
            (False, "d", "Normal", "0.02", "0.001"),
            (False, "rho", "Normal", "7850", "150"),
            (False, "m_slider", "Normal", "0.5", "0.03"),
            (False, "omega", "Normal", "3.1415926", "0.05"),
        ]
        self.uq_table.setRowCount(len(rows))
        for row, (enabled, name, dist, mean, std) in enumerate(rows):
            checkbox = QCheckBox()
            checkbox.setChecked(enabled)
            self.uq_table.setCellWidget(row, 0, checkbox)
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.uq_table.setItem(row, 1, name_item)
            dist_combo = QComboBox()
            dist_combo.addItems(["Normal", "Uniform"])
            dist_combo.setCurrentText(dist)
            self.uq_table.setCellWidget(row, 2, dist_combo)
            self.uq_table.setItem(row, 3, QTableWidgetItem(mean))
            self.uq_table.setItem(row, 4, QTableWidgetItem(std))

    def qbhk_config(self):
        params = {}
        for key, edit in self._qbhk_fields.items():
            value = edit.text().strip()
            if key in {"Ne", "max_iter"}:
                params[key] = int(float(value))
            else:
                params[key] = float(value)

        uncertain = {}
        for row in range(self.uq_table.rowCount()):
            name_item = self.uq_table.item(row, 1)
            if not name_item:
                continue
            name = name_item.text()
            checkbox = self.uq_table.cellWidget(row, 0)
            combo = self.uq_table.cellWidget(row, 2)
            mean_item = self.uq_table.item(row, 3)
            std_item = self.uq_table.item(row, 4)
            mean = float(mean_item.text()) if mean_item and mean_item.text().strip() else params.get(name, 0.0)
            std = float(std_item.text()) if std_item and std_item.text().strip() else 0.0
            uncertain[name] = {
                "enabled": bool(checkbox and checkbox.isChecked()),
                "dist": combo.currentText() if combo else "Normal",
                "mean": mean,
                "std": std,
            }
        return {
            "params": params,
            "uncertain": uncertain,
            "enable_uq": self.enable_uq.isChecked(),
            "sample_count": self.sample_count.value(),
        }

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
