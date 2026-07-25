from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from .visualization_panel import VisualizationPanel


class ResultDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("结果展示")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.resize(1500, 920)
        self.setMinimumSize(1320, 820)
        self.setStyleSheet(
            """
            QDialog {
                background: #F4F7FB;
            }
            """
        )
        self._state = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.title_label = QLabel("结果展示")
        self.title_label.setFont(QFont("Microsoft YaHei", 22, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #0F172A;")
        layout.addWidget(self.title_label)

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            """
            background: white;
            border: 1px solid #D9E2EC;
            border-radius: 16px;
            padding: 14px 16px;
            color: #334E68;
            font-size: 14px;
            """
        )
        layout.addWidget(self.summary_label)

        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet(
            """
            background: #0F172A;
            color: #E2E8F0;
            border-radius: 16px;
            padding: 12px 16px;
            font-size: 14px;
            font-weight: 600;
            """
        )
        layout.addWidget(self.detail_label)

        self.visualization_panel = VisualizationPanel()
        layout.addWidget(self.visualization_panel, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _render(self, stage_data, stage_name, object_name, method_title, record):
        self.title_label.setText(f"{stage_name} - {object_name}")
        self.summary_label.setText(
            f"阶段：{stage_name}\n方法：{method_title}\n对象：{object_name}\n"
            f"说明：{record['object_intro']}"
        )
        metrics = record["metrics"]
        self.detail_label.setText(
            f"模型：{'；'.join(record['models'])}\n"
            f"结果：均值 {metrics['mean']:.2f}，标准差 {metrics['std']:.2f}，"
            f"可靠性 {metrics['reliability']:.2f}"
        )
        self.visualization_panel.update_plots(stage_data, stage_name, object_name)

    def show_results(self, stage_data, stage_name, object_name, method_title, record):
        self._state = (stage_data, stage_name, object_name, method_title, record)
        self._render(stage_data, stage_name, object_name, method_title, record)
        self.show()
        self.raise_()
        self.activateWindow()
        return self

    def refresh(self):
        if not self._state:
            return
        self._render(*self._state)
