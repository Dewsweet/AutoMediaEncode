# coding: utf-8
"""在创建窗口之前安装翻译，语言设置重启后生效。"""
from PySide6.QtCore import QLocale, QTranslator
from qfluentwidgets import FluentTranslator

from . import resource
from .logger import logger


def resolve_language(preference: str, system_locale: QLocale | None = None) -> str:
    """将已有配置值映射为 Qt locale；Auto 按系统语言选择中英文。"""
    if preference == "zh-CN":
        return "zh_CN"
    if preference == "en-US":
        return "en_US"
    locale = system_locale if system_locale is not None else QLocale.system()
    return "zh_CN" if locale.language() == QLocale.Language.Chinese else "en_US"


def install_translations(app, preference: str) -> list[QTranslator]:
    """安装 Qt、Fluent、AME 翻译，返回需要保持存活的译者列表。"""
    language = resolve_language(preference)
    translators = []

    ame = QTranslator(app)
    if language == "en_US":
        if not ame.load(":/app/i18n/ame_en_US.qm") or ame.isEmpty():
            logger.error("AME 英文翻译资源加载失败，本次启动回退简体中文")
            language = "zh_CN"

    # Qt 与 Fluent 的源码是英文，英文模式直接使用原文。
    if language == "zh_CN":
        qt = QTranslator(app)
        if qt.load(":/app/i18n/qt/qtbase_zh_CN.qm") and not qt.isEmpty():
            translators.append(qt)
        else:
            logger.warning("Qt 简体中文翻译资源加载失败: qtbase_zh_CN.qm")

    fluent = FluentTranslator(QLocale(language), parent=app)
    if not fluent.isEmpty():
        translators.append(fluent)
    elif language == "zh_CN":
        logger.warning("Fluent Widgets 简体中文翻译资源加载失败")

    if language == "en_US":
        translators.append(ame)
    for translator in translators:
        app.installTranslator(translator)
    logger.info(f"界面语言: {preference} -> {language}")
    return translators
