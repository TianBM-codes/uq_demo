from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .matrix_panel import MatrixPanel
from .property_panel import PropertyPanel
from .result_dialog import ResultDialog
from .toolbox_panel import ToolboxPanel
from .visualization_panel import STAGE_ORDER


OBJECT_ORDER = ["活塞杆", "密封圈", "阀组件", "作动筒"]


METRIC_DATA = {
    "设计阶段": {
        "活塞杆": {"mean": 99.4, "std": 1.40, "lower": 96.6, "upper": 102.3, "center": 99.45, "fuzzy_peak": 0.92, "fuzzy_width": 2.0, "reliability": 0.97},
        "密封圈": {"mean": 98.8, "std": 1.75, "lower": 95.7, "upper": 101.9, "center": 98.80, "fuzzy_peak": 0.89, "fuzzy_width": 2.5, "reliability": 0.95},
        "阀组件": {"mean": 100.1, "std": 1.55, "lower": 97.1, "upper": 103.2, "center": 100.15, "fuzzy_peak": 0.91, "fuzzy_width": 2.3, "reliability": 0.96},
        "作动筒": {"mean": 99.7, "std": 1.32, "lower": 97.0, "upper": 102.1, "center": 99.55, "fuzzy_peak": 0.93, "fuzzy_width": 1.9, "reliability": 0.97},
    },
    "制造阶段（含装配）": {
        "活塞杆": {"mean": 98.9, "std": 2.05, "lower": 94.9, "upper": 102.8, "center": 98.85, "fuzzy_peak": 0.86, "fuzzy_width": 3.1, "reliability": 0.93},
        "密封圈": {"mean": 97.9, "std": 2.55, "lower": 93.0, "upper": 102.0, "center": 97.50, "fuzzy_peak": 0.82, "fuzzy_width": 3.6, "reliability": 0.90},
        "阀组件": {"mean": 99.2, "std": 2.25, "lower": 94.8, "upper": 103.0, "center": 98.90, "fuzzy_peak": 0.84, "fuzzy_width": 3.2, "reliability": 0.91},
        "作动筒": {"mean": 98.7, "std": 1.98, "lower": 95.0, "upper": 102.1, "center": 98.55, "fuzzy_peak": 0.87, "fuzzy_width": 3.0, "reliability": 0.93},
    },
    "试验阶段": {
        "活塞杆": {"mean": 98.2, "std": 2.35, "lower": 93.8, "upper": 102.2, "center": 98.00, "fuzzy_peak": 0.84, "fuzzy_width": 3.5, "reliability": 0.91},
        "密封圈": {"mean": 97.2, "std": 2.82, "lower": 92.1, "upper": 101.2, "center": 96.65, "fuzzy_peak": 0.80, "fuzzy_width": 4.0, "reliability": 0.88},
        "阀组件": {"mean": 98.6, "std": 2.60, "lower": 93.8, "upper": 102.9, "center": 98.35, "fuzzy_peak": 0.82, "fuzzy_width": 3.8, "reliability": 0.89},
        "作动筒": {"mean": 98.1, "std": 2.28, "lower": 94.0, "upper": 101.9, "center": 97.95, "fuzzy_peak": 0.84, "fuzzy_width": 3.3, "reliability": 0.91},
    },
    "服役阶段": {
        "活塞杆": {"mean": 97.4, "std": 3.10, "lower": 91.7, "upper": 102.0, "center": 96.85, "fuzzy_peak": 0.77, "fuzzy_width": 4.8, "reliability": 0.85},
        "密封圈": {"mean": 95.8, "std": 3.75, "lower": 89.0, "upper": 101.0, "center": 95.00, "fuzzy_peak": 0.72, "fuzzy_width": 5.5, "reliability": 0.81},
        "阀组件": {"mean": 96.9, "std": 3.40, "lower": 90.8, "upper": 102.1, "center": 96.45, "fuzzy_peak": 0.75, "fuzzy_width": 5.0, "reliability": 0.83},
        "作动筒": {"mean": 96.7, "std": 3.02, "lower": 91.0, "upper": 101.4, "center": 96.20, "fuzzy_peak": 0.78, "fuzzy_width": 4.6, "reliability": 0.85},
    },
}


OBJECT_TEMPLATE = {
    "活塞杆": {
        "intro": "活塞杆重点关注尺寸链、表面粗糙度、偏载和疲劳磨损，是作动器直线输出能力的核心承载对象。",
        "models": {
            "设计阶段": ["结构强度分析模型", "尺寸链设计模型"],
            "制造阶段（含装配）": ["粗糙度-同轴度偏差模型", "制造装配偏差传递模型"],
            "试验阶段": ["载荷-位移动力学模型", "测量误差修正模型"],
            "服役阶段": ["疲劳磨损退化模型", "剩余寿命预测模型"],
        },
    },
    "密封圈": {
        "intro": "密封圈是泄漏控制和寿命保障的关键对象，适合展示概率、区间和模糊信息在同一模块中的混合建模。",
        "models": {
            "设计阶段": ["密封接触压力模型", "微泄漏设计模型"],
            "制造阶段（含装配）": ["压缩量-配合偏差模型", "装配污染影响模型"],
            "试验阶段": ["泄漏试验响应模型", "热-压耦合验证模型"],
            "服役阶段": ["老化退化模型", "寿命衰减分析模型"],
        },
    },
    "阀组件": {
        "intro": "阀组件决定作动器流量调节与动态响应，适合展示阀芯、阀套和迟滞特性的多模型耦合分析。",
        "models": {
            "设计阶段": ["阀芯流量特性模型", "伺服阀控制模型"],
            "制造阶段（含装配）": ["阀套配合公差模型", "加工误差响应模型"],
            "试验阶段": ["动态响应试验模型", "迟滞误差辨识模型"],
            "服役阶段": ["卡滞风险模型", "服役性能衰减模型"],
        },
    },
    "作动筒": {
        "intro": "作动筒体现整体承压、刚度与动力学特征，可作为系统级对象承接活塞杆、密封圈和阀组件的传播结果。",
        "models": {
            "设计阶段": ["承压刚度模型", "筒体动力学模型"],
            "制造阶段（含装配）": ["圆柱度误差模型", "筒体装配约束模型"],
            "试验阶段": ["压力-位移耦合模型", "刚柔试验验证模型"],
            "服役阶段": ["结构老化模型", "系统级寿命预测模型"],
        },
    },
}


STAGE_SUMMARY = {
    "设计阶段": "设计阶段：纵向看量化、传播、分析三类流程，横向看活塞杆、密封圈、阀组件、作动筒四类对象，并突出各对象的设计模型。",
    "制造阶段（含装配）": "制造阶段（含装配）：不单列装配，而是将加工偏差、配合误差、装配扰动统一纳入制造阶段，适合做偏差传递展示。",
    "试验阶段": "试验阶段：围绕试验载荷、测量误差和模型校核展开，重点展示试验条件下的不确定性传播与响应输出。",
    "服役阶段": "服役阶段：突出磨损、老化、卡滞和寿命退化等长期因素，并用可靠性与模糊指标增强展示度。",
}


def build_stage_data():
    stage_data = {}
    for stage in STAGE_ORDER:
        objects = {}
        for object_name in OBJECT_ORDER:
            metrics = METRIC_DATA[stage][object_name]
            models = OBJECT_TEMPLATE[object_name]["models"][stage]
            objects[object_name] = {
                "intro": OBJECT_TEMPLATE[object_name]["intro"],
                "models": models,
                "metrics": metrics,
                "methods": {
                    "quantification": {
                        "items": [
                            f"概率模型：以 {models[0]} 为核心，输出均值 {metrics['mean']:.2f}、标准差 {metrics['std']:.2f}",
                            f"区间模型：输出上下界 [{metrics['lower']:.2f}, {metrics['upper']:.2f}]，中心值 {metrics['center']:.2f}",
                            f"模糊模型：以三角隶属度描述主观工况，峰值隶属度 {metrics['fuzzy_peak']:.2f}",
                        ]
                    },
                    "propagation": {
                        "items": [
                            f"代理模型：基于 {models[0]} 构建快速近似模型，支撑方案展示与参数扫略",
                            "混合传播模型：联合概率、区间与模糊变量，展示多源不确定性叠加过程",
                            "概率/区间传播模型：分别输出样本响应和边界包络，用于后续可靠性分析",
                        ]
                    },
                    "analysis": {
                        "items": [
                            f"概率响应：均值 {metrics['mean']:.2f}，标准差 {metrics['std']:.2f}",
                            f"区间响应：下界 {metrics['lower']:.2f}，上界 {metrics['upper']:.2f}，中心值 {metrics['center']:.2f}",
                            f"模糊响应：峰值隶属度 {metrics['fuzzy_peak']:.2f}，可靠性 {metrics['reliability']:.2f}",
                        ]
                    },
                },
            }
        stage_data[stage] = {"summary": STAGE_SUMMARY[stage], "objects": objects}
    return stage_data


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UQSim 作动器不确定性展示看板")
        self.resize(1560, 920)
        self.stage_data = build_stage_data()
        self.current_stage = STAGE_ORDER[0]
        self.current_method_key = "quantification"
        self.current_method_label = "不确定因素量化"
        self.current_record = None
        self.stage_buttons = {}
        self.result_dialog = ResultDialog(self)
        self._setup_ui()
        self._setup_connections()
        self._load_stage(self.current_stage)

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #F4F7FB;
                color: #102A43;
                font-family: "Microsoft YaHei";
            }
            QSplitter::handle {
                background: transparent;
                width: 10px;
                height: 10px;
            }
            QStatusBar {
                background: #0F172A;
                color: #E2E8F0;
                border-top: 1px solid #1E293B;
                font-size: 13px;
                padding-left: 8px;
            }
            """
        )
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.toolbox = ToolboxPanel()
        splitter.addWidget(self.toolbox)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(18, 18, 18, 18)
        center_layout.setSpacing(14)

        hero = QLabel("作动器不确定性分析展示界面")
        hero.setFont(QFont("Microsoft YaHei", 22, QFont.Weight.Bold))
        hero.setStyleSheet(
            """
            color: #0F172A;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #F8FBFF, stop:0.45 #EEF7FF, stop:1 #FFF7ED
            );
            border: 1px solid #D6E4F0;
            border-radius: 22px;
            padding: 18px 22px;
            """
        )
        center_layout.addWidget(hero)

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            """
            background: white;
            border: 1px solid #D9E2EC;
            border-radius: 18px;
            padding: 16px 18px;
            color: #334E68;
            font-size: 14px;
            line-height: 1.5;
            """
        )
        center_layout.addWidget(self.summary_label)

        stage_bar = QWidget()
        stage_layout = QHBoxLayout(stage_bar)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.setSpacing(12)
        for stage in STAGE_ORDER:
            btn = QPushButton(stage)
            btn.setMinimumHeight(54)
            btn.clicked.connect(lambda checked=False, s=stage: self._load_stage(s))
            self.stage_buttons[stage] = btn
            stage_layout.addWidget(btn)
        center_layout.addWidget(stage_bar)

        self.matrix_panel = MatrixPanel()
        center_layout.addWidget(self.matrix_panel, 3)

        splitter.addWidget(center)

        self.property_panel = PropertyPanel()
        splitter.addWidget(self.property_panel)
        splitter.setSizes([330, 880, 360])
        main_layout.addWidget(splitter)

        self._create_toolbar()
        self.statusBar().showMessage("展示界面已就绪")

    def _create_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            """
            QToolBar {
                spacing: 10px;
                padding: 10px 14px;
                background: rgba(255, 255, 255, 0.92);
                border-bottom: 1px solid #D9E2EC;
            }
            QToolButton {
                background: white;
                color: #0F172A;
                border: 1px solid #D9E2EC;
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: 700;
            }
            QToolButton:hover {
                background: #EFF6FF;
                border-color: #7DD3FC;
            }
            """
        )
        self.addToolBar(toolbar)

        run_action = QAction("运行展示分析", self)
        run_action.triggered.connect(self.run_propagation)
        toolbar.addAction(run_action)

        reset_action = QAction("重置视图", self)
        reset_action.triggered.connect(self.reset_view)
        toolbar.addAction(reset_action)

    def _setup_connections(self):
        self.toolbox.method_selected.connect(self._on_method_selected)
        self.toolbox.reset_requested.connect(self.reset_view)
        self.matrix_panel.cell_selected.connect(self._on_cell_selected)
        self.property_panel.metric_changed.connect(self._on_metric_changed)
        self.property_panel.run_btn.clicked.connect(self.run_propagation)

    def _load_stage(self, stage):
        self.current_stage = stage
        self._update_stage_buttons()
        self.summary_label.setText(
            f"当前阶段：{stage}\n{self.stage_data[stage]['summary']}"
        )
        self.matrix_panel.set_stage(stage, self.stage_data[stage])
        self.matrix_panel.set_method_focus(self.current_method_key)
        self.statusBar().showMessage(f"已切换到 {stage}")

    def _update_stage_buttons(self):
        for stage, btn in self.stage_buttons.items():
            if stage == self.current_stage:
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background: qlineargradient(
                            x1:0, y1:0, x2:1, y2:1,
                            stop:0 #0284C7, stop:1 #38BDF8
                        );
                        color: white;
                        border: none;
                        border-radius: 16px;
                        font-size: 15px;
                        font-weight: 800;
                        padding: 13px 20px;
                    }
                    """
                )
            else:
                btn.setStyleSheet(
                    """
                    QPushButton {
                        background: rgba(255, 255, 255, 0.95);
                        color: #102A43;
                        border: 1px solid #D9E2EC;
                        border-radius: 16px;
                        font-size: 15px;
                        font-weight: 700;
                        padding: 13px 20px;
                    }
                    QPushButton:hover {
                        border-color: #38BDF8;
                        background: #F8FDFF;
                    }
                    """
                )

    def _on_method_selected(self, method_key, label):
        self.current_method_key = method_key
        self.current_method_label = label
        self.matrix_panel.set_method_focus(method_key)
        self.statusBar().showMessage(f"已聚焦方法：{label}")

    def _on_cell_selected(self, record):
        self.current_record = record
        self.property_panel.set_record(record)
        self.statusBar().showMessage(
            f"已选择：{record['stage']} / {record['object']} / {record['method_title']}"
        )

    def _on_metric_changed(self, metric, value):
        if not self.current_record:
            return
        self.current_record["metrics"][metric] = value
        if self.result_dialog.isVisible():
            self.result_dialog.refresh()
        self.statusBar().showMessage(f"宸插垏鎹㈠弬鏁帮細{metric} = {value:.3f}")

    def run_propagation(self):
        if not self.current_record:
            self.matrix_panel.select_cell(self.current_method_key, OBJECT_ORDER[0])
        self.result_dialog.show_results(
            self.stage_data,
            self.current_stage,
            self.current_record["object"],
            self.current_record["method_title"],
            self.current_record,
        )
        self.statusBar().showMessage(
            f"已打开结果弹窗：{self.current_record['object']} / {self.current_stage}"
        )

    def reset_view(self):
        self.current_method_key = "quantification"
        self.current_method_label = "不确定因素量化"
        self._load_stage(STAGE_ORDER[0])
        self.result_dialog.visualization_panel.clear()
        self.statusBar().showMessage("展示视图已重置")
