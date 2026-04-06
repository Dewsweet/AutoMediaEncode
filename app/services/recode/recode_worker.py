# coding: utf-8
import os
import subprocess
import time
import ffmpeg
from pathlib import Path
from PySide6.QtCore import QThread
from ffmpeg_progress_yield import FfmpegProgress

from ...common.media_utils import classify_files
from .ffmpeg_builder import FFmpegBuilder
from ...common.signal_bus import signalBus

class RecodeWorker(QThread):
    def __init__(self, payload: dict, parent=None):
        super().__init__(parent)
        self.payload = payload
        self.builder = FFmpegBuilder()
        self._is_cancelled = False
        
        # 保存由 FfmpegProgress 返回的迭代器引用，以便中途强杀进程
        self._current_ff_process = None 

    def stop(self):
        """外部调用以强制停止任务"""
        self._is_cancelled = True
        if self._current_ff_process is not None:
            try:
                self._current_ff_process.quit()
            except Exception:
                pass

    def run(self):
        task_id = self.payload.get("task_id")
        files = self.payload.get("files", [])
        total_files = len(files)
        
        # 针对图片类没有持续进度的数据，用计次模式
        for idx, f_path in enumerate(files, start=1):
            if self._is_cancelled:
                break
                
            self._process_single_file(task_id, f_path, idx, total_files)

        if not self._is_cancelled:
            signalBus.taskCompleted.emit(task_id)


    def _process_single_file(self, task_id: str, f_path: str, idx: int, total_files: int):
        states = self.payload.get("states", {})
        video_state = states.get('video_state', {})
        audio_state = states.get('audio_state', {})
        image_state = states.get('image_state', {})
        subtitle_state = states.get('subtitle_state', {})
        output_state = states.get('output_state', {})

        file_path = Path(f_path)
        in_path_str = file_path.as_posix()
        
        classification = classify_files([in_path_str])
        is_video = bool(classification['video'])
        is_audio = bool(classification['audio']) and not is_video
        is_image = bool(classification['image'])
        is_subtitle = bool(classification['subtitle'])

        audio_kwargs, audio_container = self.builder.build_audio_kwargs(audio_state)
        image_kwargs, image_container = self.builder.build_image_kwargs(image_state)
        subtitle_kwargs, subtitle_container = self.builder.build_subtitle_kwargs(subtitle_state)

        out_ext = file_path.suffix
        if is_video:
            out_ext = "." + video_state.get('container', 'mp4').lower()
        elif is_audio:
            out_ext = ("." + audio_container).lower() if audio_container else file_path.suffix
        elif is_image:
            out_ext = ("." + image_container).lower() if image_container else file_path.suffix
        elif is_subtitle:
            out_ext = ("." + subtitle_container).lower() if subtitle_container else file_path.suffix
        
        out_dir = output_state.get('output_dir', '')
        if output_state.get('use_source_dir', True) or not out_dir:
            out_dir_path = file_path.parent
        else:
            out_dir_path = Path(out_dir)
        
        fname = file_path.stem
        if output_state.get('use_custom_suffix') and output_state.get('custom_suffix'):
            fname += output_state.get('custom_suffix', '')
            
        out_path = out_dir_path / (fname + out_ext)
        out_path_str = out_path.as_posix()

        try:
            if is_video:
                v_kwargs_list = self.builder.build_video_kwargs(video_state)
                total_passes = len(v_kwargs_list)
                for pass_num, v_kw in enumerate(v_kwargs_list, start=1):
                    if self._is_cancelled:
                        break
                        
                    merged_kw = v_kw.copy()
                    if merged_kw.get("pass") == 1 or merged_kw.get("pass") == "1":
                        merged_kw["an"] = None
                        out_path_compile = "NUL" if os.name == 'nt' else "/dev/null"
                        merged_kw["f"] = "null"
                    else:
                        out_path_compile = out_path_str
                        merged_kw.update(audio_kwargs)

                    stream = ffmpeg.input(in_path_str)
                    stream = ffmpeg.output(stream, out_path_compile, **merged_kw)
                    cmd_list = ffmpeg.compile(stream, overwrite_output=True)
                    
                    self._run_long_task_with_progress(task_id, idx, total_files, file_path.name, cmd_list, pass_num, total_passes)

            elif is_audio:
                merged_kw = audio_kwargs.copy()
                merged_kw["vn"] = None
                stream = ffmpeg.input(in_path_str)
                stream = ffmpeg.output(stream, out_path_str, **merged_kw)
                cmd_list = ffmpeg.compile(stream, overwrite_output=True)
                
                self._run_long_task_with_progress(task_id, idx, total_files, file_path.name, cmd_list)
                
            elif is_image or is_subtitle:
                kw = image_kwargs if is_image else subtitle_kwargs
                stream = ffmpeg.input(in_path_str)
                stream = ffmpeg.output(stream, out_path_str, **kw)
                cmd_list = ffmpeg.compile(stream, overwrite_output=True)
                
                # 图片字幕任务极快，直接使用 subprocess 丢后台
                creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                subprocess.run(cmd_list, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
                
                # 瞬间跑完则抛出100%完成
                signalBus.taskProgressUpdated.emit(task_id, idx, total_files, file_path.name, 100.0, "完成")
                
        except Exception as e:
            signalBus.taskError.emit(task_id, f"文件 {file_path.name} 出错: {str(e)}")


    def _run_long_task_with_progress(self, task_id, idx, total_files, filename, cmd_list, pass_num=1, total_passes=1):
        """处理带时长的任务 (借助 ffmpeg-progress-yield)"""
        self._current_ff_process = FfmpegProgress(cmd_list)
        start_time = time.time()
        
        try:
            for progress in self._current_ff_process.run_command_with_progress():
                if self._is_cancelled:
                    self._current_ff_process.quit()
                    break
                
                # 兼容 2-pass 的进度均分
                overall_progress = progress
                if total_passes > 1:
                    overall_progress = (progress / total_passes) + ((pass_num - 1) * (100.0 / total_passes))
                
                # 计算预估剩余时间 (ETA)
                elapsed = time.time() - start_time
                time_left_str = "计算中..."
                if overall_progress > 0 and overall_progress < 100:
                    total_estimated = elapsed / (overall_progress / 100)
                    remaining = total_estimated - elapsed
                    if 0 < remaining < 86400: # 正常的时间范围(<24小时)内再显示
                        m, s = divmod(int(remaining), 60)
                        h, m = divmod(m, 60)
                        time_left_str = f"{h:02d}:{m:02d}:{s:02d}"
                elif overall_progress >= 100:
                    time_left_str = "00:00:00"

                signalBus.taskProgressUpdated.emit(task_id, idx, total_files, filename, overall_progress, time_left_str)
        except Exception as e:
            signalBus.taskError.emit(task_id, f"执行异常: {str(e)}")
        finally:
            self._current_ff_process = None