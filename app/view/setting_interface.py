# coding:utf-8
import os
import shutil
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog

from qfluentwidgets import (ScrollArea, SettingCardGroup, ExpandGroupSettingCard, OptionsSettingCard, CustomColorSettingCard, PrimaryPushSettingCard, ComboBoxSettingCard, PushSettingCard, 
                            qconfig, setTheme, setThemeColor, 
                            TitleLabel, CaptionLabel, BodyLabel, ToolButton, InfoBar, InfoBarPosition, ToolTipFilter)

from qfluentwidgets import FluentIcon as FIF

from app.components.preset_dialog import PresetManagerDialog
from app.components.tools_template_card import MediaToolsCardTemplate
from app.services.setting.preset_service import preset_service
from app.services.tool_service import ToolService
from app.services.path_service import PathService
from app.common.config import cfg, VERSION, AUTHOR, YEAR
from app.common.style_sheet import StyleSheet


class SettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SettingInterface")

        self.mainPage = QWidget()
        self.mainPage.setObjectName("SettingMainPage")
        self.mainLayout = QVBoxLayout(self.mainPage)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.headerArea = QWidget()
        self.headerAreaVLayout = QVBoxLayout(self.headerArea)
        self.headerAreaVLayout.setContentsMargins(30, 30, 30, 20)

        self.scrollBox = QWidget()
        self.scrollBox.setObjectName("scrollBox")
        self.scrollBoxVLayout = QVBoxLayout(self.scrollBox)
        self.scrollBoxVLayout.setContentsMargins(30, 20, 30, 20)
        self.scrollArea = ScrollArea(self)
        self.scrollArea.setWidget(self.scrollBox) 
        self.scrollArea.setWidgetResizable(True)
        StyleSheet.SETTING_INTERFACE.apply(self)


        self.titleLabel = TitleLabel("设置")

        self._toolsCardArea()
        self._customCardArea()
        self._aboutCardArea()
        self._initLayout()
        self._connectSignalToSlot()

    def _toolsCardArea(self):
        self.toolsCardGroup = SettingCardGroup(self.tr("工具选项"), self.scrollBox)

        # 媒体工具检查卡片
        self.toolsCheckCard = ExpandGroupSettingCard(FIF.MEDIA, "媒体工具", "本软件所用到的基本媒体处理工具", self.toolsCardGroup)

        self.toolsCheckCardFuncBtnBox = QWidget()
        self.toolsCheckCardFuncBtnBoxLayout = QHBoxLayout(self.toolsCheckCardFuncBtnBox)
        self.toolsCheckCardFuncBtnBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.download_Tools_Button = ToolButton(FIF.DOWNLOAD, self.toolsCheckCard)
        self.download_Tools_Button.setToolTip("下载工具")
        self.download_Tools_Button.installEventFilter(ToolTipFilter(self.download_Tools_Button))
        self.open_tools_folder_button = ToolButton(FIF.FOLDER, self.toolsCheckCard)
        self.open_tools_folder_button.setToolTip("打开工具文件夹")
        self.open_tools_folder_button.installEventFilter(ToolTipFilter(self.open_tools_folder_button))

        self.toolsCheckCardFuncBtnBoxLayout.addWidget(self.download_Tools_Button)
        self.toolsCheckCardFuncBtnBoxLayout.addWidget(self.open_tools_folder_button)
        self.toolsCheckCardFuncBtnBoxLayout.setSpacing(10)

        self.toolsCheckCard.addWidget(self.toolsCheckCardFuncBtnBox)

        self.tool_widgets = {}
        for tool in ToolService.TOOLS_METADATA:
            card = MediaToolsCardTemplate(tool["title"], tool["desc"])

            if tool["url"]:
                card.setWebsite(tool["url"])

            if tool["is_costom"]:
                card.addVSpipe(True)
                custom_path = qconfig.get(cfg.vspipe_path)
                state = ToolService.check_tool_exists(tool["tool_name"], custom_path)
                
                if custom_path:
                    card.setSubtitle(custom_path)
                    
                card.vspipePathButton.clicked.connect(self._on_vspipe_button_clicked)
            else:
                state = ToolService.check_tool_exists(tool["tool_name"])

            card.checkState(state)
            self.toolsCheckCard.addGroupWidget(card)

            # 保存引用防止被垃圾回收，并且方便后续更新状态
            self.tool_widgets[tool["tool_name"]] = card
            
        # 编码器预设卡片
        self.encoderPresetCard = ExpandGroupSettingCard(FIF.SETTING, "编码器预设", "基础编码器相关参数的预设", self.toolsCardGroup)

        # 导出预设选项的全局按钮 (放在预设卡片右上方)
        self.exportPresetBtn = ToolButton(FIF.SAVE, self.encoderPresetCard)
        self.exportPresetBtn.setToolTip("导出所有预设")
        self.exportPresetBtn.installEventFilter(ToolTipFilter(self.exportPresetBtn))
        self.encoderPresetCard.addWidget(self.exportPresetBtn)

        self.x264PresetButton = ToolButton(FIF.EDIT, self.encoderPresetCard)
        self.x264PresetButton.setFixedSize(30, 30)
        self.x265PresetButton = ToolButton(FIF.EDIT, self.encoderPresetCard)
        self.x265PresetButton.setFixedSize(30, 30)
        self.svtav1PresetButton = ToolButton(FIF.EDIT, self.encoderPresetCard)
        self.svtav1PresetButton.setFixedSize(30, 30)

        self.encoderPresetCard.viewLayout.setContentsMargins(0, 0, 10, 0)
        self.encoderPresetCard.viewLayout.setSpacing(0)

        self.encoderPresetCard.addGroup(QIcon(), "x264", self.tr("H.264/AVC 编码器"), self.x264PresetButton)
        self.encoderPresetCard.addGroup(QIcon(), "x265", self.tr("H.265/HEVC 编码器"), self.x265PresetButton)
        self.encoderPresetCard.addGroup(QIcon(), "SVTAV1", self.tr("SVT-AV1 编码器"), self.svtav1PresetButton)
            
    def _customCardArea(self):
        self.customCardGroup = SettingCardGroup(self.tr("个性化"), self.scrollBox)

        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr("语言 (Language)"),
            self.tr("选择软件的显示语言"),
            texts=["系统默认", "简体中文", "English"],
            parent=self.customCardGroup
        )

        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            "应用主题",
            "调整你的应用外观",
            texts=["浅色", "深色", "跟随系统设置"],
            parent=self.customCardGroup
        )

        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            "主题颜色",
            "自定义你的主题颜色",
            parent=self.customCardGroup
        )

        self.bgImageCard = PushSettingCard(
            self.tr("选择图片"),
            FIF.PHOTO,
            self.tr("自定义背景图片"),
            self.tr("让程序界面更加花里胡哨😋") + (f" (当前: {Path(qconfig.get(cfg.bg_image_path)).name})" if qconfig.get(cfg.bg_image_path) else ""),
            parent=self.customCardGroup
        )
        self.clearBgButton = ToolButton(FIF.DELETE, self.bgImageCard)
        self.clearBgButton.setToolTip("清除背景图片")
        self.clearBgButton.installEventFilter(ToolTipFilter(self.clearBgButton))
        
        self.bgImageCard.hBoxLayout.addWidget(self.clearBgButton) 
        self.bgImageCard.hBoxLayout.addSpacing(20)
            
    def _aboutCardArea(self):
        self.aboutCardGroup = SettingCardGroup(self.tr("关于"), self.scrollBox)

        self.helpCard = ExpandGroupSettingCard(FIF.HELP, "帮助", "使用说明和常见问题", self.aboutCardGroup)
        self.helpNoteBox = QWidget()
        self.helpNoteBoxLayout = QVBoxLayout(self.helpNoteBox)

        self.helpNoteLineEdit = BodyLabel(self)
        self.helpNoteLineEdit.setText(
            "并非AI时代的一时兴起, 只是在AI时代下, 自己写点东西更佳简便   \n" \
            "本软件适合有一点基础的用户上手, 但普通功能也尽量的方便理解使用  \n" \
            "感谢VCB-Studio和谜之压制组的开源, 关于媒体处理和编码器可以参考他们的教程  \n" \
            "VCB-Studio 公开教程: https://guides.vcb-s.com/  \n" \
            "谜之压制组 压制教程: https://iavoe.github.io/"
        )

        self.helpNoteBoxLayout.addWidget(self.helpNoteLineEdit)
        self.helpCard.addGroupWidget(self.helpNoteBox)

        self.aboutCard = PrimaryPushSettingCard(
            self.tr('检查更新'),
            FIF.INFO,
            self.tr('关于'),
            '© ' + self.tr('Copyright') + " " + str(YEAR) + ", " + AUTHOR + ". " +
            self.tr('Version') + " " + VERSION,
            self.aboutCardGroup
        )


    def _initLayout(self):
        self.toolsCardGroup.addSettingCard(self.toolsCheckCard)
        self.toolsCardGroup.addSettingCard(self.encoderPresetCard)

        self.customCardGroup.addSettingCard(self.languageCard)
        self.customCardGroup.addSettingCard(self.themeCard)
        self.customCardGroup.addSettingCard(self.themeColorCard)
        self.customCardGroup.addSettingCard(self.bgImageCard)

        self.aboutCardGroup.addSettingCard(self.helpCard)
        self.aboutCardGroup.addSettingCard(self.aboutCard)


        self.headerAreaVLayout.addWidget(self.titleLabel)

        self.scrollBoxVLayout.addWidget(self.toolsCardGroup)
        self.scrollBoxVLayout.addWidget(self.customCardGroup)
        self.scrollBoxVLayout.addWidget(self.aboutCardGroup)
        self.scrollBoxVLayout.addStretch(1)


        self.mainLayout.addWidget(self.headerArea)
        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)

    def _connectSignalToSlot(self):
        qconfig.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))

        # 绑定工具目录按钮
        self.open_tools_folder_button.clicked.connect(self._on_open_tools_folder_clicked)
        self.download_Tools_Button.clicked.connect(self._on_download_tools_clicked)

        # 绑定导出预设按钮
        self.exportPresetBtn.clicked.connect(self._on_export_presets_clicked)

        # 绑定编码器预设按钮
        self.x264PresetButton.clicked.connect(lambda: self._show_preset_dialog("x264"))
        self.x265PresetButton.clicked.connect(lambda: self._show_preset_dialog("x265"))
        self.svtav1PresetButton.clicked.connect(lambda: self._show_preset_dialog("SVTAV1"))

        # 绑定背景图片按钮
        self.bgImageCard.clicked.connect(self._on_choose_bg_image_clicked)
        self.clearBgButton.clicked.connect(self._on_clear_bg_image_clicked)

        # 检查更新按钮
        self.aboutCard.clicked.connect(self._check_for_updates)


    def _on_open_tools_folder_clicked(self):
        """打开存放工具的本地文件夹"""
        tools_path = PathService.get_tools_dir()
        if not tools_path.exists():
            tools_path.mkdir(parents=True, exist_ok=True) # 如果没有就创建一个
        # Windows 具体打开文件夹
        os.startfile(str(tools_path))
        
    def _on_download_tools_clicked(self):
        """下载工具(预留位)"""
        # TODO: 这里之后可以写个弹窗，利用 QThread 或 QNetworkAccessManager 从后台下载压缩包
        # 流程：下载 -> 解压 -> 将文件移入 PathService.get_tools_dir()
        # 下载和解压成功后，可以调用 self.update_tools_state() 重新检查图标
        pass

    def _on_vspipe_button_clicked(self):
        """选择 vspipe 路径并更新"""
        path, _ = QFileDialog.getOpenFileName(self, "选择 vspipe", "", "可执行文件 (*.exe);;所有文件 (*.*)")
        if path:
            p = Path(path)
            card = self.tool_widgets.get("vspipe")
            
            if p.stem.lower() == "vspipe":
                path_str = str(p.resolve())
                qconfig.set(cfg.vspipe_path, path_str) # 保存到全局设置
                
                # 更新指定卡片的 UI
                if card:
                    card.setSubtitle(path_str)
                    state = ToolService.check_tool_exists("vspipe", path_str)
                    card.checkState(state)
            else:
                if card:
                    card.setSubtitle("错误: 选定的文件不是 vspipe 程序, 请检查文件名")
                    card.checkState(False)

    def _show_preset_dialog(self, encoder_name):
        """展示编码器预设管理弹窗"""
        dialog = PresetManagerDialog(encoder_name, self.window())
        dialog.exec()        

    def _on_export_presets_clicked(self):
        """将内置的 custom_preset.json 导出给用户"""
        save_path, _ = QFileDialog.getSaveFileName(
            self, "导出预设", "custom_preset.json", "JSON 文件 (*.json)"
        )
        if save_path:
            try:
                shutil.copy2(preset_service.preset_file_path, save_path)
                InfoBar.success(
                    title='导出成功',
                    content=f"预设已成功导出", 
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    title='导出失败',
                    content=f"错误信息：{str(e)}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=4000,
                    parent=self
                )

    def _on_clear_bg_image_clicked(self):
        """恢复无图片状态"""
        qconfig.set(cfg.bg_image_path, "")
        self.bgImageCard.setContent(self.tr("让程序界面更加花里胡哨😋") + " (当前: 默认纯色)")
        if self.window():
            self.window().update()

    def _on_choose_bg_image_clicked(self):
        """选择自定义背景图片"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)"
        )
        if path:
            qconfig.set(cfg.bg_image_path, path)
            self.bgImageCard.setContent(self.tr("让程序界面更加花里胡哨😋") + f" (当前: {Path(path).name})")
            # 发送更新信号给主窗口
            if self.window():
                self.window().update()

    def _check_for_updates(self):
        """检查更新 (暂时用Github页面链接)"""
        QDesktopServices.openUrl("https://github.com/Dewsweet/AutoMediaEncode")

    def update_tools_state(self):
        """重新检测所有普通工具的状态，不需要重启软件就能刷新状态"""
        # 清空路径缓存，强制重新检测磁盘
        ToolService.force_clear_cache()
        
        # 当把工具下好，或者把文件拖入之后，只要调用这个方法，即可更新前面的圆圈
        # 排除掉特殊需要自定义路径的 vspipe (也可以传参强制更新)
        for t in ToolService.TOOLS_METADATA:
            if t["is_costom"]:
                continue
            card = self.tool_widgets.get(t["key"])
            if card:
                state = ToolService.check_tool_exists(t["tool_name"])
                card.checkState(state)
