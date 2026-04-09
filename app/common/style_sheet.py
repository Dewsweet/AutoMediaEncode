# coding: utf-8
from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, isDarkTheme, qconfig
from ..services.path_service import PathService

# 继承
class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    RECODE_CARD_INTERFACE = "recode_card_interface"
    RECODE_INTERFACE = "recode_interface"
    TASK_INTERFACE = "task_interface"
    SETTING_INTERFACE = "setting_interface"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme 
        resource = PathService.get_resource_dir()
        return f"{resource}/qss/{theme.value.lower()}/{self.value}.qss"
