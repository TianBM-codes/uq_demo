from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .property_panel import PropertyPanel
from .toolbox_panel import ToolboxPanel
from .workflow_canvas import WorkflowCanvas


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.toolbox = None
        self.workflow_canvas = None
        self.property_panel = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("跨阶段跨层级不确定性传播建模平台")
        self.resize(1720, 980)
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #F4F7FB;
                color: #102A43;
                font-family: "Microsoft YaHei";
            }
            QSplitter::handle {
                background: #E2E8F0;
                width: 1px;
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

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.start_page = self._build_start_page()
        self.editor_page = self._build_editor_page()
        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.editor_page)
        self.stack.setCurrentWidget(self.start_page)
        self.statusBar().showMessage("请选择跨层级或跨阶段工作流")

    def _build_start_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(120, 90, 120, 90)
        layout.setSpacing(28)
        layout.addStretch()

        title = QLabel("请选择工作流类型")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("先区分跨层级与跨阶段，再进入对应的工作流编辑界面。")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 15px; color: #52606D;")
        layout.addWidget(subtitle)

        button_row = QWidget()
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(0, 20, 0, 20)
        button_layout.setSpacing(28)
        button_layout.addStretch()

        cross_level = self._start_button("跨层级", "零部件、组件、子系统、系统、装备")
        cross_level.clicked.connect(lambda: self._enter_editor("cross_level"))
        button_layout.addWidget(cross_level)

        cross_stage = self._start_button("跨阶段", "设计、制造、试验、服役")
        cross_stage.clicked.connect(lambda: self._enter_editor("cross_stage"))
        button_layout.addWidget(cross_stage)
        button_layout.addStretch()
        layout.addWidget(button_row)

        layout.addStretch()
        return page

    def _start_button(self, title, subtitle):
        button = QPushButton(f"{title}\n{subtitle}")
        button.setMinimumSize(320, 150)
        button.setStyleSheet(
            """
            QPushButton {
                background: white;
                border: 1px solid #CBD5E1;
                border-radius: 24px;
                color: #0F172A;
                font-size: 19px;
                font-weight: 800;
                line-height: 1.8;
                padding: 22px;
                text-align: center;
            }
            QPushButton:hover {
                background: #EFF6FF;
                border-color: #2563EB;
            }
            """
        )
        return button

    def _build_editor_page(self):
        page = QWidget()
        root = QHBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.toolbox = ToolboxPanel()
        self.workflow_canvas = WorkflowCanvas()
        self.workflow_canvas.set_catalog(self.toolbox.catalog)
        self.property_panel = PropertyPanel()

        splitter.addWidget(self.toolbox)
        splitter.addWidget(self.workflow_canvas)
        splitter.addWidget(self.property_panel)
        splitter.setSizes([300, 1030, 390])
        root.addWidget(splitter)

        self._create_toolbar()
        self._setup_connections()
        return page

    def _create_toolbar(self):
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet(
            """
            QToolBar {
                spacing: 10px;
                padding: 10px 14px;
                background: rgba(255, 255, 255, 0.95);
                border-bottom: 1px solid #D9E2EC;
            }
            QToolButton {
                background: white;
                color: #0F172A;
                border: 1px solid #D9E2EC;
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
                font-weight: 700;
            }
            QToolButton:hover {
                background: #EFF6FF;
                border-color: #60A5FA;
            }
            """
        )
        self.addToolBar(self.toolbar)
        self.toolbar.hide()

        back_action = QAction("返回选择", self)
        back_action.triggered.connect(self._back_to_start)
        self.toolbar.addAction(back_action)

        zoom_in_action = QAction("放大", self)
        zoom_in_action.triggered.connect(self.workflow_canvas.zoom_in)
        self.toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.triggered.connect(self.workflow_canvas.zoom_out)
        self.toolbar.addAction(zoom_out_action)

        actual_size_action = QAction("实际大小", self)
        actual_size_action.triggered.connect(self.workflow_canvas.reset_zoom)
        self.toolbar.addAction(actual_size_action)

        fit_action = QAction("适应窗口", self)
        fit_action.triggered.connect(self.workflow_canvas.fit_all)
        self.toolbar.addAction(fit_action)

        delete_action = QAction("删除选中", self)
        delete_action.triggered.connect(self._delete_selected)
        self.toolbar.addAction(delete_action)

        clear_action = QAction("清空画布", self)
        clear_action.triggered.connect(self._clear_canvas)
        self.toolbar.addAction(clear_action)

    def _setup_connections(self):
        self.toolbox.item_selected.connect(self._on_tree_selected)
        self.workflow_canvas.selection_changed.connect(self.property_panel.show_payload)
        self.workflow_canvas.block_added.connect(self._on_block_added)
        self.workflow_canvas.block_renamed.connect(self.toolbox.rename_instance)
        self.workflow_canvas.model_configured.connect(self._on_model_configured)
        self.property_panel.model_configured.connect(self._on_model_configured)

    def _enter_editor(self, workflow):
        self.toolbox.set_workflow(workflow)
        self.workflow_canvas.clear_workflow(workflow)
        self.property_panel.show_payload(self._default_payload())
        self.stack.setCurrentWidget(self.editor_page)
        self.toolbar.show()
        self.statusBar().showMessage(f"已进入{self.toolbox.current_workflow_text()}工作流编辑界面")

    def _back_to_start(self):
        self.stack.setCurrentWidget(self.start_page)
        self.toolbar.hide()
        self.statusBar().showMessage("请选择跨层级或跨阶段工作流")

    def _on_tree_selected(self, payload):
        detail = self._tree_payload(payload)
        self.property_panel.show_payload(detail)
        self.statusBar().showMessage(f"已聚焦：{detail['title']}")

    def _on_block_added(self, payload):
        self.toolbox.mark_block_added(payload)
        self.statusBar().showMessage(f"已添加：{payload.get('label', payload.get('scope', '部件'))}")

    def _on_model_configured(self, payload):
        self.toolbox.mark_model_selected(payload.get("context", {}), payload.get("model_name", ""))

    def _delete_selected(self):
        if self.workflow_canvas.delete_selected():
            self.property_panel.show_payload(None)
            self.statusBar().showMessage("已删除选中的部件或连线")
        else:
            self.statusBar().showMessage("请先在画布中选中要删除的部件或连线")

    def _clear_canvas(self):
        self.workflow_canvas.clear_workflow(self.toolbox.current_workflow)
        self.toolbox.clear_instances()
        self.property_panel.show_payload(self._default_payload())
        self.statusBar().showMessage("已清空当前工作流画布")

    def _tree_payload(self, payload):
        kind = payload.get("kind", "unknown")
        name = payload.get("name", "模型树节点")
        scope = payload.get("scope", "")
        model_options = [self._model_payload(option) for option in payload.get("model_options", [])]

        if kind == "model":
            detail = self._model_payload(payload)
            detail["model_options"] = model_options
            detail["config_context"] = {
                "workflow": payload.get("workflow", self.toolbox.current_workflow),
                "scope": scope,
                "category": payload.get("category", ""),
            }
            return detail

        if kind in {"stage", "level"}:
            models = []
            for categories in self.toolbox.catalog.get(payload.get("workflow", ""), {}).get(name, {}).values():
                models.extend(categories)
            return {
                "title": name,
                "param_name": name,
                "var_type": "随机变量",
                "dist_type": "Normal",
                "mean": "",
                "std": "",
                "source": "当前工作流结构",
                "model_options": [self._model_payload(option) for option in models],
                "config_context": {
                    "workflow": payload.get("workflow", self.toolbox.current_workflow),
                    "scope": name,
                    "category": "节点总体配置",
                },
                "io": [
                    ("输入", "上游参数 / 工况 / 状态", "作为该大节点配置输入"),
                    ("输出", "节点结果 / 可靠性指标", "供下游节点连接使用"),
                ],
                "mapping": [(name, "画布对应节点", "节点标签、模型配置和输入输出参数")],
            }

        if kind == "category" and model_options:
            detail = dict(model_options[0])
            detail["title"] = f"{scope} - {name} - {detail['param_name']}"
            detail["model_options"] = model_options
            detail["config_context"] = {
                "workflow": payload.get("workflow", self.toolbox.current_workflow),
                "scope": scope,
                "category": name,
            }
            return detail

        title = f"{scope} - {name}" if scope else name
        return {
            "title": title,
            "param_name": name,
            "var_type": "随机变量" if "不确定" in name else "区间变量",
            "dist_type": "Normal" if "不确定" in name else "Interval",
            "mean": "",
            "std": "",
            "source": "模型树与画布连线",
            "model_options": model_options,
            "config_context": {
                "workflow": payload.get("workflow", self.toolbox.current_workflow),
                "scope": scope or name,
                "category": name,
            },
            "io": [
                ("输入", "关键输入参数", f"{title} 对应的模型输入集合"),
                ("输出", "关键输出参数", f"{title} 输出给画布下游子项"),
            ],
            "mapping": [(title, "画布对应阶段/层级子项", "输入输出参数映射")],
        }

    def _model_payload(self, payload):
        name = payload.get("name", payload.get("param_name", "模型"))
        scope = payload.get("scope", "")
        category = payload.get("category", "模型")
        title = f"{scope} - {category} - {name}"
        return {
            "title": title,
            "param_name": name,
            "var_type": "随机变量" if "不确定" in category else "区间变量",
            "dist_type": "Normal" if "不确定" in category else "Interval",
            "mean": "",
            "std": "",
            "source": "跨层级跨阶段模型输入输出表",
            "io": [
                ("输入", payload.get("inputs") or "关键输入参数", "模型输入定义"),
                ("输出", payload.get("outputs") or "关键输出参数", "模型输出定义"),
            ],
            "mapping": [(title, "画布下游子项", "关键输入/输出参数")],
            "config_context": {
                "workflow": payload.get("workflow", self.toolbox.current_workflow),
                "scope": scope,
                "category": category,
            },
        }

    def _default_payload(self):
        return {
            "title": f"{self.toolbox.current_workflow_text()}工作流",
            "param_name": "未选择节点",
            "var_type": "随机变量",
            "dist_type": "Normal",
            "mean": "",
            "std": "",
            "source": "工作流编辑",
            "io": [
                ("输入", "左侧可添加对象", "拖拽整体流程或阶段/层级到画布"),
                ("输出", "工作流实例", "在左侧已添加结构中记录，在画布中进行连线"),
            ],
            "mapping": [],
        }
