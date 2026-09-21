# coding:utf-8
"""软件更新提示对话框：展示最新版本信息与更新日志，提供"前往下载"入口"""
from datetime import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout
from qfluentwidgets import (MessageBoxBase, SubtitleLabel, BodyLabel, TextEdit,
                            StrongBodyLabel, CaptionLabel)

from app.common.config import VERSION


class UpdateDialog(MessageBoxBase):
    """更新内容展示弹窗 (MessageBoxBase 风格)

    yesButton 为"前往下载", cancelButton 为"以后再说"
    """

    def __init__(self, release_info: dict, parent=None):
        super().__init__(parent)

        tag_name = release_info.get("tag_name", "")
        html_url = release_info.get("html_url", "")
        published_at = release_info.get("published_at", "")
        body = release_info.get("body", "")

        self.html_url = html_url

        # --- 标题 ---
        self.titleLabel = SubtitleLabel(self.tr("发现新版本"), self)

        # --- 版本信息行 ---
        self.versionWidget = None
        self.versionLayout = QHBoxLayout()
        self.localLabel = BodyLabel(self.tr("当前版本") + f": {VERSION}", self)
        self.remoteLabel = StrongBodyLabel(self.tr("最新版本") + f": {tag_name}", self)
        self.versionLayout.addWidget(self.localLabel)
        self.versionLayout.addStretch(1)
        self.versionLayout.addWidget(self.remoteLabel)

        # --- 发布日期 ---
        self.dateLabel = CaptionLabel(self._format_date(published_at), self)
        self.dateLabel.setVisible(bool(published_at))

        # --- 更新日志 ---
        self.changelogLabel = BodyLabel(self.tr("更新日志"), self)
        self.changelogTextEdit = TextEdit(self)
        if body:
            # GitHub Release body 为 Markdown 源文本，用 setMarkdown 渲染标题/列表/加粗等
            self.changelogTextEdit.setMarkdown(body)
        else:
            self.changelogTextEdit.setPlainText(self.tr("（无更新日志）"))
        self.changelogTextEdit.setReadOnly(True)

        # --- 布局 ---
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(5)
        self.viewLayout.addLayout(self.versionLayout)
        self.viewLayout.addWidget(self.dateLabel)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.changelogLabel)
        self.viewLayout.addWidget(self.changelogTextEdit, 1)

        # --- 尺寸自适应父窗口 ---
        if parent:
            target_w = max(520, int(parent.width() * 0.5))
            target_h = max(420, int(parent.height() * 0.6))
            self.widget.setFixedSize(target_w, target_h)
        else:
            self.widget.setMinimumWidth(480)
            self.widget.setMinimumHeight(380)

        # --- 按钮 ---
        self.yesButton.setText(self.tr("前往下载"))
        self.cancelButton.setText(self.tr("以后再说"))

        # 点击"前往下载"时打开 Release 页面
        self.yesButton.clicked.connect(self._on_download_clicked)

    def _format_date(self, iso_date: str) -> str:
        """将 ISO 8601 时间格式化为本地可读日期"""
        try:
            dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
            return self.tr("发布于") + ": " + dt.astimezone().strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return ""

    def _on_download_clicked(self):
        if self.html_url:
            QDesktopServices.openUrl(QUrl(self.html_url))
        self.accept()
