# coding:utf-8
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (InfoBarIcon, BodyLabel, CaptionLabel, 
                            IconWidget, PushButton, HyperlinkButton)
from qfluentwidgets import FluentIcon as FIF

class MediaToolsCardTemplate(QWidget):
    def __init__(self, title, subtitle, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(60)

        self.mainLayout = QVBoxLayout(self)

        self.hBox = QWidget()
        self.hBoxLayout = QHBoxLayout(self.hBox)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.vBox = QWidget()
        self.vBoxLayout = QVBoxLayout(self.vBox)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)


        # Widget
        self.titleLabel = BodyLabel(title)
        self.subtitleLabel = CaptionLabel(subtitle)
        self.subtitleLabel.setFont(QFont("Microsoft YaHei", 8))
        self.subtitleLabel.setStyleSheet("color: gray;")

        self.stateIcon = IconWidget()
        self.stateIcon.setFixedSize(20, 20)

        self.websiteButton = HyperlinkButton(self)
        self.websiteButton.setVisible(False)

        self.vspipePathButton = PushButton("...", self)
        self.vspipePathButton.setFixedSize(40, 30)
        self.vspipePathButton.setVisible(False)


        # Layout
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.setSpacing(0)

        self.hBoxLayout.addWidget(self.stateIcon)
        self.hBoxLayout.addSpacing(10)
        self.hBoxLayout.addWidget(self.vBox)
        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.websiteButton)
        self.hBoxLayout.addSpacing(0)
        self.hBoxLayout.addWidget(self.vspipePathButton)

        self.mainLayout.addWidget(self.hBox)
        self.mainLayout.setContentsMargins(50, 10, 55, 10)

        self.setLayout(self.mainLayout)

    def addVSpipe(self, bool):
        if bool:
            self.mainLayout.setContentsMargins(50, 10, 10, 10)
            self.vspipePathButton.setVisible(True)

    def setWebsite(self, url: str):
        self.websiteButton.setUrl(QUrl(url))
        self.websiteButton.setText(self.tr("软件官网"))
        self.websiteButton.setIcon(FIF.LINK)
        self.websiteButton.setVisible(True) 

    def checkState(self, state: bool):
        if state:
            self.stateIcon.setIcon(InfoBarIcon.SUCCESS)
        else:
            self.stateIcon.setIcon(InfoBarIcon.WARNING)
            
    def setSubtitle(self, subtitle: str):
        self.subtitleLabel.setText(subtitle)

