from pymediainfo import MediaInfo
from pathlib import Path
import math
import re
from threading import Lock

from PySide6.QtCore import QCoreApplication
from app.common.logger import logger

from app.services.tool_service import ToolService

_parse_lock = Lock()
# MediaInfo 为 CJK 文本对齐，将键名中的 ASCII 转成全角；只逆转这部分转换。
_report_key_width = {code: code - 0xFEE0 for code in range(0xFF01, 0xFF5F)}
_report_key_width[0x3000] = ord(" ")
_report_chapter = re.compile(
    r"^\s*([0-9０-９]{2}[:：][0-9０-９]{2}[:：][0-9０-９]{2}[.．][0-9０-９]{3})\s*[:：]\s*(.*)$"
)


def parse_media_info(filename, **kwargs):
    """串行访问 DLL 的共享选项；结构化调用默认保持英文属性命名。"""
    options = {"Language": ""}
    options.update(kwargs.pop("mediainfo_options", None) or {})
    with _parse_lock:
        return MediaInfo.parse(filename, mediainfo_options=options, **kwargs)


class MediaInfoService:
    """
    处理与 MediaInfo DLL 交互的逻辑类
    提取出与界面无关的业务逻辑
    """
    def __init__(self):
        # 缓存解析过的文件避免重复加载
        self._cache = {}

    @staticmethod
    def tr(text, disambiguation=None, n=-1):
        return QCoreApplication.translate("MediaInfoService", text, disambiguation, n)

    @staticmethod
    def format_size(size_bytes): 
        if not size_bytes: return "0 B"
        try:
            size_bytes = float(size_bytes)
            if size_bytes == 0:
                return "0 B"
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return f"{s} {['B', 'KiB', 'MiB', 'GiB', 'TiB'][i]}"
        except:
            return f"{size_bytes} B"

    @staticmethod
    def format_bitrate(bps): 
        # 将比特率转换为 kb/s
        if not bps: return QCoreApplication.translate("MediaInfoService", "未知")
        try:
            bps = float(bps)
            kbps = round(bps / 1000, 2)
            return f"{kbps} kb/s"
        except:
            return f"{bps} b/s"

    @staticmethod
    def format_duration(msec): 
        # 将持续时间从毫秒转换为 h:mm:ss 格式
        if not msec: return QCoreApplication.translate("MediaInfoService", "未知")
        try:
            seconds = int(msec) // 1000
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            if h > 0:
                return f"{h}h {m:02d}m {s:02d}s"
            else:
                return f"{m}m {s:02d}s"
        except:
            return f"{msec} ms"
        
    @staticmethod
    def format_displayAspectRatio(dar): 
        # 将 JSON 输出中的 画面比例（DAR）小数形式转成比例形式
        if not dar: return QCoreApplication.translate("MediaInfoService", "未知")
        try:
            if dar == "1.778":
                return "16 : 9"
            elif dar == "1.333":
                return "4 : 3"
            elif dar == "2.352":
                return "21 : 9"
            elif dar == "1.85":
                return "1.85 : 1"
            elif dar == "2.39":
                return "2.39 : 1"
            else:
                return dar
        except:
            return dar


    def get_info(self, file_path: str) -> tuple[dict | str | None, str | None]: 
        """
        调用 MediaInfo DLL 获取媒体信息
        参数:
        file_path: 媒体文件路径
        """
        path = Path(file_path)
        try:
            if not path.is_file():
                error = self.tr("文件不存在，请检查路径是否正确。")
                return error, error
            file_stat = path.stat()
            if file_stat.st_size == 0:
                error = self.tr("文件为空，请检查文件是否损坏。")
                return error, error
        except OSError as exc:
            logger.warning(f"无法访问媒体文件: {file_path} - {exc}")
            error = self.tr("无法读取媒体信息，请检查文件和 MediaInfo DLL。")
            return error, error

        mi_path = ToolService.get_tool_path("mediainfo")
        if not mi_path:
            error = self.tr("未添加 MediaInfo DLL, 请确认相关工具路径")
            return error, error
        app = QCoreApplication.instance()
        language = (app.property("ameLanguage") if app else None) or "zh_CN"
        language_path = ToolService.get_mediainfo_language_path(mi_path) if language == "zh_CN" else None
        try:
            language_stamp = language_path.stat().st_mtime_ns if language_path else None
        except OSError:
            language_stamp = None
        cache_key = (str(path.resolve()), file_stat.st_mtime_ns, file_stat.st_size,
                     language, mi_path, str(language_path), language_stamp)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            media_info = parse_media_info(file_path, library_file=mi_path)
        except Exception as exc:
            logger.warning(f"MediaInfo 解析失败: {file_path} - {exc}")
            error = self.tr("无法读取媒体信息，请检查文件和 MediaInfo DLL。")
            return error, error

        unknown = self.tr("未知")
        # 获取需要组装的信息参数
        general = media_info.general_tracks[0] if media_info.general_tracks else None
        videos = media_info.video_tracks
        audios = media_info.audio_tracks
        texts = media_info.text_tracks
        images = media_info.image_tracks

        general_info = {}
        if general:
            general_info = {
                "fileName": general.file_name,
                "fileSize": MediaInfoService.format_size(general.file_size) if general.file_size else unknown,
                "format": general.format,
                "duration": MediaInfoService.format_duration(general.duration) if general.duration else unknown,
                "bitRate": MediaInfoService.format_bitrate(general.overall_bit_rate) if general.overall_bit_rate else unknown,
            }

        video_info = []
        for v in videos:
            video_info.append({
                "language": v.language,
                "format": v.format,
                "formatProfile": v.format_profile,
                "bitRate": MediaInfoService.format_bitrate(v.bit_rate) if v.bit_rate else unknown,
                "width": v.width,
                "height": v.height,
                "displayAspectRatio": MediaInfoService.format_displayAspectRatio(v.display_aspect_ratio),
                "frameRate": f"{v.frame_rate} FPS" if v.frame_rate else unknown,
                "bitDepth": f"{v.bit_depth} bit" if v.bit_depth else unknown,
                "colorSpace": v.color_space,
                "chromaSubsampling": v.chroma_subsampling,
            })
        audio_info = []
        for a in audios:
            audio_info.append({
                "language": a.language,
                "format": a.format,
                "formatProfile": a.format_profile,
                "bitRate": MediaInfoService.format_bitrate(a.bit_rate) if a.bit_rate else unknown,
                "samplingRate": f"{a.sampling_rate} Hz" if a.sampling_rate else unknown,
                "channels": f"{a.channel_s} ch" if getattr(a, "channel_s", None) else (f"{a.channels} ch" if getattr(a, "channels", None) else unknown),
            })
        text_info = []
        for t in texts:
            text_info.append({
                "format": t.format,
                "language": t.language,
                "title": t.title,
            })
        image_info = []
        for i in images:
            image_info.append({
                "format": i.format,
                "width": i.width,
                "height": i.height,
            })

        base_info = {
            "general": general_info,
            "video": video_info,
            "audio": audio_info,
            "text": text_info,
            "image": image_info,
        }
        
        report_language = ""
        if language == "zh_CN":
            if language_path:
                try:
                    report_language = language_path.read_text(encoding="utf-8-sig")
                    if not report_language.strip():
                        logger.warning(f"MediaInfo 中文语言表为空，报告使用英文: {language_path}")
                        report_language = ""
                except (OSError, UnicodeError) as exc:
                    logger.warning(f"MediaInfo 中文语言表读取失败，报告使用英文: {language_path} - {exc}")
            else:
                logger.warning(f"未找到 MediaInfo 配套中文语言表，报告使用英文: {mi_path}")
        try:
            full_info = parse_media_info(file_path, output="Text", full=False, library_file=mi_path,
                                        mediainfo_options={"Language": report_language})
        except Exception as exc:
            logger.warning(f"MediaInfo 详细报告生成失败: {file_path} - {exc}")
            return base_info, self.tr("无法读取媒体信息，请检查文件和 MediaInfo DLL。")

        self._cache[cache_key] = (base_info, full_info)

        return base_info, full_info

    def view_info(self, file_path: str) -> str:
        """基础信息使用 AME 翻译；格式标识、语言代码和用户元数据原样保留。"""
        base_info, _ = self.get_info(file_path)
        if isinstance(base_info, str):
            return base_info
        if base_info is None:
            return self.tr("未添加 MediaInfo DLL, 请确认相关工具路径")

        general = base_info.get("general", {})
        audio = base_info.get("audio", [])
        video = base_info.get("video", [])
        image = base_info.get("image", [])
        text = base_info.get("text", [])
        unknown = self.tr("未知")
        md_lines = []
        if image and not video and not audio:
            md_lines.append(self.tr("**格式: {format}** ; {size}").format(
                format=general.get("format") or self.tr("未知格式"), size=general.get("fileSize", "")))
        elif general:
            md_lines.append("**{format}** ; {size}; {duration}; {bitrate}   ".format(
                format=general.get("format") or self.tr("未知格式"), size=general.get("fileSize", ""),
                duration=general.get("duration", ""), bitrate=general.get("bitRate", "")))
        md_lines.append("")

        if video:
            codecs = " | ".join(v.get("format") or unknown for v in video)
            md_lines.append(self.tr("**%n** 个视频流: {codecs}", None, len(video)).format(codecs=codecs) + "   ")
        if audio:
            codecs = " | ".join(a.get("format") or unknown for a in audio)
            md_lines.append(self.tr("**%n** 个音频流: {codecs}", None, len(audio)).format(codecs=codecs) + "   ")
        if text:
            codecs = " | ".join(t.get("format") or unknown for t in text)
            md_lines.append(self.tr("**%n** 个字幕流: {codecs}", None, len(text)).format(codecs=codecs) + "   ")
        md_lines.append("")

        for i, v in enumerate(video, 1):
            md_lines.append(self.tr("#### 视频 {index}").format(index=i))
            if v.get("language"):
                md_lines.append(self.tr("- 语言: {language}   ").format(language=v["language"]))
            md_lines.append(self.tr("- 编码格式: {format} ({profile})   ").format(
                format=v.get("format") or unknown, profile=v.get("formatProfile") or ""))
            md_lines.append(self.tr("- 分辨率: {width} x {height} ({ratio})   ").format(
                width=v.get("width") or "?", height=v.get("height") or "?", ratio=v.get("displayAspectRatio", unknown)))
            md_lines.append(self.tr("- 帧率: {rate}   ").format(rate=v.get("frameRate", unknown)))
            md_lines.append(self.tr("- 视频码率: {bitrate}   ").format(bitrate=v.get("bitRate", unknown)))
            md_lines.append(self.tr("- 位深: {depth}   ").format(depth=v.get("bitDepth", unknown)))
            md_lines.append(self.tr("- 色彩抽样: {color}{chroma}   ").format(
                color=v.get("colorSpace") or "?", chroma=v.get("chromaSubsampling") or "?"))
            md_lines.append("")

        for i, a in enumerate(audio[:2], 1):
            md_lines.append(self.tr("#### 音频 {index}").format(index=i))
            if a.get("language"):
                md_lines.append(self.tr("- 语言: {language}   ").format(language=a["language"]))
            md_lines.append(self.tr("- 编码格式: {format}   ").format(format=a.get("format") or unknown))
            md_lines.append(self.tr("- 音频码率: {bitrate}   ").format(bitrate=a.get("bitRate", unknown)))
            md_lines.append(self.tr("- 采样率: {rate}   ").format(rate=a.get("samplingRate", unknown)))
            md_lines.append(self.tr("- 声道数: {channels}   ").format(channels=a.get("channels", unknown)))
            md_lines.append("")

        for i, t in enumerate(text[:2], 1):
            md_lines.append(self.tr("#### 字幕 {index}").format(index=i))
            if t.get("language"):
                md_lines.append(self.tr("- 语言: {language}   ").format(language=t["language"]))
            md_lines.append(self.tr("- 类型: {format}   ").format(format=t.get("format") or unknown))
            md_lines.append("")

        for i, img in enumerate(image, 1):
            md_lines.append(self.tr("#### 图片 {index}").format(index=i))
            md_lines.append(self.tr("- 格式: {format}   ").format(format=img.get("format") or unknown))
            ratio = round(int(img["width"]) / int(img["height"]), 2) if img.get("width") and img.get("height") else ""
            md_lines.append(self.tr("- 分辨率: {width} x {height} ({ratio})   ").format(
                width=img.get("width") or "?", height=img.get("height") or "?", ratio=ratio))
            md_lines.append("")

        return "\n".join(md_lines)

    def full_info(self, file_path: str) -> str:
        """组装并返回完整的原始媒体文本（便于作为完整信息查看）"""
        _, full_text = self.get_info(file_path)
        if full_text is None:
            return self.tr("未添加 MediaInfo DLL, 请确认相关工具路径")

        cleaned_lines = []
        for line in str(full_text).splitlines():
            # 过滤多余的空行，只在段落间保留单行空行
            if not line.strip():
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue

            # 章节时间本身含冒号，先识别完整时间再分离标题。
            chapter = _report_chapter.match(line)
            if chapter:
                key, val = chapter.groups()
            elif re.search(r"[:：]", line):
                key, val = re.split(r"[:：]", line, maxsplit=1)
            else:
                cleaned_lines.append(line.strip())
                continue
            # 不规范化右侧值，保留路径、用户标题和元数据的原始字符。
            key = key.translate(_report_key_width).strip()
            cleaned_lines.append(f"{key}: {val.strip()}")

        return "\n".join(cleaned_lines).strip()

    def image_size_info(self, file_path: str) -> dict | None:
        base_info, _ = self.get_info(file_path)
        if not isinstance(base_info, dict):
            return None
        image = base_info.get("image", [])
        if not image:
            return None
        img = image[0]  
        width = img.get("width")
        height = img.get("height")

        info = {
            "width": width,
            "height": height,
        }
        return info
