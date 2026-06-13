# coding:utf-8
from pathlib import Path
import sys
import shutil

from .path_service import PathService

class ToolService:
    """工具路径解析服务，负责根据工具名称和配置解析出可执行文件的绝对路径"""
    TOOLS_METADATA = [
        {
            "tool_name": "ffmpeg",
            "folder": "ffmpeg",
            "type": ".exe",
            "aliases": [],
            "title": "FFMpeg",
            "desc": "领先的多媒体框架",
            "url": "https://ffmpeg.org/",
            "is_custom": False,
        },
        {
            "tool_name": "MediaInfo",
            "folder": "mediainfo",
            "type": ".dll",
            "aliases": [],
            "title": "MediaInfo",
            "desc": "媒体文件信息分析工具",
            "url": "https://mediaarea.net/MediaInfo",
            "is_custom": False,
        },
        {
            "tool_name": "mkvmerge",
            "folder": "mkvtoolnix",
            "type": ".exe",
            "aliases": [
                "mkvmerge.exe",
                "mkvextract", "mkvextract.exe",
                "mkvinfo", "mkvinfo.exe",
                "mkvpropedit", "mkvpropedit.exe",
            ],
            "title": "MKVToolNix",
            "desc": "MKV 混流工具",
            "url": "https://www.matroska.org/index.html",
            "is_custom": False,
        },
        {
            "tool_name": "x264",
            "folder": "x26x",
            "type": ".exe",
            "aliases": [
                "x264.exe", 
                "x264_64", "x264_64.exe",
                "x264-x64", "x264-x64.exe",
            ],
            "title": "x264",
            "desc": "H.264 视频编码器",
            "url": "https://www.videolan.org/developers/x264.html",
            "is_custom": False,
        },
        {
            "tool_name": "x265",
            "folder": "x26x",
            "type": ".exe",
            "aliases": [
                "x265.exe", 
                "x265_64", "x265_64.exe",
                "x265-x64", "x265-x64.exe",
            ],
            "title": "x265",
            "desc": "H.265 视频编码器",
            "url": "https://www.videolan.org/developers/x265.html",
            "is_custom": False,
        },
        {
            "tool_name": "SvtAv1",
            "folder": "svtav1",
            "type": ".exe",
            "aliases": [
                "SvtAv1EncApp", "SvtAv1EncApp.exe",
                "SvtAv1.exe", "svt_av1", "svt-av1",
            ],
            "title": "SVT-AV1",
            "desc": "SVT-AV1 视频编码器",
            "url": "https://gitlab.com/AOMediaCodec/SVT-AV1",
            "is_custom": False,
        },
        {
            "tool_name": "qaac",
            "folder": "qaac",
            "type": ".exe",
            "aliases": ["qaac.exe"],
            "title": "qaac",
            "desc": "AAC 音频编码器，基于 Apple 的 CoreAudio",
            "url": "https://github.com/nu774/qaac",
            "is_custom": False,
        },
        {
            "tool_name": "vspipe",
            "folder": "",
            "type": ".exe",
            "aliases": ["vspipe.exe"],
            "title": "VapourSynth",
            "desc": "强大的视频处理框架; 不影响软件的基本功能, 有需要请自行指定位置",
            "url": "https://github.com/vapoursynth/vapoursynth",
            "is_custom": True,
        },
    ]

    # 工具路径缓存 { name_lower: str|None }
    _tool_path_cache: dict[str, str | None] = {}

    @staticmethod
    def _resolve_metadata(name: str) -> dict:
        """根据名称或别名匹配 TOOLS_METADATA, 找不到时返回降级条目"""
        raw = name.lower().strip()
        for entry in ToolService.TOOLS_METADATA:
            candidates = [entry["tool_name"].lower()]
            candidates.extend(a.lower() for a in entry.get("aliases", []))
            if raw in candidates:
                meta = dict(entry)
                meta["_matched_name"] = name  # 记录实际传入的名字
                return meta
        # 降级：假设是 .exe，无 folder
        return {"tool_name": name, "folder": "", "type": ".exe", "aliases": [], "_matched_name": name}

    @staticmethod
    def _search_tools_dir(meta: dict) -> str | None:
        """
        在 tools/ 目录下搜索工具文件
        搜索优先级: folder 子目录 → tools 根目录；标准名 → 别名；精确匹配 → glob 兜底
        """
        tools_dir = PathService.get_tools_dir()

        # 收集待搜索的子目录
        sub_dirs: list[Path] = []
        folder = meta.get("folder", "")
        if folder:
            sub_dirs.append(tools_dir / folder)
        sub_dirs.append(tools_dir)  # tools 根目录兜底
        if not folder:
            # 未命中 metadata 时，遍历所有一级子目录（不递归）以增加搜索范围
            for child in sorted(tools_dir.iterdir()):
                if child.is_dir():
                    sub_dirs.append(child)

        # 收集待尝试的文件名
        filenames: list[str] = []
        matched = meta.get("_matched_name", meta["tool_name"])
        target_ext = meta.get("type", ".exe").lower()

        filenames.append(matched)
        if not matched.lower().endswith(target_ext):
            filenames.append(matched + target_ext)

        # 别名匹配时，优先使用 metadata 中定义的标准名和别名列表，增加命中率和准确性
        if matched.lower() == meta["tool_name"].lower():
            if (meta["tool_name"] + target_ext) not in filenames:
                filenames.append(meta["tool_name"] + target_ext)
            for alias in meta.get("aliases", []):
                if alias not in filenames:
                    filenames.append(alias)

        # 逐目录、逐文件名尝试
        for sub_dir in sub_dirs:
            if not sub_dir.is_dir():
                continue
            for fname in filenames:
                p = sub_dir / fname
                if p.is_file():
                    return str(p.resolve())
            # 兜底：模糊匹配
            keyword = matched.lower()
            for f in sub_dir.iterdir():
                if not f.is_file():
                    continue
                if f.suffix.lower() != target_ext:
                    continue
                stem = f.stem.lower()
                if keyword in stem or stem in keyword:
                    return str(f.resolve())

        return None


    @staticmethod
    def check_tool_exists(tool_name: str, custom_path: str = None) -> bool:
        """检查工具是否存 (走缓存，不重复搜盘)"""
        if custom_path:
            p = Path(custom_path)
            if p.is_file():
                return True
        return ToolService.get_tool_path(tool_name, custom_path) is not None

    @staticmethod
    def get_tool_path(tool_name: str, custom_path: str = None) -> str | None:
        """
        获取工具可执行文件的绝对路径。
        搜索顺序: custom_path → tools/folder/ → tools/ → 系统 PATH。
        结果缓存在 _tool_path_cache 中。
        """
        cache_key = tool_name.lower().strip() # 统一小写、去除空白，作为缓存键

        # 1. 自定义路径
        if custom_path:
            p = Path(custom_path)
            if p.is_file():
                result = str(p.resolve())
                ToolService._tool_path_cache[cache_key] = result
                return result

        # 缓存命中
        if cache_key in ToolService._tool_path_cache:
            return ToolService._tool_path_cache[cache_key]

        # 2. 解析元数据，搜索 tools/ 目录
        meta = ToolService._resolve_metadata(cache_key)
        result = ToolService._search_tools_dir(meta)
        if result is not None:
            ToolService._tool_path_cache[cache_key] = result
            return result

        # 3. 系统 PATH
        system_path = shutil.which(tool_name)
        if system_path:
            result = str(Path(system_path).resolve())
            ToolService._tool_path_cache[cache_key] = result
            return result

        ToolService._tool_path_cache[cache_key] = None
        return None

    @staticmethod
    def force_clear_cache(tool_name: str = None):
        """
        清除路径缓存。
        传入 tool_name 清除单个，不传则清空全部。
        """
        if tool_name is None:
            ToolService._tool_path_cache.clear()
        else:
            key = tool_name.lower().strip()
            ToolService._tool_path_cache.pop(key, None)