# coding:utf-8
from qfluentwidgets import ConfigItem, qconfig, Theme, QConfig, OptionsConfigItem, OptionsValidator

class Config(QConfig):
    """ 存放应用的全局配置，继承或利用 qconfig """
    
    # 语言和个性化
    language = OptionsConfigItem("Personalization", "Language", "Auto", OptionsValidator(["Auto", "zh-CN", "en-US"]))
    bg_image_path = ConfigItem("Personalization", "BackgroundImage", "")

    # 定义 vspipe 的自定义路径配置项，默认值为空
    vspipe_path = ConfigItem("Tools", "VspipePath", "")

YEAR = 2026
AUTHOR = "Dewsweet"
WINDOW_NAME = "Auto Media Encode"
VERSION = "0.3.5 - Beta"

cfg = Config()
qconfig.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)

