from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import FluentIcon as FIF, TitleLabel, CaptionLabel, PrimaryPushButton, PushButton

class HeaderWidget(QWidget):
    def __init__(self, title:str, subtitle:str, start_name:str, parent=None):
        super().__init__(parent)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.buttonBox = QWidget(self)
        self.buttonHLayout = QHBoxLayout(self.buttonBox)
        self.buttonHLayout.setContentsMargins(0, 10, 0, 0)
        

        self.title_label = TitleLabel(title, self)
        self.subtitle_label = CaptionLabel(subtitle, self)
        self.subtitle_label.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))

        self.reload_button = PushButton(FIF.ADD, '重载文件', self)
        self.start_button = PrimaryPushButton(FIF.PLAY, start_name, self)

        self.buttonHLayout.addStretch(1)
        self.buttonHLayout.addWidget(self.reload_button, alignment=Qt.AlignRight)
        self.buttonHLayout.addWidget(self.start_button, alignment=Qt.AlignRight)

        self.mainLayout.addWidget(self.title_label)
        self.mainLayout.addWidget(self.subtitle_label)
        self.mainLayout.addWidget(self.buttonBox, alignment=Qt.AlignRight)
        self.mainLayout.setAlignment(Qt.AlignTop)
        self.mainLayout.setSpacing(0)




