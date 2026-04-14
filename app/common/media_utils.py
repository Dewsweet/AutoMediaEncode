import os

VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.ts', 'mpg', '.mpeg', '.m4v', 'm2ts', '.rmvb', '.vob', '.divx', '.xvid'}
AUDIO_EXTS = {'.mp3', '.aac', '.wav', '.flac', '.ogg', '.m4a', '.wma', '.opus', '.alac', '.pcm', '.mka', '.tta', '.tak', '.wv', '.ape'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif', '.webp', '.heif', '.avif', '.j2k', '.jp2', '.jpx', '.j2c', '.jxl'}
SUBTITLE_EXTS = {'.srt', '.ass', '.ssa', '.vtt', '.sub'}

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
        ext = os.path.splitext(path)[1].lower()
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
