from pathlib import Path

VIDEO_EXTS = {'.mp4', '.m4v', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.f4v', '.webm', '.mpg', '.mpeg', '.evo', '.vob', '.ts', '.m2ts', '.mts', '.rmvb'}
AUDIO_EXTS = {'.mp3', '.aac', '.wav', '.flac', '.ogg', '.m4a', '.wma', '.opus', '.alac', '.pcm', '.mka', '.tta', '.tak', '.wv', '.ape', '.ac3'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif', '.webp', '.heif', '.avif', '.j2k', '.j2c', '.jxl'}
SUBTITLE_EXTS = {'.srt', '.ass', '.ssa', '.vtt', '.sub'}

BDMV = {'.bdmv', '.mpls', '.m2ts'}
MATROSKA = {'.mk3d', '.mka', '.mks', '.mkv'}
AVC = {'.264', '.avc', '.h264', '.x264'}
HEVC = {'.265', '.hevc', '.h265', '.x265'}
IVF = {'.av1', '.vp8', '.vp9', '.avf'}
DTS = {'.dts', '.dtshd', '.dts-hd', '.dtsma'}
DOLBY = {'.ac3', '.eac3', '.eb3', '.ec3'}
TRUEHD = {'.mlp', '.thd', '.thd+ac3', '.truehd', '.true-hd'}

DEMUXING_EXTS = VIDEO_EXTS | {'.mka', '.mks'}
MUXING_EXTS = VIDEO_EXTS | AUDIO_EXTS | SUBTITLE_EXTS | MATROSKA | AVC | HEVC | IVF | DTS | DOLBY | TRUEHD | {'.ffv1', '.txt', '.xml'}

def classify_files(file_paths):
    """
    根据文件后缀对文件进行分类
    返回字典结构，包含对应的文件路径列表
    """
    result = {
        'video': [],
        'audio': [],
        'image': [],
        'subtitle': [],
        'unknown': []
    }
    for path in file_paths:
        ext = Path(path).suffix.lower()
        if ext in VIDEO_EXTS:
            result['video'].append(path)
        elif ext in AUDIO_EXTS:
            result['audio'].append(path)
        elif ext in IMAGE_EXTS:
            result['image'].append(path)
        elif ext in SUBTITLE_EXTS:
            result['subtitle'].append(path)
        else:
            result['unknown'].append(path)
                
    return result

def get_present_types(classified_dict):
    """返回非空的有效分类列表"""
    return [k for k, v in classified_dict.items() if v and k != 'unknown']

def build_safe_filter(name: str, exts: set, chunk_size: int = 15) -> str:
    """
    将过长的后缀 set 拆分为以 chunk_size 为一组的多个过滤器。
    避免触发 Windows QFileDialog 过滤器下拉菜单超长导致卡死的 Bug。
    """
    ext_list = sorted(list(exts))  # 排序以保证每次显示顺序一致，不再随机变化
    groups = []
    
    for i in range(0, len(ext_list), chunk_size):
        chunk = ext_list[i:i+chunk_size]
        groups.append(" ".join(f"*{e}" for e in chunk))
        
    if len(groups) == 1:
        return f"{name} ({groups[0]})"
    
    # 如果超过单组，划分为 '视频文件(1) (*.mp4...) ;; 视频文件(2) (*.ts...)'
    return ";;".join(f"{name}({i+1}) ({g})" for i, g in enumerate(groups))
