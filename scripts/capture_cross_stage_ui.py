from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ui.main_window import MainWindow


OUT_DIR = ROOT / "generated_results" / "cross_stage_demo"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window._enter_editor("cross_stage")
    window.workflow_canvas.load_demo_workflow("cross_stage")
    window.resize(1720, 980)
    window.show()

    def grab() -> None:
        app.processEvents()
        pixmap = window.grab()
        pixmap.save(str(OUT_DIR / "00_platform_cross_stage_workflow.png"))
        app.quit()

    QTimer.singleShot(800, grab)
    app.exec()


if __name__ == "__main__":
    main()
