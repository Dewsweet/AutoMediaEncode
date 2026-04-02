# coding:utf-8
from pathlib import Path
import sys

class PathService:
    @staticmethod
    def get_base_dir() -> Path:
        """获取项目的根目录，兼容开发环境和打包后的环境"""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            # 目前 tools 文件夹位于 main.py 同目录下
            return Path(__file__).resolve().parent.parent.parent
        
    @staticmethod
    def get_tools_dir() -> Path:
        """获取 tools 文件夹的路径"""
        return PathService.get_base_dir() / "tools" 
    
    @staticmethod
    def get_app_dir() -> Path:
        """获取 app 目录的路径"""
        return PathService.get_base_dir() / "app"
    
    @staticmethod
    def get_component_dir() -> Path:
        """获取 components 目录的路径"""
        return PathService.get_app_dir() / "components"
    
    @staticmethod
    def get_common_dir() -> Path:
        """获取 common 目录的路径"""
        return PathService.get_app_dir() / "common"
    
    @staticmethod
    def get_resource_dir() -> Path:
        """获取 resource 目录的路径"""
        return PathService.get_app_dir() / "resource"
    
    @staticmethod
    def get_config_dir() -> Path:
        """获取 config 目录的路径"""
        return PathService.get_app_dir() / "config"
