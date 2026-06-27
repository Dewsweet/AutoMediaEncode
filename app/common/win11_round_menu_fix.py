# coding: utf-8
"""Win11 fixes for qfluentwidgets popup menus."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QEvent
from qfluentwidgets import RoundMenu
from qfluentwidgets.components.widgets.combo_box import ComboBoxMenu
from qfluentwidgets.components.widgets.menu import MenuAnimationType


_PATCHED = False
_DWMWA_BORDER_COLOR = 34
_DWMWA_COLOR_NONE = 0xFFFFFFFE


def _is_win11_or_later() -> bool:
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


def _remove_dwm_border(hwnd) -> None:
    """Disable the Win11 one-pixel DWM frame around frameless popup windows."""
    if not _is_win11_or_later():
        return

    color = wintypes.DWORD(_DWMWA_COLOR_NONE)
    ctypes.windll.dwmapi.DwmSetWindowAttribute(
        wintypes.HWND(int(hwnd)),
        wintypes.DWORD(_DWMWA_BORDER_COLOR),
        ctypes.byref(color),
        ctypes.sizeof(color),
    )


def install_win11_round_menu_fix() -> None:
    """Patch qfluentwidgets popups to match Win10 rendering on Win11."""
    global _PATCHED
    if _PATCHED or not _is_win11_or_later():
        return

    original_event = RoundMenu.event
    original_combo_init = ComboBoxMenu.__init__
    original_round_menu_exec = RoundMenu.exec

    def event(self, e):
        result = original_event(self, e)
        if e.type() in (QEvent.Type.WinIdChange, QEvent.Type.Show):
            try:
                _remove_dwm_border(self.winId())
            except Exception:
                pass

        return result

    def combo_init(self, parent=None):
        original_combo_init(self, parent)
        self.view.setGraphicsEffect(None)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.adjustSize()

    def combo_exec(self, pos, ani=True, aniType=MenuAnimationType.DROP_DOWN):
        self.view.adjustSize(pos, aniType)
        self.adjustSize()
        return original_round_menu_exec(self, pos, False, MenuAnimationType.NONE)

    RoundMenu.event = event
    ComboBoxMenu.__init__ = combo_init
    ComboBoxMenu.exec = combo_exec
    _PATCHED = True
