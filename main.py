"""
不确定性传播演示程序 —— 入口文件

架构说明（方便后续植入 UQSim）：
├── core/          核心计算层（100% 可移植）
│   ├── distribution.py    分布定义
│   └── uncertainty.py     不确定性传播算法
├── canvas/        画布渲染层（接口对齐 UQSim）
│   ├── base_node.py       节点基类
│   ├── connection.py      连线
│   ├── graphics_view.py   画布视图
│   ├── stage_node.py      跨阶段节点
│   └── container_node.py  跨层级容器节点
└── ui/            Demo 外壳层（集成时替换）
    ├── main_window.py     主窗口
    ├── toolbox_panel.py   左侧工具箱
    └── property_panel.py  右侧属性面板
"""
import sys
from PySide6.QtWidgets import QApplication
from ui import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
