# coding:utf-8
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator
from app.common.win11_round_menu_fix import install_win11_round_menu_fix
from app.view.main_window import MainWindow
from app.services.task_manager import taskManager  # 导入并常驻后台

if __name__ == '__main__':
    # 启用高 DPI 缩放支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    
    app = QApplication(sys.argv)
    install_win11_round_menu_fix()

    translation = FluentTranslator()
    app.installTranslator(translation)
    
    w = MainWindow()
    w.show()
    
    sys.exit(app.exec())
