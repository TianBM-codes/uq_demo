import json
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, Signal
from PySide6.QtGui import QDrag, QFont
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

try:
    import openpyxl
except ImportError:
    openpyxl = None


WORKFLOW_MIME = "application/x-uq-workflow-payload"
WORKFLOW_LABELS = {"cross_level": "跨层级", "cross_stage": "跨阶段"}
SCOPE_KIND = {"cross_level": "level", "cross_stage": "stage"}
SCOPE_NAMES = {
    "cross_level": ["零部件", "组件", "子系统", "系统", "装备"],
    "cross_stage": ["设计阶段", "制造阶段", "试验阶段", "服役阶段"],
}
MODEL_CATEGORIES = ["功能性能模型", "不确定性传播模型", "零组件可靠性模型", "系统可靠性模型"]


class ModelTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_pos = None
        self.setDragEnabled(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return
        if (event.position().toPoint() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        item = self.itemAt(self._drag_start_pos)
        payload = self._drag_payload(item)
        if not payload:
            super().mouseMoveEvent(event)
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(WORKFLOW_MIME, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

    def _drag_payload(self, item):
        if item is None:
            return None
        payload = dict(item.data(0, Qt.ItemDataRole.UserRole) or {})
        if payload.get("kind") in {"route", "stage", "level"}:
            return payload
        return None


class ToolboxPanel(QWidget):
    item_selected = Signal(dict)
    workflow_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.current_workflow = "cross_level"
        self.catalog = self._load_catalog()
        self.selected_models = {}
        self.instances = {}
        self._setup_ui()
        self.set_workflow(self.current_workflow)

    def _setup_ui(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #F4F7FB;
                color: #102A43;
                font-family: "Microsoft YaHei";
            }
            QPushButton {
                background: white;
                border: 1px solid #D9E2EC;
                border-radius: 10px;
                padding: 9px 10px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:checked {
                background: #1D4ED8;
                color: white;
                border-color: #1D4ED8;
            }
            QTreeWidget {
                background: white;
                border: 1px solid #D9E2EC;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QTreeWidget::item {
                min-height: 28px;
                padding: 3px 4px;
            }
            QTreeWidget::item:selected {
                background: #DBEAFE;
                color: #1D4ED8;
                border-radius: 4px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("工作流结构")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        self.cross_level_btn = QPushButton("跨层级")
        self.cross_level_btn.setCheckable(True)
        self.cross_level_btn.clicked.connect(lambda: self.set_workflow("cross_level"))
        layout.addWidget(self.cross_level_btn)

        self.cross_stage_btn = QPushButton("跨阶段")
        self.cross_stage_btn.setCheckable(True)
        self.cross_stage_btn.clicked.connect(lambda: self.set_workflow("cross_stage"))
        layout.addWidget(self.cross_stage_btn)

        hint = QLabel("从“可添加对象”拖拽整体流程或阶段/层级到画布；具体模型在右侧配置。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #52606D; font-size: 12px; line-height: 1.5;")
        layout.addWidget(hint)

        self.tree = ModelTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree, 1)

    def set_workflow(self, workflow):
        if workflow not in WORKFLOW_LABELS:
            return
        self.current_workflow = workflow
        self.cross_level_btn.setChecked(workflow == "cross_level")
        self.cross_stage_btn.setChecked(workflow == "cross_stage")
        self._populate_tree()
        self.workflow_changed.emit(workflow)

    def current_workflow_text(self):
        return WORKFLOW_LABELS[self.current_workflow]

    def model_options(self, workflow, scope, category):
        return list(self.catalog.get(workflow, {}).get(scope, {}).get(category, []))

    def mark_model_selected(self, context, model_name):
        workflow = context.get("workflow", self.current_workflow)
        scope = context.get("scope", "")
        category = context.get("category", "")
        if workflow != self.current_workflow or not scope or not category or not model_name:
            return
        self.selected_models[(workflow, scope, category)] = model_name
        category_item = self._find_category_item(scope, category)
        if category_item is None:
            category_item = self._ensure_category_item(scope, category)
        if category_item is None:
            return

        marker_text = f"已选：{model_name}"
        for index in range(category_item.childCount()):
            child = category_item.child(index)
            child_payload = child.data(0, Qt.ItemDataRole.UserRole) or {}
            if child_payload.get("kind") == "selected_model":
                child.setText(0, marker_text)
                child.setData(0, Qt.ItemDataRole.UserRole, {"kind": "selected_model", "name": model_name})
                return

        marker = QTreeWidgetItem([marker_text])
        marker.setForeground(0, Qt.GlobalColor.darkGreen)
        marker.setData(0, Qt.ItemDataRole.UserRole, {"kind": "selected_model", "name": model_name})
        category_item.insertChild(0, marker)
        category_item.setExpanded(True)

    def mark_block_added(self, payload):
        workflow = payload.get("workflow", self.current_workflow)
        scope = payload.get("scope", "")
        label = payload.get("label", scope)
        if workflow != self.current_workflow or not scope:
            return
        self.instances.setdefault((workflow, scope), [])
        if label not in self.instances[(workflow, scope)]:
            self.instances[(workflow, scope)].append(label)
        self._populate_tree()

    def rename_instance(self, payload):
        workflow = payload.get("workflow", self.current_workflow)
        scope = payload.get("scope", "")
        old_label = payload.get("old_label", "")
        new_label = payload.get("new_label", "")
        labels = self.instances.get((workflow, scope), [])
        for index, label in enumerate(labels):
            if label == old_label:
                labels[index] = new_label
                break
        self._populate_tree()

    def clear_instances(self):
        self.instances = {
            key: value
            for key, value in self.instances.items()
            if key[0] != self.current_workflow
        }
        self.selected_models = {
            key: value
            for key, value in self.selected_models.items()
            if key[0] != self.current_workflow
        }
        self._populate_tree()

    def _populate_tree(self):
        self.tree.clear()
        workflow = self.current_workflow
        root_label = WORKFLOW_LABELS[workflow]
        root = QTreeWidgetItem([root_label])
        root.setData(0, Qt.ItemDataRole.UserRole, {"kind": "group", "workflow": workflow, "name": root_label})

        library_root = QTreeWidgetItem(["可添加对象"])
        library_root.setData(0, Qt.ItemDataRole.UserRole, {"kind": "library", "workflow": workflow, "name": "可添加对象"})
        self._add_route_item(library_root, workflow, f"{root_label}流程")

        structure_root = QTreeWidgetItem(["已添加到工作流"])
        structure_root.setData(0, Qt.ItemDataRole.UserRole, {"kind": "structure", "workflow": workflow, "name": "已添加到工作流"})

        for scope in SCOPE_NAMES[workflow]:
            library_scope_item = QTreeWidgetItem([scope])
            library_scope_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {"kind": SCOPE_KIND[workflow], "workflow": workflow, "name": scope, "scope": scope},
            )
            library_root.addChild(library_scope_item)

            structure_scope_item = QTreeWidgetItem([scope])
            structure_scope_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {"kind": "scope_bucket", "workflow": workflow, "name": scope, "scope": scope},
            )
            for instance in self.instances.get((workflow, scope), []):
                instance_item = QTreeWidgetItem([instance])
                instance_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {"kind": SCOPE_KIND[workflow], "workflow": workflow, "name": instance, "scope": scope},
                )
                structure_scope_item.addChild(instance_item)

            for category in MODEL_CATEGORIES:
                selected_model = self.selected_models.get((workflow, scope, category))
                if selected_model:
                    category_item = QTreeWidgetItem([category])
                    category_item.setData(
                        0,
                        Qt.ItemDataRole.UserRole,
                        {
                            "kind": "category",
                            "workflow": workflow,
                            "scope": scope,
                            "name": category,
                            "model_options": self.model_options(workflow, scope, category),
                        },
                    )
                    marker = QTreeWidgetItem([f"已选：{selected_model}"])
                    marker.setForeground(0, Qt.GlobalColor.darkGreen)
                    marker.setData(0, Qt.ItemDataRole.UserRole, {"kind": "selected_model", "name": selected_model})
                    category_item.insertChild(0, marker)
                    structure_scope_item.addChild(category_item)
            structure_root.addChild(structure_scope_item)

        root.addChild(library_root)
        root.addChild(structure_root)

        self.tree.addTopLevelItem(root)
        self.tree.expandItem(root)
        self.tree.expandItem(library_root)
        self.tree.expandItem(structure_root)

    def _load_catalog(self):
        catalog = {
            workflow: {scope: {category: [] for category in MODEL_CATEGORIES} for scope in scopes}
            for workflow, scopes in SCOPE_NAMES.items()
        }
        workbook = self._find_workbook()
        if not workbook or openpyxl is None:
            return catalog

        try:
            worksheet = openpyxl.load_workbook(workbook, data_only=True).active
        except Exception:
            return catalog

        current = ["", "", ""]
        for row in worksheet.iter_rows(min_row=2, values_only=True):
            level_one, level_two, category, model, inputs, outputs = row[:6]
            if level_one:
                current[0] = str(level_one).strip()
            if level_two:
                current[1] = str(level_two).strip()
            if category:
                current[2] = str(category).strip()
            if not current[0] or not current[1] or not current[2] or not model:
                continue

            workflow = "cross_stage" if current[0] == "跨阶段" else "cross_level"
            scope = current[1]
            category_name = current[2]
            if scope not in catalog[workflow]:
                catalog[workflow][scope] = {category: [] for category in MODEL_CATEGORIES}
            if category_name not in catalog[workflow][scope]:
                catalog[workflow][scope][category_name] = []
            catalog[workflow][scope][category_name].append(
                {
                    "kind": "model",
                    "workflow": workflow,
                    "scope": scope,
                    "category": category_name,
                    "name": str(model).strip(),
                    "inputs": self._clean_cell(inputs),
                    "outputs": self._clean_cell(outputs),
                }
            )
        return catalog

    def _find_workbook(self):
        data_dir = Path(__file__).resolve().parent.parent / "data"
        matches = sorted(data_dir.glob("跨层级跨阶段模型输入输出表*.xlsx"))
        return matches[0] if matches else None

    def _clean_cell(self, value):
        if not value:
            return ""
        return " / ".join(part.strip() for part in str(value).splitlines() if part.strip())

    def _add_route_item(self, parent, workflow, name):
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.ItemDataRole.UserRole, {"kind": "route", "workflow": workflow, "name": name})
        parent.addChild(item)

    def _find_category_item(self, scope, category):
        root = self.tree.topLevelItem(0)
        if not root:
            return None
        for scope_index in range(root.childCount()):
            parent_item = root.child(scope_index)
            if parent_item.text(0) != "已添加到工作流":
                continue
            for bucket_index in range(parent_item.childCount()):
                scope_item = parent_item.child(bucket_index)
                if scope_item.text(0) != scope:
                    continue
                for category_index in range(scope_item.childCount()):
                    category_item = scope_item.child(category_index)
                    if category_item.text(0) == category:
                        return category_item
        return None

    def _ensure_category_item(self, scope, category):
        root = self.tree.topLevelItem(0)
        if not root:
            return None
        structure_root = None
        for index in range(root.childCount()):
            if root.child(index).text(0) == "已添加到工作流":
                structure_root = root.child(index)
                break
        if structure_root is None:
            return None
        for scope_index in range(structure_root.childCount()):
            scope_item = structure_root.child(scope_index)
            if scope_item.text(0) != scope:
                continue
            category_item = QTreeWidgetItem([category])
            category_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {
                    "kind": "category",
                    "workflow": self.current_workflow,
                    "scope": scope,
                    "name": category,
                    "model_options": self.model_options(self.current_workflow, scope, category),
                },
            )
            scope_item.addChild(category_item)
            scope_item.setExpanded(True)
            return category_item
        return None

    def _on_item_clicked(self, item):
        payload = dict(item.data(0, Qt.ItemDataRole.UserRole) or {"kind": "unknown", "name": item.text(0)})
        self.item_selected.emit(payload)
