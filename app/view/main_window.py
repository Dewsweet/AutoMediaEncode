from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from qfluentwidgets import FluentWindow, NavigationItemPosition
from qfluentwidgets import FluentIcon as FIF

from .mediainfo_interface import MediaifInterface
from .setting_interface import SettingInterface

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()

        self.initWindow()

        # 创建子页面实例
        self.mediaInfoInterface = MediaifInterface(self)
        self.settingInterface = SettingInterface(self)
        self.initNavigation()


    def initWindow(self):
        self.resize(900, 700)
        self.setWindowTitle('Auto Mdia Encode')
        self.setMinimumSize(600, 500)

        # 将窗口移动到屏幕中央
        desktop = QApplication.primaryScreen().availableGeometry() 
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)


    def initNavigation(self):
        # 添加子页面到侧边导航栏
        self.addSubInterface(self.mediaInfoInterface, FIF.INFO, 'Media Info')


        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Setting', NavigationItemPosition.BOTTOM)


