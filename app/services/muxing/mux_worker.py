import os
import re
import subprocess
import shlex
import time
from PySide6.QtCore import QThread, Signal
from ..tool_service import ToolService
from ..error_service import ErrorService
from ...common.logger import logger
from ...common.signal_bus import signalBus
from ffmpeg_progress_yield import FfmpegProgress

class MuxWorker(QThread):
    def __init__(self, payload: dict, parent=None):
        super().__init__(parent)
        self.payload = payload
        self.task_id = payload.get('task_id')
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def stop(self):
        self.cancel()

    def _emit_progress(self, task_id: str, progress: float, start_time: float, label: str = 'Muxing(FFmpeg)'):
        elapsed = time.time() - start_time
        time_left_str = "计算中..."
        if progress > 0 and progress < 100:
            total_estimated = elapsed / (progress / 100)
            remaining = total_estimated - elapsed
            if 0 < remaining < 86400:
                m, s = divmod(int(remaining), 60)
                h, m = divmod(m, 60)
                time_left_str = f"{h:02d}:{m:02d}:{s:02d}"
        elif progress >= 100:
            time_left_str = "00:00:00"

        signalBus.taskProgressUpdated.emit(task_id, 1, 1, label, progress, time_left_str)

    def _run_ffmpeg_mux(self, output_path: str, tracks_state: dict, chapter_files: list, attachments: list):
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path:
            ffmpeg_path = 'ffmpeg'

        cmd = [ffmpeg_path, '-y']
        file_paths = list(tracks_state.keys())
        file_index_map = {}

        for idx, file_path in enumerate(file_paths):
            file_index_map[file_path] = idx
            cmd.extend(['-i', file_path])

        map_args = []
        for file_path, tracks in tracks_state.items():
            input_idx = file_index_map[file_path]
            for track in tracks.get('video', []):
                map_args.extend(['-map', f'{input_idx}:{track["id"]}'])
            for track in tracks.get('audio', []):
                map_args.extend(['-map', f'{input_idx}:{track["id"]}'])

        if not map_args:
            signalBus.taskError.emit(self.task_id, 'MP4 / MOV 至少需要一个可封装的视频或音频轨道')
            return

        cmd.extend(map_args)
        cmd.extend(['-c', 'copy'])
        cmd.append(output_path)

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        logger.info(f"执行混流命令: {shlex.join(cmd)}")

        self._current_ff_process = FfmpegProgress(cmd)
        start_time = time.time()

        try:
            popen_kwargs = {}
            if os.name == 'nt':
                popen_kwargs['creationflags'] = creation_flags
                popen_kwargs['stdin'] = subprocess.DEVNULL

            for progress in self._current_ff_process.run_command_with_progress(popen_kwargs=popen_kwargs):
                if self._is_cancelled:
                    self._current_ff_process.quit()
                    return

                self._emit_progress(self.task_id, float(progress), start_time, 'Muxing(FFmpeg)')

            if self._is_cancelled:
                return

            self._emit_progress(self.task_id, 100.0, start_time, 'Muxing(FFmpeg)')
            signalBus.taskCompleted.emit(self.task_id)

        except Exception as e:
            if self._is_cancelled:
                logger.info(f"[Task {self.task_id}] User cancelled task, ignoring FfmpegProgress RuntimeError.")
                return

            logger.exception(f"[Task {self.task_id}] FFmpeg mux execution failed:")
            main_error = ErrorService.ffmpeg_error(str(e))
            signalBus.taskError.emit(self.task_id, f"混流失败:\n{main_error}")
        finally:
            self._current_ff_process = None

    def run(self):
        try:
            states = self.payload['states']
            output_state = states['output_state']
            container = states['option_state'].get('container')
            output_path = output_state.get('output_path')
            tracks_state = states['tracks_state'] 
            ordered_tracks = states.get('ordered_tracks', [])
            chapter_files = states.get('chapter_files', [])
            attachments = states['attachment_state'].get('attachments', [])

            container_str = str(container).lower() if container else ''
            if container_str in {'mp4', 'mov'}:
                self._run_ffmpeg_mux(output_path, tracks_state, chapter_files, attachments)
                return

            # 仅处理 mkv
            if container_str != 'mkv':
                signalBus.taskError.emit(self.task_id, "目前仅支持 MKV 封装")
                return

            mkvmerge_path = ToolService.get_tool_path('mkvmerge')
            if not mkvmerge_path:
                mkvmerge_path = 'mkvmerge'

            cmd = [mkvmerge_path, '-o', output_path]

            file_paths = list(tracks_state.keys())
            chapter_file = chapter_files[0] if chapter_files else None
            chapter_used = False

            # 遍历每个输入文件及其提取的轨道
            for file_path, tracks in tracks_state.items():
                video_ids = [str(t['id']) for t in tracks.get('video', [])]
                audio_ids = [str(t['id']) for t in tracks.get('audio', [])]
                subtitle_ids = [str(t['id']) for t in tracks.get('subtitle', [])]

                if not video_ids and not audio_ids and not subtitle_ids and tracks.get('empty', False):
                    continue

                if chapter_file and not chapter_used:
                    cmd.extend(['--chapters', chapter_file])
                    chapter_used = True

                if not tracks.get('keep_chapters', False):
                    cmd.append('--no-chapters')

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
                            
                        if track.get('is_default'):
                            cmd.extend(['--default-track-flag', f"{tid}:1"])
                        else:
                            cmd.extend(['--default-track-flag', f"{tid}:0"])

                        flags = track.get('flags', [])
                        
                        if '强制显示' in flags: cmd.extend(['--forced-display-flag', f"{tid}:1"])
                        if '听觉障碍' in flags: cmd.extend(['--hearing-impaired-flag', f"{tid}:1"])
                        if '视觉障碍' in flags: cmd.extend(['--visual-impaired-flag', f"{tid}:1"])
                        if '文字描述' in flags: cmd.extend(['--text-descriptions-flag', f"{tid}:1"])
                        if '原始语言' in flags: cmd.extend(['--original-flag', f"{tid}:1"])
                        if '评论轨道' in flags: cmd.extend(['--commentary-flag', f"{tid}:1"])

                # 追加具体文件
                cmd.append(file_path)

            if ordered_tracks:
                track_order_args = []
                for t in ordered_tracks:
                    if '章节' in t['type']: continue
                    if t['file'] in file_paths:
                        f_idx = file_paths.index(t['file'])
                        track_order_args.append(f"{f_idx}:{t['id']}")
                
                if track_order_args:
                    cmd.extend(['--track-order', ','.join(track_order_args)])

            # 全局附件
            for att in attachments:
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
                    signalBus.taskError.emit(self.task_id, "任务已被用户取消")
                    return

                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                match = progress_pattern.search(line)
                if match:
                    percent = float(match.group(1))
                    signalBus.taskProgressUpdated.emit(self.task_id, 1, 1, "Muxing(MKVMerge)", percent, "--")

            returncode = process.wait()
            # 0 是成功, 1 是带警告的成功
            if returncode == 0 or returncode == 1:
                signalBus.taskProgressUpdated.emit(self.task_id, 1, 1, "Muxing(MKVMerge)", 100.0, "--")
                signalBus.taskCompleted.emit(self.task_id)
            else:
                stderr_text = process.stderr.read()
                signalBus.taskError.emit(self.task_id, f"混流失败 (code {returncode}):\n{stderr_text}")

        except Exception as e:
            logger.exception("混流执行异常")
            signalBus.taskError.emit(self.task_id, str(e))