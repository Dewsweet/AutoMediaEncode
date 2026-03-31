# coding:utf-8
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from qfluentwidgets import FluentTranslator

from app.view.main_window import MainWindow

if __name__ == '__main__':
    # 启用高 DPI 缩放支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)

    translation = FluentTranslator()
    app.installTranslator(translation)
    
    w = MainWindow()
    w.show()
    
    sys.exit(app.exec())