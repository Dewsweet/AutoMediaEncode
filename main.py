# coding:utf-8
import sys
from contextlib import redirect_stdout
from io import StringIO

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

with redirect_stdout(StringIO()):
    from qfluentwidgets import FluentTranslator

from app.common.win11_round_menu_fix import install_win11_round_menu_fix
from app.view.main_window import MainWindow
from app.services.task_manager import taskManager  # 导入并常驻后台

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    
    app = QApplication(sys.argv)
    install_win11_round_menu_fix()

    from app.common.qt_warning_filter import install_warning_filter
    install_warning_filter()

    translation = FluentTranslator()
    app.installTranslator(translation)
    
    w = MainWindow()
    w.show()
    
    sys.exit(app.exec())
