from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPainter, QColor, QPixmap
from PySide6.QtCore import Qt

from qfluentwidgets import FluentWindow, NavigationItemPosition
from qfluentwidgets import FluentIcon as FIF, qconfig, isDarkTheme

from .mediainfo_interface import MediaifInterface
from .setting_interface import SettingInterface
from .recode_interface import RecodeInterface
from .task_interface import TaskInterface
from app.common.config import cfg, WINDOW_NAME, AUTHOR, VERSION

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        self.initWindow()

        # 创建子页面实例
        self.mediaInfoInterface = MediaifInterface(self)
        self.settingInterface = SettingInterface(self)
        self.recodeInterface = RecodeInterface(self)
        self.taskInterface = TaskInterface(self)
        self.initNavigation()
        

        # 背景图片缓存，避免每帧重复读取硬盘导致严重卡顿
        self._bg_image_path = None # 当前缓存的背景图片路径，只有当这个路径变化了才会重新从硬盘加载图片
        self._bg_pixmap = None # 原始背景图片的 QPixmap 对象，加载后就缓存起来
        self._scaled_pixmap = None # 根据当前窗口尺寸缩放后的背景图片缓存，只有当窗口尺寸变化了才会重新生成这个对象
        self._last_size = None # 记录上次生成缩放图时的窗口尺寸，避免不必要的缩放计算

        # 监听背景图片配置的改变
        qconfig.themeChanged.connect(self.repaint)
        qconfig.themeColorChanged.connect(self.repaint)
        # 如果配置文件被手动修改了，这里没有专门的信号，但我们可以在界面选好后让他触发 repaint。
        # 暂时在 setting_interface_on_choose... 里面触发 app 的全局更新，但最简单的还是我们给 cfg 单独的绑定
        # cfg 里面没有 bg_image_path 直接的信号，我们就依赖界面操作。
        
    def _update_bg_cache(self, w, h):
        """更新和缩放背景图的缓存对象"""
        bg_path = qconfig.get(cfg.bg_image_path)
        
        # 只有路径变化了才重新从硬盘读图片
        if bg_path != self._bg_image_path:
            self._bg_image_path = bg_path
            if bg_path and bg_path != "": 
                self._bg_pixmap = QPixmap(bg_path)
            else:
                self._bg_pixmap = None
            # 路径换了，必须重新生成缩放缩略图
            self._scaled_pixmap = None

        # 只要存在原始图片，检查是否需要重新生成缩放版本的图片（窗口尺寸变化时）
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            if self._last_size != (w, h) or self._scaled_pixmap is None:
                self._scaled_pixmap = self._bg_pixmap.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self._last_size = (w, h)
        else:
            self._scaled_pixmap = None

    def paintEvent(self, e):
        super().paintEvent(e)
        
        w, h = self.width(), self.height()
        self._update_bg_cache(w, h)

        if self._scaled_pixmap:
            painter = QPainter(self)
            painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
            
            # 画缓存里这帧已经渲染好的图
            x = (w - self._scaled_pixmap.width()) // 2
            y = (h - self._scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, self._scaled_pixmap)

            # 绘制半透明滤镜遮罩
            if isDarkTheme():
                overlay_color = QColor(0, 0, 0, 180) # 深色：黑色半透明滤镜
            else:
                overlay_color = QColor(255, 255, 255, 180) # 浅色：白色半透明滤镜,

            painter.fillRect(self.rect(), overlay_color)


    def initWindow(self):
        self.resize(900, 700)
        self.setWindowTitle(WINDOW_NAME + " " + VERSION)
        self.setMinimumSize(600, 500)
        
        # 强制将内部各层背景设为透明，否则主窗口画的背景图片会被覆盖
        # self.stackedWidget.setStyleSheet("background: transparent;")
        
        # 将窗口移动到屏幕中央
        desktop = QApplication.primaryScreen().availableGeometry() 
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)


    def initNavigation(self):
        # 添加子页面到侧边导航栏
        self.addSubInterface(self.mediaInfoInterface, FIF.INFO, 'Media Info')
        self.addSubInterface(self.recodeInterface, FIF.MEDIA, 'Recode')

        self.addSubInterface(self.taskInterface, FIF.ADD, 'Task Progress', NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Setting', NavigationItemPosition.BOTTOM)


