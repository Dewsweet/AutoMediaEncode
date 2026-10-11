# coding:utf-8
"""AutoMediaEncode 程序入口：应用设置、翻译、主窗口与事件循环。"""
import os
import sys
from contextlib import redirect_stdout
from io import StringIO


def main() -> int:
    # 从快捷方式或其他目录启动时，也使用应用根目录；兼容 Nuitka 打包路径。
    from app.services.path_service import PathService
    os.chdir(PathService.get_base_dir())

    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    # PySide6 默认启用高 DPI；这些设置必须先于 QApplication 创建。
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    app = QApplication(sys.argv)

    # 仅隐藏第三方库的首次导入提示，不重定向程序运行期的输出。
    with redirect_stdout(StringIO()):
        from app.common.config import AUTHOR, VERSION, cfg
        from app.common.i18n import install_translations

    app.setApplicationName('AutoMediaEncode')
    app.setApplicationVersion(VERSION)
    app.setOrganizationName(AUTHOR)

    from app.common.win11_round_menu_fix import install_win11_round_menu_fix
    from app.common.qt_warning_filter import install_warning_filter
    install_win11_round_menu_fix()
    install_warning_filter()

    # 先安装翻译再导入和创建窗口，并保持译者引用到事件循环结束。
    translators = install_translations(app, cfg.get(cfg.language))
    window = None
    try:
        from app.view.main_window import MainWindow
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception:
        from app.common.logger import logger
        logger.exception('AutoMediaEncode 启动或运行异常')
        raise
    finally:
        if window is not None:
            window.shutdown()


if __name__ == '__main__':
    sys.exit(main())
