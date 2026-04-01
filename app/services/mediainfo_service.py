from pymediainfo import MediaInfo
import math

from app.services.tool_service import ToolService

class MediaInfoService:
    """
    处理与 MediaInfo CLI 工具交互的逻辑类
    提取出与界面无关的业务逻辑
    """
    def __init__(self):
        # 缓存解析过的文件避免重复加载
        self._cache = {}

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
        if not bps: return "未知"
        try:
            bps = float(bps)
            kbps = round(bps / 1000, 2)
            return f"{kbps} kb/s"
        except:
            return f"{bps} b/s"

    @staticmethod
    def format_duration(sec): 
        if not sec: return "未知"
        try:
            sec = float(sec)
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            if h > 0:
                return f"{h}h {m}m {s}s"
            elif m > 0:
                return f"{m}m {s}s"
            else:
                return f"{s}s"
        except:
            return f"{sec}s"
        
    @staticmethod
    def format_displayAspectRatio(dar): 
        # 将 JSON 输出中的 画面比例（DAR）小数形式转成比例形式
        if not dar: return "未知"
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


    def get_info(self, file_path: str) -> tuple[dict, str]: 
        """
        调用 mediainfo CLI 获取媒体信息
        参数:
        file_path: 媒体文件路径
        """
        if getattr(self, "_cache", None) is not None and file_path in self._cache:
            return self._cache[file_path]

        try:
            mi_path = ToolService.get_tool_path("mediainfo")
            media_info = MediaInfo.parse(file_path, library_file=mi_path)
        except:
            base_info=None

        # 获取需要组装的信息参数
        general = media_info.general_tracks[0] if media_info.general_tracks else None
        videos = media_info.video_tracks
        audios = media_info.audio_tracks
        texts = media_info.text_tracks
        iamges = media_info.image_tracks

        general_info = {}
        if general:
            general_info = {
                "fileName": general.file_name,
                "fileSize": MediaInfoService.format_size(general.file_size) if general.file_size else "未知",
                "format": general.format,
                "duration": MediaInfoService.format_duration(general.duration) if general.duration else "未知",
                "bitRate": MediaInfoService.format_bitrate(general.overall_bit_rate) if general.overall_bit_rate else "未知",
            }

        video_info = []
        for v in videos:
            video_info.append({
                "language": v.language,
                "format": v.format,
                "formatProfile": v.format_profile,
                "bitRate": MediaInfoService.format_bitrate(v.bit_rate) if v.bit_rate else "未知",
                "width": v.width,
                "height": v.height,
                "displayAspectRatio": MediaInfoService.format_displayAspectRatio(v.display_aspect_ratio),
                "frameRate": f"{v.frame_rate} FPS" if v.frame_rate else "未知",
                "bitDepth": f"{v.bit_depth} bit" if v.bit_depth else "未知",
                "colorSpace": v.color_space,
                "chromaSubsampling": v.chroma_subsampling,
            })
        audio_info = []
        for a in audios:
            audio_info.append({
                "language": a.language,
                "format": a.format,
                "formatProfile": a.format_profile,
                "bitRate": MediaInfoService.format_bitrate(a.bit_rate) if a.bit_rate else "未知",
                "samplingRate": f"{a.sampling_rate} Hz" if a.sampling_rate else "未知",
                "channels": f"{a.channel_s} ch" if getattr(a, "channel_s", None) else (f"{a.channels} ch" if getattr(a, "channels", None) else "未知"),
            })
        text_info = []
        for t in texts:
            text_info.append({
                "format": t.format,
                "language": t.language,
                "title": t.title,
            })
        image_info = []
        for i in iamges:
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
        
        try:
            full_info = MediaInfo.parse(file_path, output="Text", full=False, library_file=mi_path)
        except:
            full_info=None

        if getattr(self, "_cache", None) is not None:
            self._cache[file_path] = (base_info, full_info)

        return base_info, full_info

    def view_info(self, file_path: str) -> str:
        """组装并返回基础信息的 Markdown 文本输出"""
        base_info, _ = self.get_info(file_path)
        if base_info is None:
            return "MediaInfo 解析失败，无法获取媒体信息。"
        

        general = base_info.get("general", {})
        audio = base_info.get("audio", [])
        video = base_info.get("video", [])
        image = base_info.get("image", [])
        text = base_info.get("text", [])

        # md_lines= ["### 基础信息"]
        md_lines = []
        if audio and not video:
            md_lines.append(f"**{general.get('format', '未知格式')}** ; {general.get('fileSize')};  {general.get('duration')}; {general.get('bitRate')}   ")
        elif image and not video and not audio:
            md_lines.append(f"**格式: {general.get('format', '未知格式')}** ; {general.get('fileSize')}")
        elif general:
            md_lines.append(f"**{general.get('format', '未知格式')}** ; {general.get('fileSize', '')};  {general.get('duration', '')}; {general.get('bitRate', '')}   ")
        md_lines.append("   ")

        if video:
            v_codecs = " | ".join([v.get("format", "未知") for v in video])
            md_lines.append(f"**{len(video)}** 个视频流: {v_codecs}   ")
        if audio:
            a_codecs = " | ".join([a.get("format", "未知") for a in audio])
            md_lines.append(f"**{len(audio)}** 个音频流: {a_codecs}   ")
        if text:
            t_formats = " | ".join([t.get("format", "未知") for t in text])
            md_lines.append(f"**{len(text)}** 个字幕流: {t_formats}   ")
        md_lines.append("   ")

        for i, v in enumerate(video, 1):
            md_lines.append(f"#### 视频 {i}")
            if v.get("language"): md_lines.append(f"-语言: {v.get('language')}   ")
            md_lines.append(f"-编码格式: {v.get('format', '未知')} ({v.get('formatProfile', '')})    ")
            md_lines.append(f"-分辨率: {v.get('width', '?')} x {v.get('height', '?')} ({v.get('displayAspectRatio')})    ")
            md_lines.append(f"-帧率: {v.get('frameRate')}    ")
            md_lines.append(f"-视频码率: {v.get('bitRate')}    ")
            md_lines.append(f"-位深: {v.get('bitDepth')}    ")
            md_lines.append(f"-色彩抽样: {v.get('colorSpace', '?')}{v.get('chromaSubsampling', '?')}    ")
            md_lines.append("")

        for i, a in enumerate(audio[:2], 1):
            md_lines.append(f"#### 音频 {i}")
            if a.get("language"): md_lines.append(f"-语言: {a.get('language')}   ")
            md_lines.append(f"-编码格式: {a.get('format', '未知')}    ")
            md_lines.append(f"-音频码率: {a.get('bitRate')}   ")
            md_lines.append(f"-采样率: {a.get('samplingRate')}   ")
            md_lines.append(f"-声道数: {a.get('channels')}   ")
            md_lines.append("")

        for i, t in enumerate(text[:2], 1):
            md_lines.append(f"#### 字幕 {i}")
            if t.get("language"): md_lines.append(f"-语言: {t.get('language')}   ")
            md_lines.append(f"-类型: {t.get('format', '未知')}   ")
            md_lines.append("")

        for i, img in enumerate(image, 1):
            md_lines.append(f"#### 图片 {i}")
            md_lines.append(f"-格式: {img.get('format', '未知')}   ")
            ratio = int(img.get('width', 0)) / int(img.get('height', 1)) if img.get('width') and img.get('height') else ""
            md_lines.append(f"-分辨率: {img.get('width', '?')} x {img.get('height', '?')} ({round(ratio, 2)})   ")
            md_lines.append("")

        return "\n".join(md_lines)


    def full_info(self, file_path: str) -> str:
        """组装并返回完整的原始媒体文本（便于作为完整信息查看）"""
        _, full_text = self.get_info(file_path)
        if full_text is None:
            return "MediaInfo 解析失败，无法获取完整媒体信息。"

        cleaned_lines = []
        for line in str(full_text).splitlines():
            # 过滤多余的空行，只在段落间保留单行空行
            if not line.strip():
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue

            if ':' in line:
                key, val = line.split(':', 1)
                cleaned_lines.append(f"{key.strip()}: {val.strip()}")
            else:
                cleaned_lines.append(line.strip())

        return "\n".join(cleaned_lines).strip()
