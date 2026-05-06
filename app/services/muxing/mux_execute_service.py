# coding: utf-8
import os
import re
import subprocess
from PySide6.QtCore import QThread, Signal
from ...services.tool_service import ToolService
from ...common.logger import logger

class MuxExecuteWorker(QThread):
    progress = Signal(int)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, params: dict, parent=None):
        super().__init__(parent)
        self.params = params
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # 仅处理 mkv
            if self.params.get('container') != 'mkv':
                self.error.emit("目前仅支持 MKV 封装")
                return

            mkvmerge_path = ToolService.get_tool_path('mkvmerge')
            if not mkvmerge_path:
                mkvmerge_path = 'mkvmerge'

            cmd = [mkvmerge_path, '-o', self.params['output']]

            # 遍历每个输入文件及其提取的轨道
            for file_path, tracks in self.params['inputs'].items():
                video_ids = [str(t['id']) for t in tracks.get('video', [])]
                audio_ids = [str(t['id']) for t in tracks.get('audio', [])]
                subtitle_ids = [str(t['id']) for t in tracks.get('subtitle', [])]

                # 控制复制的轨道
                if video_ids:
                    cmd.extend(['-d', ','.join(video_ids)])
                else:
                    cmd.append('-D')

                if audio_ids:
                    cmd.extend(['-a', ','.join(audio_ids)])
                else:
                    cmd.append('-A')

                if subtitle_ids:
                    cmd.extend(['-s', ','.join(subtitle_ids)])
                else:
                    cmd.append('-S')

                # 解析轨道修饰符
                for category in ['video', 'audio', 'subtitle']:
                    for track in tracks.get(category, []):
                        tid = str(track['id'])
                        
                        if track.get('language'):
                            cmd.extend(['--language', f"{tid}:{track['language']}"])
                        
                        if track.get('name'):
                            cmd.extend(['--track-name', f"{tid}:{track['name']}"])
                            
                        cmd.extend(['--default-track', f"{tid}:{'1' if track.get('is_default') else '0'}"])

                        flags = track.get('flags', [])
                        
                        cmd.extend(['--forced-display-flag', f"{tid}:{'1' if '强制显示' in flags else '0'}"])
                        cmd.extend(['--hearing-impaired-flag', f"{tid}:{'1' if '听觉障碍' in flags else '0'}"])
                        cmd.extend(['--visual-impaired-flag', f"{tid}:{'1' if '视觉障碍' in flags else '0'}"])
                        cmd.extend(['--text-descriptions-flag', f"{tid}:{'1' if '文字描述' in flags else '0'}"])
                        cmd.extend(['--original-flag', f"{tid}:{'1' if '原始语言' in flags else '0'}"])
                        cmd.extend(['--commentary-flag', f"{tid}:{'1' if '评论轨道' in flags else '0'}"])

                # 追加具体文件
                cmd.append(file_path)

            # 全局附件
            for att in self.params.get('attachments', []):
                cmd.extend(['--attach-file', att])

            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            
            logger.info(f"执行混流命令: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                creationflags=creation_flags
            )

            progress_pattern = re.compile(r"Progress:\s*(\d+)%")

            while True:
                if self._is_cancelled:
                    process.terminate()
                    self.error.emit("任务已被用户取消")
                    return

                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                match = progress_pattern.search(line)
                if match:
                    self.progress.emit(int(match.group(1)))

            returncode = process.wait()
            # 0 是成功, 1 是带警告的成功
            if returncode == 0 or returncode == 1:
                self.progress.emit(100)
                self.finished.emit(returncode)
            else:
                stderr_text = process.stderr.read()
                self.error.emit(f"混流失败 (code {returncode}):\n{stderr_text}")

        except Exception as e:
            logger.exception("混流执行异常")
            self.error.emit(str(e))
