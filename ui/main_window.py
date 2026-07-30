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

from .property_panel import PropertyPanel
from .toolbox_panel import ToolboxPanel
from .workflow_canvas import WorkflowCanvas


STAGES = ["设计阶段", "制造阶段", "试验阶段", "服役阶段"]

WORKFLOW_NODES = {
    "injection": {
        "id": "injection",
        "category": "support",
        "section_title": "支撑模块",
        "title": "不确定因素注入",
        "summary": "将工况、粗糙度、装配间隙、载荷、环境、退化等不确定参数注入到功能模型。",
        "footer": "强调“参数如何进模型”，这是甲方最关心的入口。",
        "goal": "支撑概率、区间、随机过程、模糊等参数定义，并完成参数与模型接口的绑定。",
        "inputs": "先验参数、试验数据、服役数据、边界条件",
        "outputs": "可传播的不确定参数集合、注入映射关系",
        "algorithms": ["概率建模", "区间建模", "随机过程建模", "随机场建模", "模糊建模"],
        "config_items": [
            "选择参数类型：概率 / 区间 / 随机过程 / 模糊",
            "配置注入位置：材料参数、几何参数、装配偏差、载荷与环境",
            "设置相关性、时间相关性、空间相关性",
        ],
        "highlight_values": [
            "不确定参数个数",
            "注入对象数量",
            "相关性与约束关系",
        ],
        "stage_hint": "跨阶段通用",
        "link_label": "注入到功能模型",
        "link_color": "#059669",
    },
    "functional": {
        "id": "functional",
        "category": "functional",
        "section_title": "功能性模型",
        "title": "功能性模型样板库",
        "summary": "按设计、制造、试验、服役组织样板库，支撑弹性静力学、刚柔耦合、密封、装配、退化等模型。",
        "footer": "这里体现“样板库集成”，而不是零散算法堆砌。",
        "goal": "把多阶段、多物理场的功能模型统一组织在一个拖拽式样板库里，支撑快速搭建分析链。",
        "inputs": "注入参数、阶段上下文、模型模板、边界条件",
        "outputs": "响应变量、阶段结果、可传递状态量",
        "algorithms": ["弹性静力学模型", "刚柔耦合动力学模型", "密封性能分析模型", "装配模型", "退化模型"],
        "config_items": [
            "按阶段切换模型模板：设计 / 制造 / 试验 / 服役",
            "为每个模型设置求解器、步长、收敛策略",
            "配置输入输出接口，明确传递给下游的响应变量",
        ],
        "highlight_values": [
            "样板库覆盖阶段",
            "模型输入输出数量",
            "可复用模板数",
        ],
        "stage_hint": "设计-制造-试验-服役",
        "link_label": "生成传播对象",
        "link_color": "#2563EB",
    },
    "propagation": {
        "id": "propagation",
        "category": "propagation",
        "section_title": "不确定性传播模型",
        "title": "不确定性传播建模",
        "summary": "把多源不确定信息从参数层传播到系统响应层，突出跨阶段、跨层级传递关系。",
        "footer": "这是界面中心，应当比普通求解器更醒目。",
        "goal": "解决多源不确定性在功能模型中的传播与映射，形成从微观参数波动到宏观响应的主链路。",
        "inputs": "功能模型响应、输入参数分布、相关性结构",
        "outputs": "概率响应、区间包络、随机过程响应、传播链路信息",
        "algorithms": ["概率传播模型", "区间传播模型", "概率-区间混合传播模型", "随机过程传播模型", "随机场传播模型"],
        "config_items": [
            "选择传播类型：概率 / 区间 / 混合 / 随机过程 / 随机场",
            "设置样本数、近似方法、代理模型或降阶策略",
            "定义传播目标：性能、寿命、稳定性、失效概率",
        ],
        "highlight_values": [
            "传播路径",
            "样本量与效率",
            "多阶段耦合响应",
        ],
        "stage_hint": "建模核心",
        "link_label": "进入可靠性分析",
        "link_color": "#D97706",
    },
    "reliability": {
        "id": "reliability",
        "category": "reliability",
        "section_title": "可靠性分析模型",
        "title": "可靠性分析与评价",
        "summary": "区分零组件可靠性和系统可靠性，支撑一次二阶矩、代理模型、蒙特卡洛、故障树、贝叶斯网络等。",
        "footer": "分析结果可回到模型修正，形成闭环。",
        "goal": "基于传播结果评估零组件和系统级风险，输出可靠性、寿命与风险指标。",
        "inputs": "传播响应、失效判据、结构与系统拓扑",
        "outputs": "可靠度、失效率、寿命预测、系统风险评价",
        "algorithms": ["一次二阶矩模型", "蒙特卡洛模型", "代理模型", "故障树模型", "贝叶斯网络模型"],
        "config_items": [
            "选择对象层级：零组件级 / 系统级",
            "设置失效阈值、寿命准则、系统结构关系",
            "配置结果输出：可靠度、重要度、剩余寿命、风险等级",
        ],
        "highlight_values": [
            "可靠度",
            "失效概率",
            "寿命预测结果",
        ],
        "stage_hint": "零组件级 + 系统级",
        "link_label": "反馈校准",
        "link_color": "#7C3AED",
    },
}

LIBRARY_ITEM_MAP = {
    "不确定因素注入": "injection",
    "参数映射与接口配置": "injection",
    "功能性模型": "functional",
    "弹性静力学模型": "functional",
    "刚柔耦合动力学模型": "functional",
    "机电耦合模型": "functional",
    "密封性能分析模型": "functional",
    "装配模型": "functional",
    "退化模型": "functional",
    "概率传播模型": "propagation",
    "区间传播模型": "propagation",
    "概率-区间混合传播模型": "propagation",
    "随机过程传播模型": "propagation",
    "随机场传播模型": "propagation",
    "模糊传播模型": "propagation",
    "一次二阶矩模型": "reliability",
    "响应面模型": "reliability",
    "蒙特卡洛模型": "reliability",
    "代理模型": "reliability",
    "故障树模型": "reliability",
    "贝叶斯网络模型": "reliability",
    "模型修正与贝叶斯校准": "reliability",
    "敏感性分析": "reliability",
    "寿命预测与风险评价": "reliability",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_stage = STAGES[0]
        self.stage_buttons = {}
        self._setup_ui()
        self._setup_connections()
        self._load_stage(self.current_stage)
        self.workflow_canvas.reset_view()

    def _setup_ui(self):
        self.setWindowTitle("UQ传播建模演示原型")
        self.resize(1680, 980)
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
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.toolbox = ToolboxPanel()
        splitter.addWidget(self.toolbox)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(18, 18, 18, 18)
        center_layout.setSpacing(14)

        hero = QLabel("面向不确定性传播建模的可靠性分析平台")
        hero.setFont(QFont("Microsoft YaHei", 23, QFont.Weight.Bold))
        hero.setStyleSheet(
            """
            color: #0F172A;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #F8FBFF, stop:0.4 #EEF7FF, stop:1 #FFF7ED
            );
            border: 1px solid #D6E4F0;
            border-radius: 24px;
            padding: 20px 22px;
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
            line-height: 1.55;
            """
        )
        center_layout.addWidget(self.summary_label)

        stage_bar = QWidget()
        stage_layout = QHBoxLayout(stage_bar)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.setSpacing(12)
        for stage in STAGES:
            btn = QPushButton(stage)
            btn.setMinimumHeight(52)
            btn.clicked.connect(lambda checked=False, value=stage: self._load_stage(value))
            self.stage_buttons[stage] = btn
            stage_layout.addWidget(btn)
        center_layout.addWidget(stage_bar)

        self.workflow_canvas = WorkflowCanvas(WORKFLOW_NODES)
        center_layout.addWidget(self.workflow_canvas, 1)

        self.highlight_label = QLabel("")
        self.highlight_label.setWordWrap(True)
        self.highlight_label.setStyleSheet(
            """
            background: #0F172A;
            color: #E2E8F0;
            border-radius: 18px;
            padding: 14px 16px;
            font-size: 14px;
            font-weight: 600;
            """
        )
        center_layout.addWidget(self.highlight_label)

        splitter.addWidget(center)

        self.property_panel = PropertyPanel()
        splitter.addWidget(self.property_panel)
        splitter.setSizes([360, 930, 390])
        root.addWidget(splitter)

        self._create_toolbar()
        self.statusBar().showMessage("新的流程编排界面已加载")

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

        focus_action = QAction("聚焦传播主线", self)
        focus_action.triggered.connect(lambda: self.workflow_canvas.add_node_by_id("propagation"))
        toolbar.addAction(focus_action)

        connect_action = QAction("连接选中节点", self)
        connect_action.triggered.connect(self._connect_selected_nodes)
        toolbar.addAction(connect_action)

        reset_action = QAction("恢复默认链路", self)
        reset_action.triggered.connect(self.reset_view)
        toolbar.addAction(reset_action)

    def _setup_connections(self):
        self.toolbox.section_selected.connect(self._on_section_selected)
        self.toolbox.item_selected.connect(self._on_item_selected)
        self.toolbox.reset_requested.connect(self.reset_view)
        self.workflow_canvas.node_selected.connect(self._on_node_selected)

    def _load_stage(self, stage):
        self.current_stage = stage
        self._update_stage_buttons()
        self.summary_label.setText(
            f"当前阶段：{stage}\n"
            "界面主叙事从“功能菜单”改成“传播建模链路”。左侧按样板库组织模型，中央串联参数注入、功能模型、传播模型和可靠性评价，"
            "右侧则明确每个块支持哪些算法与配置项。"
        )
        self.highlight_label.setText(
            f"{stage}重点："
            + {
                "设计阶段": "强调设计参数、材料参数与结构响应的传播关系。",
                "制造阶段": "强调加工误差、装配偏差和工艺波动向性能的传递。",
                "试验阶段": "强调载荷工况、测量误差与模型修正闭环。",
                "服役阶段": "强调退化、磨损、寿命预测与可靠性动态更新。",
            }[stage]
        )
        self.statusBar().showMessage(f"已切换到{stage}")

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
                        padding: 12px 18px;
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
                        padding: 12px 18px;
                    }
                    QPushButton:hover {
                        border-color: #38BDF8;
                        background: #F8FDFF;
                    }
                    """
                )

    def _on_section_selected(self, section_key, section_title):
        self.workflow_canvas.highlight_section(section_key)
        self.statusBar().showMessage(f"已聚焦{section_title}")

    def _on_item_selected(self, payload):
        node_id = LIBRARY_ITEM_MAP.get(payload["item"], "propagation")
        self.workflow_canvas.add_node_by_id(node_id)
        self.statusBar().showMessage(f"已将模块加入画布：{payload['item']}")

    def _on_node_selected(self, block):
        if not block:
            self.highlight_label.setText("当前未选中节点。可以从左侧拖入模块，或在画布上框选两个组件后执行连接。")
            return
        block = dict(block)
        block["stage_hint"] = f"{self.current_stage}重点"
        self.property_panel.set_block(block)
        self.highlight_label.setText(
            f"当前聚焦：{block['title']}。"
            f" 建议在界面里显性展示 {block['highlight_values'][0]}、{block['highlight_values'][1]} 和 {block['highlight_values'][2]}。"
        )
        self.statusBar().showMessage(f"当前模块：{block['title']}")

    def reset_view(self):
        self._load_stage(STAGES[0])
        self.workflow_canvas.reset_view()
        self.statusBar().showMessage("已恢复默认链路")

    def _connect_selected_nodes(self):
        if self.workflow_canvas.connect_selected_nodes():
            self.statusBar().showMessage("已建立组件之间的连线")
        else:
            self.statusBar().showMessage("请先在画布中选中两个组件，再执行连接")
