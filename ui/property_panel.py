from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator, QFont
from PySide6.QtWidgets import (
    QFrame,
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PropertyPanel(QWidget):
    metric_changed = Signal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self._record = None
        self._updating = False
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #F1F5F9;
            }
            QGroupBox {
                font-size: 15px;
                font-weight: 700;
                color: #102A43;
                border: 1px solid #D9E2EC;
                border-radius: 18px;
                margin-top: 10px;
                background: rgba(255, 255, 255, 0.95);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QLineEdit {
                background: white;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 7px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #38BDF8;
            }
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        title = QLabel("模块详情")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #102A43;")
        layout.addWidget(title)

        self.selection_card = QGroupBox("当前模块")
        self.selection_card.setStyleSheet(
            """
            QGroupBox {
                border-radius: 20px;
                border: 1px solid #D6E4F0;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FBFF
                );
            }
            """
        )
        selection_layout = QVBoxLayout(self.selection_card)
        selection_layout.setContentsMargins(14, 18, 14, 14)
        selection_layout.setSpacing(8)

        self.stage_label = QLabel("阶段：-")
        self.object_label = QLabel("对象：-")
        self.method_label = QLabel("方法：-")
        for widget in (self.stage_label, self.object_label, self.method_label):
            widget.setStyleSheet("font-size: 14px; color: #243B53;")
            selection_layout.addWidget(widget)
        layout.addWidget(self.selection_card)

        self.intro_group = QGroupBox("模块说明")
        intro_layout = QVBoxLayout(self.intro_group)
        intro_layout.setContentsMargins(14, 18, 14, 14)
        self.intro_label = QLabel("选择矩阵模块后，这里会展示该对象在当前阶段的模型与分析逻辑。")
        self.intro_label.setWordWrap(True)
        self.intro_label.setStyleSheet("font-size: 14px; color: #486581; line-height: 1.5;")
        intro_layout.addWidget(self.intro_label)
        layout.addWidget(self.intro_group)

        self.model_group = QGroupBox("涉及模型")
        model_layout = QVBoxLayout(self.model_group)
        model_layout.setContentsMargins(14, 18, 14, 14)
        self.model_label = QLabel("-")
        self.model_label.setWordWrap(True)
        self.model_label.setStyleSheet("font-size: 14px; color: #243B53;")
        model_layout.addWidget(self.model_label)
        layout.addWidget(self.model_group)

        self.method_group = QGroupBox("方法内容")
        method_layout = QVBoxLayout(self.method_group)
        method_layout.setContentsMargins(14, 18, 14, 14)
        self.method_content = QLabel("-")
        self.method_content.setWordWrap(True)
        self.method_content.setStyleSheet("font-size: 14px; color: #243B53; line-height: 1.55;")
        method_layout.addWidget(self.method_content)
        layout.addWidget(self.method_group)

        self.edit_group = QGroupBox("可调参数")
        edit_layout = QVBoxLayout(self.edit_group)
        edit_layout.setContentsMargins(14, 18, 14, 14)
        self.edit_note = QLabel("直接输入数字即可，回车或失去焦点后立即生效。")
        self.edit_note.setWordWrap(True)
        self.edit_note.setStyleSheet("font-size: 12px; color: #64748B;")
        edit_layout.addWidget(self.edit_note)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)
        self.metric_inputs = {}
        validator = QDoubleValidator(-100000.0, 100000.0, 4, self)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        for key, title in [
            ("mean", "概率均值"),
            ("std", "概率标准差"),
            ("lower", "区间下界"),
            ("upper", "区间上界"),
            ("center", "区间中心值"),
            ("fuzzy_peak", "模糊峰值"),
            ("fuzzy_width", "模糊宽度"),
            ("reliability", "可靠性"),
        ]:
            edit = QLineEdit()
            edit.setValidator(validator)
            edit.setPlaceholderText("输入数字")
            edit.editingFinished.connect(lambda metric=key, widget=edit: self._on_metric_changed(metric, widget.text()))
            form.addRow(title, edit)
            self.metric_inputs[key] = edit
        edit_layout.addLayout(form)
        layout.addWidget(self.edit_group)

        self.metric_group = QGroupBox("输出指标")
        metric_layout = QVBoxLayout(self.metric_group)
        metric_layout.setContentsMargins(14, 18, 14, 14)
        self.metric_table = QTableWidget(6, 2)
        self.metric_table.horizontalHeader().setVisible(False)
        self.metric_table.verticalHeader().setVisible(False)
        self.metric_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.metric_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.metric_table.setStyleSheet("font-size: 13px;")
        metric_layout.addWidget(self.metric_table)
        layout.addWidget(self.metric_group)

        self.run_btn = QPushButton("运行展示分析")
        self.run_btn.setMinimumHeight(54)
        self.run_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #15803D, stop:1 #22C55E
                );
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 16px;
                font-weight: 800;
                padding: 12px 16px;
            }
            QPushButton:hover { background: #166534; }
            """
        )
        layout.addWidget(self.run_btn)
        layout.addStretch()
        self.set_record(None)

    def set_record(self, record):
        self._record = record
        if not record:
            self.stage_label.setText("阶段：-")
            self.object_label.setText("对象：-")
            self.method_label.setText("方法：-")
            self.intro_label.setText("选择矩阵模块后，这里会展示该对象在当前阶段的模型与分析逻辑。")
            self.model_label.setText("-")
            self.method_content.setText("-")
            self._set_metrics({})
            self._set_editors_enabled(False)
            return

        self.stage_label.setText(f"阶段：{record['stage']}")
        self.object_label.setText(f"对象：{record['object']}")
        self.method_label.setText(f"方法：{record['method_title']}")
        self.intro_label.setText(record["object_intro"])
        self.model_label.setText("\n".join([f"• {item}" for item in record["models"]]))
        self.method_content.setText("\n".join([f"• {item}" for item in record["cell"]["items"]]))
        self._set_metrics(record["metrics"])
        self._set_editors_enabled(True)
        self._sync_editors(record["metrics"])

    def _set_editors_enabled(self, enabled):
        self.edit_group.setEnabled(enabled)

    def _sync_editors(self, metrics):
        self._updating = True
        try:
            for key, widget in self.metric_inputs.items():
                value = metrics.get(key)
                widget.setText("" if value is None else f"{value:.4f}")
        finally:
            self._updating = False

    def _on_metric_changed(self, metric, text):
        if self._updating or not self._record:
            return
        try:
            value = float(text)
        except ValueError:
            self._sync_editors(self._record["metrics"])
            return
        self._record["metrics"][metric] = value
        self._set_metrics(self._record["metrics"])
        self.metric_changed.emit(metric, value)

    def _set_metrics(self, metrics):
        rows = [
            ("概率均值", metrics.get("mean", "-")),
            ("概率标准差", metrics.get("std", "-")),
            ("区间下界", metrics.get("lower", "-")),
            ("区间上界", metrics.get("upper", "-")),
            ("区间中心值", metrics.get("center", "-")),
            ("模糊峰值", metrics.get("fuzzy_peak", "-")),
        ]
        for row, (label, value) in enumerate(rows):
            self.metric_table.setItem(row, 0, QTableWidgetItem(label))
            item = QTableWidgetItem(f"{value:.3f}" if isinstance(value, (int, float)) else str(value))
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.metric_table.setItem(row, 1, item)
