import re
from pathlib import Path
from typing import Dict, List, Any
from pymediainfo import MediaInfo

from app.services.tool_service import ToolService

class DemuxProbeService:
    def __init__(self):
        self.mi_path = ToolService.get_tool_path('mediainfo')

    def probe_file(self, file_path: str | Path) -> Dict[str, Any]:
        """
        运行 MediaInfo 获取 媒体文件信息，并解析出轨道、章节等结构化数据。
        """
        if not self.mi_path:
            return {"error": "mediainfo not found"}
            
        file_path_str = str(file_path)
        try:
            media_info = MediaInfo.parse(file_path_str, library_file=self.mi_path)
            return self.parse_mediainfo_output(media_info)
        except Exception as e:
            print(f"Error probing file {file_path_str}: {e}")
            return {"error": str(e)}

    def parse_mediainfo_output(self, media_info: MediaInfo) -> Dict[str, Any]:
        """
        解析 MediaInfo 输出，提取视频、音频、字幕、附件流信息以及章节数量等结构化数据。
        """
        result = {
            "video": [],
            "audio": [],
            "subtitle": [],
            "attachment": [],
            "chapters": 0
        }

        # 视频轨道
        for track in media_info.video_tracks:
            result["video"].append({
                "id": getattr(track, "stream_identifier", getattr(track, "track_id", "")),
                "lang": getattr(track, "language", "und"),
                "type": "video",
                "codec": getattr(track, "format", "Unknown"),
                "res_str": f"{getattr(track, 'width', '?')}x{getattr(track, 'height', '?')}",
                "fps_str": f"{getattr(track, 'frame_rate', '?')}FPS",
                "default": getattr(track, "default", "No") == "Yes",
                "title": getattr(track, "title", ""),
            })

        # 音频轨道
        for track in media_info.audio_tracks:
            hz = getattr(track, "sampling_rate", "?")
            ch = getattr(track, "channel_s", getattr(track, "channels", "?"))
            result["audio"].append({
                "id": getattr(track, "stream_identifier", getattr(track, "track_id", "")),
                "lang": getattr(track, "language", "und"),
                "type": "audio",
                "codec": getattr(track, "format", "Unknown"),
                "hz_str": f"{hz}Hz" if hz != "?" else "?",
                "ch_str": f"{ch}ch" if ch != "?" else "?",
                "default": getattr(track, "default", "No") == "Yes",
                "title": getattr(track, "title", ""),
            })

        # 字幕轨道
        for track in media_info.text_tracks:
            result["subtitle"].append({
                "id": getattr(track, "stream_identifier", getattr(track, "track_id", "")),
                "lang": getattr(track, "language", "und"),
                "type": "subtitle",
                "codec": getattr(track, "format", "Unknown"),
                "default": getattr(track, "default", "No") == "Yes",
                "title": getattr(track, "title", ""),
            })

        # 附件 (从 General 轨道中读取以 " / " 分隔的名称)
        if media_info.general_tracks:
            general = media_info.general_tracks[0]
            attachments_str = getattr(general, "attachment", "")
            # 有时属性可能叫做 'attachments'
            if not attachments_str:
                attachments_str = getattr(general, "attachments", "")
                
            if attachments_str and isinstance(attachments_str, str):
                for filename in attachments_str.split(" / "):
                    filename = filename.strip()
                    if filename:
                        result["attachment"].append({
                            "id": "",  # 从 General 中取出的附件不再具备直接追踪的流 ID
                            "lang": "und",
                            "type": "attachment",
                            "filename": filename,
                            "default": False,
                            "title": "",
                        })

        # 附件 (依然保留 other_tracks 检查，以防万一)
        for track in media_info.other_tracks:
            filename = getattr(track, "title", getattr(track, "format", "attachment"))
            result["attachment"].append({
                "id": getattr(track, "stream_identifier", getattr(track, "track_id", "")),
                "lang": "und",
                "type": "attachment",
                "filename": filename,
                "default": False,
                "title": "",
            })
            
        # 提取章节数量
        # mpls 或者 mkv 的章节通常作为 menu_tracks 存在
        if media_info.menu_tracks:
            for tm in media_info.menu_tracks:
                # pymediainfo 中章节经常作为类似 '_00_00_00_000' 的属性存在字典中
                data = tm.to_data()
                chapter_count = 0
                for key in data.keys():
                    # 匹配时间轴开头的 key, 例如 '_00_00_00_000' 或者 '00:00:00'
                    if re.match(r'^_?\d+[_:]\d+[_:]\d+', key):
                        chapter_count += 1
                        
                if chapter_count > 0:
                    result["chapters"] += chapter_count
                else:
                    # 如果没有带时间轴具体的章节，回退算作 1 个处理
                    result["chapters"] += 1

        return result

    def format_track_for_ui(self, stream_dict: Dict[str, Any], track_number: int) -> str:
        """
        格式化输出字符串并在 UI 上显示
        """
        s_type = stream_dict.get("type", "").capitalize()
        lang = stream_dict.get("lang", "und")
        if not lang: 
            lang = "und" 
            
        is_default_str = "(default)" if stream_dict.get("default") else ""
        title_str = f" [{stream_dict.get('title')}]" if stream_dict.get('title') else ""
        codec = str(stream_dict.get("codec", "Unknown")).upper()
        
        if s_type == "Attachment":
            filename = stream_dict.get("filename", "Unknown")
            ext = filename.split('.')[-1].lower() if '.' in filename else "file"
            if ext in ["ttf", "otf", "woff"]:
                attach_type = "font"
            elif ext in ["jpg", "png", "jpeg"]:
                attach_type = "image"
            else:
                attach_type = ext
            return f"附件 {track_number}: {attach_type} ({filename})"
            
        elif s_type == "Subtitle":
            return f"轨道 {track_number}: {s_type}({lang}) {codec}{title_str} {is_default_str}".strip()
            
        elif s_type == "Video":
            res_str = stream_dict.get("res_str", "")
            fps_str = stream_dict.get("fps_str", "")
            return f"轨道 {track_number}: {s_type}({lang}) {codec} {res_str} {fps_str} {is_default_str}".strip()
            
        elif s_type == "Audio":
            hz_str = stream_dict.get("hz_str", "")
            ch_str = stream_dict.get("ch_str", "")
            return f"轨道 {track_number}: {s_type}({lang}) {codec} {hz_str} {ch_str} {is_default_str}".strip()

        return f"轨道 {track_number}: {s_type}({lang}) {codec} {is_default_str}".strip()
