from PySide6.QtGui import QColor

from .base_node import BaseNode


class StageNode(BaseNode):
    STAGE_COLORS = {
        "设计": "#3498DB",
        "制造": "#2ECC71",
        "装配": "#F39C12",
        "试验": "#9B59B6",
        "服役": "#E74C3C",
        "映射": "#16A085",
        "响应": "#8E44AD",
    }

    def __init__(self, stage_name="阶段", std_dev=1.0):
        super().__init__(title=stage_name, node_type="stage")
        self.params = {"stage_name": stage_name, "std_dev": std_dev}
        self.width = 135
        self.height = 78
        self.title_height = 28
        self.add_input_port("in")
        self.add_output_port("out")
        self.output_dist = None

    def _get_title_color(self):
        name = self.params.get("stage_name", "")
        for key, color in self.STAGE_COLORS.items():
            if key in name:
                return QColor(color)
        return QColor("#34495E")

    def set_stage_name(self, name):
        self.params["stage_name"] = name
        self.title = name
        self.title_item.setPlainText(name)
        self.update()


class InputSourceNode(BaseNode):
    def __init__(self, name="初始输入", mean=0.0, std=1.0):
        super().__init__(title=name, node_type="source")
        self.params = {"name": name, "mean": mean, "std": std}
        self.width = 140
        self.height = 72
        self.title_height = 28
        self.add_output_port("out")
        self.output_dist = None

    def _get_title_color(self):
        return QColor("#1ABC9C")


class OutputResultNode(BaseNode):
    def __init__(self, name="最终结果"):
        super().__init__(title=name, node_type="result")
        self.params = {"name": name}
        self.width = 140
        self.height = 72
        self.title_height = 28
        self.add_input_port("in")
        self.result_dist = None

    def _get_title_color(self):
        return QColor("#E74C3C")
