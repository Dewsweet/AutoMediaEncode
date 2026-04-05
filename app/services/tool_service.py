# coding:utf-8
from pathlib import Path
import sys
import shutil

from .path_service import PathService

class ToolService:
    # 定义全局可复用的工具配置列表
    # 这个列表之后不仅可用于生成设置界面，还能用来统一管理各个工具的注册情况。
    TOOLS_METADATA = [
        {
            "tool_name": "ffmpeg",
            "folder": "ffmpeg",
            "type": ".exe",
            "title": "FFMpeg", 
            "desc": "领先的多媒体框架", 
            "url": "https://ffmpeg.org/", 
            "is_costom": False
            },
        {
            "tool_name": "MediaInfo", 
            "folder": "mediainfo",
            "type": ".dll",
            "title": "MediaInfo", 
            "desc": "媒体文件信息分析工具", 
            "url": "https://mediaarea.net/MediaInfo", 
            "is_costom": False
            },
        {
            "tool_name": "mkvmerge", 
            "folder": "mkvtoolnix",
            "type": ".exe",
            "title": "MKVToolNix", 
            "desc": "MKV 混流工具", 
            "url": "https://www.matroska.org/index.html", 
            "is_costom": False
            },
        {
            "tool_name": "x264",
            "folder": "x26x",
            "type": ".exe",
            "title": "x264",
            "desc": "H.264 视频编码器",
            "url": "https://www.videolan.org/developers/x264.html",
            "is_costom": False
        },
        {
            "tool_name": "x265",
            "folder": "x26x",
            "type": ".exe",
            "title": "x265",
            "desc": "H.265 视频编码器",
            "url": "https://www.videolan.org/developers/x265.html",
            "is_costom": False
        },
        {
            "tool_name": "SvtAv1",
            "folder": "svtav1",
            "type": ".exe",
            "title": "SVT-AV1",
            "desc": "SVT-AV1 视频编码器",
            "url": "https://gitlab.com/AOMediaCodec/SVT-AV1",
            "is_costom": False
        },
        {
            "tool_name": "vspipe", 
            "folder": "",
            "type": ".exe",
            "title": "VapourSynth", 
            "desc": "强大的视频处理框架", 
            "url": "https://github.com/vapoursynth/vapoursynth", 
            "is_costom": True},
    ]

    # 维护一个工具路径的缓存，避免频繁访问磁盘
    _tool_path_cache = {}

    @staticmethod
    def check_tool_exists(tool_name: str, custom_path: str = None) -> bool:
        """
        检查工具是否存在
        1. 如果提供了 custom_path 优先检查 custom_path。
        2. 否则检查根目录下的 tools 文件夹。
        3. 如果 tools 下没有
        
        ，最后使用 shutil.which 检查系统环境变量 Path 中是否存在。
        """
        # 1. 检查自定义路径（例如 vspipe 专用的自定义路径）
        if custom_path:
            p = Path(custom_path)
            if p.is_file():
                return True

        for tool in ToolService.TOOLS_METADATA:
            if tool["tool_name"].lower() == tool_name.lower():
                tool_name = tool["tool_name"] + tool["type"]
                folder = tool["folder"]
                break
        
        # 2. 检查本地 tools 目录
        local_path = PathService.get_tools_dir() / folder / tool_name
        if local_path.is_file():
            return True

        # 3. 检查系统环境变量
        if shutil.which(tool_name):
            return True

        return False

    @staticmethod
    def get_tool_path(tool_name: str, custom_path: str = None) -> str:
        """
        获取工具的实际可执行路径（如果有）。
        这也是其他功能面板调用 CLI 程序时获取路径的统一入口。
        返回字符串路径，如果没找到则返回 None。
        """
        if custom_path:
            p = Path(custom_path)
            if p.is_file():
                return str(p.resolve())

        for tool in ToolService.TOOLS_METADATA:
            if tool["tool_name"].lower() == tool_name.lower():
                tool_name = tool["tool_name"] + tool["type"]
                folder = tool["folder"]
                break
        
        local_path = PathService.get_tools_dir() / folder / tool_name
        if local_path.is_file():
            return str(local_path.resolve())    

        system_path = shutil.which(tool_name)
        if system_path:
            return str(Path(system_path).resolve())

        return None
    
    @staticmethod
    def force_clear_cache(tool_name: str):
        """强制清除某个工具的路径缓存（如果有）"""
        if tool_name in ToolService._tool_path_cache:
            del ToolService._tool_path_cache[tool_name]