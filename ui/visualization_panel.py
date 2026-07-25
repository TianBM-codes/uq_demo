import math

import matplotlib
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


STAGE_ORDER = ["设计阶段", "制造阶段（含装配）", "试验阶段", "服役阶段"]


class _PlotTab(QWidget):
    def __init__(self, empty_text):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.figure = Figure(figsize=(6, 3), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.empty = QLabel(empty_text)
        self.empty.setWordWrap(True)
        self.empty.setStyleSheet("padding: 18px; color: #52606D; background: #F8FAFC; border: 1px solid #E5E7EB;")
        layout.addWidget(self.canvas)
        layout.addWidget(self.empty)
        self.canvas.hide()

    def show_empty(self, text=None):
        if text:
            self.empty.setText(text)
        self.figure.clear()
        self.canvas.draw_idle()
        self.canvas.hide()
        self.empty.show()

    def show_plot(self):
        self.empty.hide()
        self.canvas.show()
        self.canvas.draw_idle()


class VisualizationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #D9E2EC;
                background: white;
                border-radius: 18px;
                top: -1px;
            }
            QTabBar::tab {
                background: #F8FAFC;
                color: #334E68;
                padding: 11px 18px;
                border: 1px solid #D9E2EC;
                border-bottom: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 13px;
                font-weight: 700;
            }
            QTabBar::tab:selected {
                background: white;
                color: #0F172A;
            }
            """
        )
        layout.addWidget(self.tabs)

        self.evolution_tab = _PlotTab("选择对象并点击运行后，显示该对象跨阶段均值、标准差和可靠性变化。")
        self.comparison_tab = _PlotTab("选择对象并点击运行后，显示当前阶段各对象的标准差与可靠性对比。")
        self.summary_tab = _PlotTab("选择对象并点击运行后，显示概率、区间、模糊三类结果的综合展示。")

        self.tabs.addTab(self.evolution_tab, "跨阶段趋势")
        self.tabs.addTab(self.comparison_tab, "同阶段对比")
        self.tabs.addTab(self.summary_tab, "综合响应")

    def clear(self):
        self.evolution_tab.show_empty()
        self.comparison_tab.show_empty()
        self.summary_tab.show_empty()

    def update_plots(self, stage_data_map, selected_stage, selected_object):
        if not selected_stage or not selected_object:
            self.clear()
            return
        self._plot_stage_evolution(stage_data_map, selected_object)
        self._plot_stage_comparison(stage_data_map[selected_stage], selected_stage, selected_object)
        self._plot_summary(stage_data_map[selected_stage]["objects"][selected_object], selected_stage, selected_object)

    def _plot_stage_evolution(self, stage_data_map, object_name):
        fig = self.evolution_tab.figure
        fig.clear()
        fig.patch.set_facecolor("white")
        ax_mean = fig.add_subplot(111)
        ax_rel = ax_mean.twinx()
        ax_mean.set_facecolor("#FBFDFF")

        means = [stage_data_map[stage]["objects"][object_name]["metrics"]["mean"] for stage in STAGE_ORDER]
        stds = [stage_data_map[stage]["objects"][object_name]["metrics"]["std"] for stage in STAGE_ORDER]
        reliabilities = [stage_data_map[stage]["objects"][object_name]["metrics"]["reliability"] for stage in STAGE_ORDER]

        x = list(range(len(STAGE_ORDER)))
        ax_mean.plot(x, means, color="#1D4ED8", marker="o", linewidth=2.6, label="均值")
        ax_mean.plot(x, stds, color="#EA580C", marker="s", linewidth=2.6, label="标准差")
        ax_rel.plot(x, reliabilities, color="#059669", marker="^", linewidth=2.4, label="可靠性")

        ax_mean.set_xticks(x)
        ax_mean.set_xticklabels(STAGE_ORDER, rotation=18, ha="right")
        ax_mean.set_ylabel("均值 / 标准差")
        ax_rel.set_ylabel("可靠性")
        ax_mean.set_title(f"{object_name}跨阶段演化趋势")
        ax_mean.grid(True, linestyle="--", alpha=0.18)

        lines = ax_mean.get_lines() + ax_rel.get_lines()
        ax_mean.legend(lines, [line.get_label() for line in lines], loc="upper left")
        self.evolution_tab.show_plot()

    def _plot_stage_comparison(self, stage_bundle, stage_name, selected_object):
        fig = self.comparison_tab.figure
        fig.clear()
        fig.patch.set_facecolor("white")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#FBFDFF")

        objects = list(stage_bundle["objects"].keys())
        stds = [stage_bundle["objects"][obj]["metrics"]["std"] for obj in objects]
        reliabilities = [stage_bundle["objects"][obj]["metrics"]["reliability"] for obj in objects]
        colors = ["#0EA5E9" if obj != selected_object else "#F97316" for obj in objects]

        bars = ax.bar(objects, stds, color=colors, alpha=0.9, label="标准差")
        ax.set_ylabel("标准差")
        ax.set_title(f"{stage_name}对象响应对比")
        ax.grid(True, axis="y", linestyle="--", alpha=0.16)
        ax.tick_params(axis="x", rotation=10)

        ax2 = ax.twinx()
        ax2.plot(objects, reliabilities, color="#7C3AED", marker="o", linewidth=2.4, label="可靠性")
        ax2.set_ylabel("可靠性")

        for bar, value in zip(bars, stds):
            ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.2f}", ha="center", va="bottom", fontsize=9)

        lines = [bars, ax2.get_lines()[0]]
        ax.legend(lines, ["标准差", "可靠性"], loc="upper right")
        self.comparison_tab.show_plot()

    def _plot_summary(self, object_bundle, stage_name, object_name):
        fig = self.summary_tab.figure
        fig.clear()
        fig.patch.set_facecolor("white")
        ax_pdf = fig.add_subplot(121)
        ax_fuzzy = fig.add_subplot(122)
        ax_pdf.set_facecolor("#FBFDFF")
        ax_fuzzy.set_facecolor("#FBFDFF")

        metrics = object_bundle["metrics"]
        mean = metrics["mean"]
        std = max(metrics["std"], 1e-6)
        lower = metrics["lower"]
        upper = metrics["upper"]
        center = metrics["center"]
        fuzzy_peak = metrics["fuzzy_peak"]
        fuzzy_width = metrics["fuzzy_width"]

        left = mean - 4 * std
        right = mean + 4 * std
        xs = [left + (right - left) * i / 199 for i in range(200)]
        ys = [self._normal_pdf(x, mean, std) for x in xs]
        ax_pdf.plot(xs, ys, color="#2563EB", linewidth=2.5, label="概率密度")
        ax_pdf.axvspan(lower, upper, color="#F59E0B", alpha=0.2, label="区间响应")
        ax_pdf.axvline(center, color="#EA580C", linestyle="--", linewidth=2.0, label="区间中心值")
        ax_pdf.set_title(f"{object_name}概率/区间结果")
        ax_pdf.set_xlabel("响应值")
        ax_pdf.set_ylabel("概率密度")
        ax_pdf.grid(True, linestyle="--", alpha=0.2)
        ax_pdf.legend(loc="upper right", fontsize=9)

        fuzzy_x = [center - fuzzy_width, center, center + fuzzy_width]
        fuzzy_y = [0, fuzzy_peak, 0]
        ax_fuzzy.plot(fuzzy_x, fuzzy_y, color="#7C3AED", linewidth=2.5)
        ax_fuzzy.fill_between(fuzzy_x, fuzzy_y, color="#C4B5FD", alpha=0.45)
        ax_fuzzy.set_title(f"{object_name}模糊隶属度")
        ax_fuzzy.set_xlabel("响应值")
        ax_fuzzy.set_ylabel("隶属度")
        ax_fuzzy.set_ylim(0, 1.05)
        ax_fuzzy.grid(True, linestyle="--", alpha=0.2)
        fig.suptitle(f"{stage_name}综合响应展示", fontsize=13, fontweight="bold")
        self.summary_tab.show_plot()

    @staticmethod
    def _normal_pdf(x, mean, std):
        return math.exp(-0.5 * ((x - mean) / std) ** 2) / (std * math.sqrt(2 * math.pi))
