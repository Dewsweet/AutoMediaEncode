import subprocess
import json
import math

class MediaInfoService:
    """
    处理与 MediaInfo CLI 工具交互的逻辑类
    提取出与界面无关的业务逻辑
    """
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

    @staticmethod
    def _parse_basic_markdown(json_output: str) -> str: # 从 mediainfo 的 JSON 输出中提取关键信息，并格式化为 Markdown 文本
        try:
            data = json.loads(json_output)
            tracks = data.get("media", {}).get("track", []) 
            
            general = {} 
            videos = []
            audios = []
            texts = []
            
            for t in tracks:
                t_type = t.get("@type")
                if t_type == "General": general = t
                elif t_type == "Video": videos.append(t)
                elif t_type == "Audio": audios.append(t)
                elif t_type == "Text": texts.append(t)
            
            md_lines = ["### 容器和一般信息"]
            
            container = general.get("Format", "未知格式") 
            size = MediaInfoService.format_size(general.get("FileSize"))
            duration = MediaInfoService.format_duration(general.get("Duration"))
            overall_br = MediaInfoService.format_bitrate(general.get("OverallBitRate"))    
            
            md_lines.append(f"**{container}** : {size}, {duration}, {overall_br}   ")
            
            if videos:
                v_codecs = " | ".join([v.get("Format", "未知") for v in videos])
                md_lines.append(f"{len(videos)}个视频流: {v_codecs}   ")
            if audios:
                a_codecs = " | ".join([a.get("Format", "未知") for a in audios[:2]])
                if len(audios) > 2: a_codecs += " | ..."
                md_lines.append(f"{len(audios)}个音频流: {a_codecs}   ")
            if texts:
                t_codecs = " | ".join([t.get("Format", "未知") for t in texts[:3]])
                if len(texts) > 3: t_codecs += " | ..."
                md_lines.append(f"{len(texts)}个字幕流: {t_codecs}    ")
            
            md_lines.append("")
            
            for i, v in enumerate(videos, 1):
                md_lines.append(f"#### 视频 {i}")
                md_lines.append(f"-视频码率: {MediaInfoService.format_bitrate(v.get('BitRate'))}   ")
                dar_str = MediaInfoService.format_displayAspectRatio(v.get("DisplayAspectRatio"))        
                md_lines.append(f"-分辨率: {v.get('Width', '?')} x {v.get('Height', '?')} ({dar_str})   ")
                md_lines.append(f"-帧率: {v.get('FrameRate', '?')} FPS   ")
                md_lines.append(f"-位深: {v.get('BitDepth', '?')} bit   ")
                md_lines.append(f"-色彩抽样: {v.get('ColorSpace', '?')}:{v.get('ChromaSubsampling', '?')}   ")
                md_lines.append(f"-编码格式: {v.get('Format', '?')} {v.get('Format_Profile', '')}   ".strip())
                md_lines.append("")
                
            for i, a in enumerate(audios[:2], 1):
                md_lines.append(f"#### 音频 {i}")
                md_lines.append(f"-音频码率: {MediaInfoService.format_bitrate(a.get('BitRate'))}   ")
                md_lines.append(f"-采样率: {a.get('SamplingRate', '?')} Hz   ")
                md_lines.append(f"-声道数: {a.get('Channels', '?')} ch   ")
                md_lines.append(f"-编码格式: {a.get('Format', '?')} {a.get('Format_AdditionalFeatures', '')}   ".strip())
                md_lines.append("")
                
            for i, t in enumerate(texts[:3], 1):
                md_lines.append(f"#### 字幕 {i}")
                md_lines.append(f"-字幕类型: {t.get('Format', '未知')}   ")
                md_lines.append("")
            
            return "\n".join(md_lines) 
        except Exception as e:
            return f"解析基础信息时出错:\n{e}\n\n{json_output}"

    @staticmethod
    def _clean_raw_text(raw_text: str) -> str:
        cleaned_lines = []
        for line in raw_text.splitlines(): 
            # 只有包含冒号的行才当做 Key-Value 处理
            if ':' in line:
                # 只针对第一个冒号进行切割，防止拆坏文件路径(比如 C:\xxx)或时间(12:30:00)
                key, val = line.split(':', 1)
                # 清除左右两端空格，重新拼接紧凑格式
                cleaned_lines.append(f"{key.strip()}: {val.strip()}")
            else:
                # 对没有冒号的普通行(如 Video, Audio 标题)也去掉行尾的冗余换行空格
                cleaned_lines.append(line.strip())
        
        return "\n".join(cleaned_lines)

    @staticmethod
    def get_info(file_path: str, basic_mode: bool = True) -> str: 
        """
        调用 mediainfo CLI 获取媒体信息
        参数:
        file_path: 媒体文件路径
        basic_mode: 是否只获取基础信息(Markdown), 还是完整信息(Json_raw)
        """
        cmd = ["mediainfo"]
        if basic_mode:
            cmd.append("--Output=JSON")
        
        cmd.append(file_path)

        try:
            import sys 
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW 

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=creationflags
            )
            if result.returncode == 0:
                raw_out = result.stdout.strip() 
                if basic_mode:
                    return MediaInfoService._parse_basic_markdown(raw_out)
                else:
                    return MediaInfoService._clean_raw_text(raw_out)
            else:
                return f"Error executing mediainfo:\n{result.stderr}"
            
        except FileNotFoundError:
            return "Error: 找不到 mediainfo 命令。请确保它已被加入到系统环境变量，或在设置页配置。"
        except Exception as e:
            return f"An error occurred: {str(e)}"
