from PySide6.QtCore import qInstallMessageHandler, QtMsgType


# Qt 警告关键字列表，包含任一关键字的 warning 将被静默
_IGNORED_PATTERNS = [
    'does not have a property named',
]


def _is_ignored(message: str) -> bool:
    for pattern in _IGNORED_PATTERNS:
        if pattern in message:
            return True
    return False


# 修补 qfluentwidgets FlowLayout.takeAt 的返回值类型错误
# 原代码返回 QWidget（QObject），违反 QLayout.takeAt 契约，触发 RuntimeWarning
def _patch_flow_layout():
    from qfluentwidgets.components.layout.flow_layout import FlowLayout

    def _take_at(self, index: int):
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            w = item.widget()
            if w is not None:
                ani = w.property('flowAni')
                if ani is not None:
                    self._anis.remove(ani)
                    self._aniGroup.removeAnimation(ani)
                    ani.deleteLater()
            return item  # 返回 QLayoutItem 而非 widget
        return None

    def _take_all_widgets(self):
        while self._items:
            item = self._items.pop(0)
            w = item.widget()
            if w:
                w.deleteLater()

    FlowLayout.takeAt = _take_at
    FlowLayout.takeAllWidgets = _take_all_widgets


def install_warning_filter():
    # 修补第三方库的运行时错误
    _patch_flow_layout()

    # 获取默认处理器，安装自定义过滤器
    original_handler = qInstallMessageHandler(None)

    def handler(msg_type: QtMsgType, context, message: str):
        if msg_type == QtMsgType.QtWarningMsg and _is_ignored(message):
            return  # 静默已知无害的 Qt 警告
        original_handler(msg_type, context, message)

    qInstallMessageHandler(handler)
