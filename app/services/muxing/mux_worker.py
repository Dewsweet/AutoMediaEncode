import os
import re
import subprocess
import shlex
import time
import json
from pathlib import Path
from collections import deque
from PySide6.QtCore import QThread, Signal
from ..tool_service import ToolService
from ..error_service import ErrorService
from ...common.logger import logger
from ...common.signal_bus import signalBus
from ffmpeg_progress_yield import FfmpegProgress
from ..output_service import OutputTransaction
from ..process_service import kill_process

class MuxWorker(QThread):
    def __init__(self, payload: dict, parent=None):
        super().__init__(parent)
        self.payload = payload
        self.task_id = payload.get('task_id')
        self._is_cancelled = False
        self._has_error = False
        self._current_ff_process = None
        self._current_subprocess = None

    def cancel(self):
        self.stop()

    def stop(self):
        """外部调用以强制停止任务"""
        self._is_cancelled = True
        kill_process(self._current_ff_process)
        kill_process(self._current_subprocess)

    def _fail(self, message):
        if not self._is_cancelled and not self._has_error:
            self._has_error = True
            signalBus.taskError.emit(self.task_id, message)

    @staticmethod
    def format_time(seconds: float) -> str:
        if seconds < 0: return "--:--"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def run(self):
        task_start_time = time.time()
        logger.info(f"\n\n\n{'='*20} 混流任务开始编排: {self.task_id} {'='*20}")
        logger.debug(f"Payload 详情:\n{json.dumps(self.payload, indent=4, ensure_ascii=False)}")

        outputs = None
        try:
            if self._is_cancelled:
                return
            states = self.payload.get('states', {})
            output_state = states.get('output_state', {})
            container = states.get('option_state', {}).get('container')
            output_path = output_state.get('output_path')
            tracks_state = dict(states.get('tracks_state', {}))
            ordered_tracks = states.get('ordered_tracks', [])
            chapter_files = states.get('chapter_files', [])
            attachment_state = states.get('option_state', {}).get('enable_attachment', False)
            attachments = states.get('attachment_state', {}).get('attachments', [])
            embedded_attachments = states.get('attachment_state', {}).get('embedded_attachments', {})
            if attachment_state:
                for source, ids in embedded_attachments.items():
                    if ids:
                        tracks_state.setdefault(source, {'empty': False})

            if not output_path or not tracks_state:
                raise ValueError(self.tr("请设置输出路径并选择需要封装的轨道"))
            outputs = OutputTransaction(list(tracks_state) + chapter_files + attachments)
            outputs.plan(output_path)
            staged_output = str(outputs.stage(output_path))

            container_str = str(container).lower() if container else ''
            
            if container_str in {'mp4', 'mov'}:
                self._run_ffmpeg_mux(staged_output, tracks_state, chapter_files, attachments)
            elif container_str == 'mkv':
                self._run_mkvmerge_mux(staged_output, tracks_state, chapter_files, attachments, attachment_state, ordered_tracks, embedded_attachments)
            else:
                self._fail(self.tr("不支持的封装格式: {container}").format(container=container_str))
                logger.error(f"[Task {self.task_id}] 不支持的封装格式: {container_str}")

            if not self._is_cancelled and not self._has_error:
                outputs.commit()

        except Exception as e:
            if not self._is_cancelled:
                logger.exception("混流执行异常")
                self._fail(self.tr("混流执行失败: {error}").format(error=str(e)))
        finally:
            if outputs is not None:
                outputs.cleanup()

        if not self._is_cancelled and not self._has_error:
            run_duration = time.time() - task_start_time
            logger.info(f"{'='*20} 混流任务全部完成: {self.task_id}, 总耗时: {run_duration:.2f}s {'='*20}\n")
            signalBus.taskCompleted.emit(self.task_id)

    def _run_mkvmerge_mux(self, output_path: str, tracks_state: dict, chapter_files: list, attachments: list, attachment_state: bool, ordered_tracks: list, embedded_attachments=None):
        mkvmerge_path = ToolService.get_tool_path('mkvmerge')
        if not mkvmerge_path:
            logger.error(f"[Task {self.task_id}] 未找到 MkvMerge 可执行文件, 停止运行")
            self._fail(self.tr("未找到 MkvMerge 可执行文件, 请检查相关设置或查看 log"))
            return

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
            
            selected_attachments = (embedded_attachments or {}).get(file_path, [])
            if attachment_state and selected_attachments:
                cmd.extend(['--attachments', ','.join(str(i) for i in selected_attachments)])
            else:
                cmd.append('--no-attachments')

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
        if attachment_state and attachments:
            for att in attachments:
                cmd.extend(['--attach-file', att])

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        logger.info(f"[Task {self.task_id}] mkvmerge command:\n{shlex.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creation_flags
        )
        self._current_subprocess = process

        progress_pattern = re.compile(r"Progress:\s*(\d+)%")
        start_time = time.time()

        output_lines = deque(maxlen=100)
        try:
            if self._is_cancelled:
                kill_process(process)
            for line in process.stdout:
                output_lines.append(line)
                if self._is_cancelled:
                    kill_process(process)
                    break
                match = progress_pattern.search(line)
                if match:
                    percent = float(match.group(1))
                    time_left_str = "--:--"
                    if 0 < percent <= 100:
                        elapsed = time.time() - start_time
                        time_left_str = self.format_time(elapsed / (percent / 100.0) - elapsed)
                    signalBus.taskProgressUpdated.emit(self.task_id, 1, 1, self.tr("混流 (mkvmerge)"), percent, time_left_str)
            returncode = process.wait()
            if not self._is_cancelled:
                if returncode in (0, 1):
                    signalBus.taskProgressUpdated.emit(self.task_id, 1, 1, self.tr("混流 (mkvmerge)"), 100.0, "00:00:00")
                else:
                    main_error = ErrorService.cli_error('mkvmerge', ''.join(output_lines))
                    self._fail(self.tr("混流失败 (code {code}):\n{error}").format(code=returncode, error=main_error))
        finally:
            kill_process(process)
            process.wait()
            process.stdout.close()
            self._current_subprocess = None

    def _run_ffmpeg_mux(self, output_path: str, tracks_state: dict, chapter_files: list, attachments: list):
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path:
            logger.error(f"[Task {self.task_id}] 未找到 FFMpeg 可执行文件, 停止运行")
            self._fail(self.tr("未找到 FFMpeg 可执行文件, 请检查相关设置或查看 log"))
            return

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
            self._fail(self.tr('MP4 / MOV 至少需要一个可封装的视频或音频轨道'))
            return

        cmd.extend(map_args)
        cmd.extend(['-c', 'copy'])
        cmd.append(output_path)

        logger.info(f"[Task {self.task_id}] FFmpeg command:\n{shlex.join(cmd)}")

        self._current_ff_process = FfmpegProgress(cmd)
        start_time = time.time()

        try:
            popen_kwargs = {}
            if os.name == 'nt':
                popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                popen_kwargs['stdin'] = subprocess.DEVNULL

            for progress in self._current_ff_process.run_command_with_progress(popen_kwargs=popen_kwargs):
                if self._is_cancelled:
                    kill_process(self._current_ff_process)
                    return

                time_left_str = "--:--"
                if progress and float(progress) > 0 and float(progress) <= 100:
                    elapsed = time.time() - start_time
                    prg_value = float(progress) / 100.0
                    total_est = elapsed / prg_value
                    rem_time = total_est - elapsed
                    time_left_str = self.format_time(rem_time)

                signalBus.taskProgressUpdated.emit(self.task_id, 1, 1, self.tr("混流 (FFmpeg)"), float(progress), time_left_str)

            if not self._is_cancelled:
                signalBus.taskProgressUpdated.emit(self.task_id, 1, 1, self.tr("混流 (FFmpeg)"), 100.0, "00:00:00")

        except Exception as e:
            if not self._is_cancelled:
                err_msg = str(e)
                logger.error(f"[Task {self.task_id}] FFmpeg mux execution failed:\n{err_msg}")
                main_error = ErrorService.ffmpeg_error(err_msg)
                self._fail(self.tr("混流失败:\n{error}").format(error=main_error))
        finally:
            self._current_ff_process = None
