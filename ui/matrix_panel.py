from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


ROW_META = [
    ("quantification", "不确定因素量化", "#DBEAFE", "#1D4ED8"),
    ("propagation", "不确定性传播建模", "#FFEDD5", "#C2410C"),
    ("analysis", "不确定性分析", "#EDE9FE", "#6D28D9"),
]


class MatrixCard(QPushButton):
    def __init__(self, payload, bg_color, accent_color, parent=None):
        super().__init__(parent)
        self.payload = payload
        self.bg_color = bg_color
        self.accent_color = accent_color
        self.focused = False
        self.selected = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(220, 130)
        self.setMaximumHeight(150)
        self._apply_style()

    def set_state(self, focused=False, selected=False):
        self.focused = focused
        self.selected = selected
        self._apply_style()

    def _apply_style(self):
        border = self.accent_color if self.selected else "#D9E2EC"
        bg = "white" if self.selected else self.bg_color
        glow = "4px" if self.selected else "0px"
        pad = "16px" if self.selected else "14px"
        self.setStyleSheet(
            f"""
            QPushButton {{
                text-align: left;
                background: {bg};
                color: #102A43;
                border: 2px solid {border};
                border-radius: 22px;
                padding: {pad};
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {self.accent_color};
                background: white;
            }}
            """
        )


class MatrixPanel(QWidget):
    cell_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stage = None
        self.current_stage_data = {}
        self.current_selection = None
        self.current_focus = "quantification"
        self.object_order = []
        self.cards = {}
        self.row_labels = {}
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        self.stage_label = QLabel("阶段对象矩阵")
        self.stage_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        self.stage_label.setStyleSheet("color: #102A43;")
        outer.addWidget(self.stage_label)

        self.stage_note = QLabel("横向为对象，纵向为流程方法。")
        self.stage_note.setWordWrap(True)
        self.stage_note.setStyleSheet("color: #52606D; font-size: 13px;")
        outer.addWidget(self.stage_note)

        frame = QFrame()
        frame.setStyleSheet(
            """
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F9FBFF, stop:1 #F8FAFC
                );
                border: 1px solid #D9E2EC;
                border-radius: 24px;
            }
            """
        )
        outer.addWidget(frame)

        self.grid = QGridLayout(frame)
        self.grid.setContentsMargins(18, 18, 18, 18)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)

    def set_stage(self, stage_name, stage_data):
        self.current_stage = stage_name
        self.current_stage_data = stage_data
        self.object_order = list(stage_data["objects"].keys())
        self.stage_label.setText(f"{stage_name}：对象 × 方法矩阵")
        self.stage_note.setText(stage_data["summary"])
        self._rebuild_grid()
        if self.object_order:
            self.select_cell(self.current_focus, self.object_order[0])

    def set_method_focus(self, method_key):
        self.current_focus = method_key
        self._refresh_states()
        if self.object_order:
            current_object = self.current_selection["object"] if self.current_selection else self.object_order[0]
            self.select_cell(method_key, current_object)

    def select_cell(self, method_key, object_name):
        payload = self.current_stage_data["objects"][object_name]
        record = {
            "stage": self.current_stage,
            "object": object_name,
            "method_key": method_key,
            "method_title": next(row[1] for row in ROW_META if row[0] == method_key),
            "cell": payload["methods"][method_key],
            "models": payload["models"],
            "metrics": payload["metrics"],
            "object_intro": payload["intro"],
            "stage_summary": self.current_stage_data["summary"],
        }
        self.current_selection = record
        self._refresh_states(selected=(method_key, object_name))
        self.cell_selected.emit(record)

    def _rebuild_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.cards.clear()
        self.row_labels.clear()

        corner = QLabel("流程方法")
        corner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        corner.setMinimumSize(180, 64)
        corner.setStyleSheet(
            "background: #0F172A; border: none; border-radius: 18px; font-size: 16px; font-weight: 700; color: white; padding: 8px;"
        )
        self.grid.addWidget(corner, 0, 0)

        for col, object_name in enumerate(self.object_order, start=1):
            object_card = QLabel(object_name)
            object_card.setAlignment(Qt.AlignmentFlag.AlignCenter)
            object_card.setMinimumHeight(64)
            object_card.setStyleSheet(
                """
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFFFFF, stop:1 #F8FAFC
                );
                border: 1px solid #D9E2EC;
                border-radius: 18px;
                font-size: 17px;
                font-weight: 700;
                color: #102A43;
                padding: 10px;
                """
            )
            self.grid.addWidget(object_card, 0, col)

        for row, (method_key, title, bg_color, accent_color) in enumerate(ROW_META, start=1):
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumWidth(180)
            label.setStyleSheet(
                f"""
                background: {bg_color};
                border: 1px solid #DCE8F3;
                border-radius: 18px;
                font-size: 16px;
                font-weight: 700;
                color: {accent_color};
                padding: 14px;
                """
            )
            self.grid.addWidget(label, row, 0)
            self.row_labels[method_key] = label

            for col, object_name in enumerate(self.object_order, start=1):
                payload = self.current_stage_data["objects"][object_name]
                method_payload = payload["methods"][method_key]
                text = self._build_card_text(payload["models"], method_payload)
                button = MatrixCard(payload, bg_color, accent_color)
                button.setText(text)
                button.clicked.connect(
                    lambda checked=False, mk=method_key, obj=object_name: self.select_cell(mk, obj)
                )
                self.cards[(method_key, object_name)] = button
                self.grid.addWidget(button, row, col)

        self._refresh_states()

    @staticmethod
    def _build_card_text(models, method_payload):
        lines = [f"模型：{models[0]}"]
        for item in method_payload["items"][:2]:
            lines.append(f"• {item}")
        return "\n".join(lines)

    def _refresh_states(self, selected=None):
        selected = selected or (
            (self.current_selection["method_key"], self.current_selection["object"])
            if self.current_selection else None
        )
        for (method_key, object_name), card in self.cards.items():
            card.set_state(
                focused=(method_key == self.current_focus),
                selected=(selected == (method_key, object_name)),
            )
