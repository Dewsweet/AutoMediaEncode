# coding:utf-8
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import TitleLabel

class SettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SettingInterface")

        self.vBoxLayout = QVBoxLayout(self)
        
        self.titleLabel = TitleLabel("设置页面", self)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        
        self.vBoxLayout.addWidget(self.titleLabel)