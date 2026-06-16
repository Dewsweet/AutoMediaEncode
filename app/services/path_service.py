# coding:utf-8
from pathlib import Path
import sys

class PathService:
    @staticmethod
    def is_compiled() -> bool:
        """判断当前环境是否为打包后的环境"""
        return "__compiled__" in globals() or getattr(sys, 'frozen', False)

    @staticmethod
    def get_base_dir() -> Path:
        """获取项目的根目录"""
        if PathService.is_compiled():
            return Path(sys.argv[0]).resolve().parent
        else:
            return Path(__file__).resolve().parent.parent.parent
        
    @staticmethod
    def get_log_dir() -> Path:
        """获取 logs 目录的路径"""
        log_dir = PathService.get_base_dir() / "logs"
        log_dir.mkdir(exist_ok=True)
        return log_dir

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
    
    # 动态路径管理
    @staticmethod
    def get_config_dir() -> Path:
        """获取 config 目录的路径"""
        if PathService.is_compiled():
            return PathService.get_base_dir() / "config"
        else:
            return PathService.get_app_dir() / "config"
    
    @staticmethod
    def get_json_dir() -> Path:
        """获取 json 目录的路径"""
        if PathService.is_compiled():
            return PathService.get_base_dir() / "data" / "json"
        else:
            return PathService.get_common_dir() / "json"
