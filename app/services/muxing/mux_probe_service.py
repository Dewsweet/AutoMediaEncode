# coding: utf-8
import json
import subprocess
import os
from pathlib import Path
from ...services.tool_service import ToolService
from ...common.logger import logger

class MuxProbeService:
    @staticmethod
    def probe_file(file_path: str) -> dict:
        """
        探测媒体文件, 返回轨道信息及其属性。
        """
        mkvmerge_path = ToolService.get_tool_path('mkvmerge')
        if not mkvmerge_path:
            mkvmerge_path = 'mkvmerge'
            
        path_obj = Path(file_path)
        if not path_obj.exists():
            logger.error(f"文件不存在: {file_path}")
            return {}

        cmd = [mkvmerge_path, '-J', file_path]
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        
        try:
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                creationflags=creation_flags, 
                text=True, 
                encoding='utf-8'
            )
            if result.returncode != 0 and result.returncode != 1:
                # mkvmerge 放回1有时也是成功的(带警告)，不绝对报错
                logger.error(f"mkvmerge 探测失败 (code {result.returncode}): {result.stderr}")
                return {}
                
            data = json.loads(result.stdout)
            file_size = path_obj.stat().st_size

            # 补救纯章节文件的探测
            if not data.get('container', {}).get('recognized', True):
                ext = path_obj.suffix.lower()
                if ext in ['.txt', '.xml']:
                    tracks = [{
                        'codec': f"{ext.strip('.').upper()} Chapters",
                        'type': 'chapters',
                        'properties': {'track_name': ''}
                    }]
                    return {
                        'path': file_path,
                        'name': path_obj.name,
                        'size': file_size,
                        'format_size': MuxProbeService.format_size(file_size),
                        'container': 'Chapters',
                        'tracks': tracks,
                        'attachments': [],
                        'chapters': []
                    }
                else:
                    return {}

            container_type = data.get('container', {}).get('type', 'Unknown')
            
            tracks = data.get('tracks', [])
            chapters = data.get('chapters', [])
            # 把mkv自带章节作为伪轨道拼在最后
            if chapters:
                num_entries = sum(c.get('num_entries', 0) for c in chapters)
                tracks.append({
                    'codec': 'Chapters',
                    'type': 'chapters',
                    'properties': {
                        'num_entries': num_entries,
                        'track_name': ''
                    }
                })
            
            return {
                'path': file_path,
                'name': path_obj.name,
                'size': file_size,
                'format_size': MuxProbeService.format_size(file_size),
                'container': container_type,
                'tracks': tracks,
                'attachments': data.get('attachments', []),
                'chapters': chapters
            }
        except Exception as e:
            logger.error(f"探测文件异常 [{file_path}]: {e}")
            return {}

    @staticmethod
    def format_size(size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"
        size_name = ("B", "KiB", "MiB", "GiB", "TiB")
        i = 0
        while size_bytes >= 1024 and i < len(size_name) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_name[i]}"
