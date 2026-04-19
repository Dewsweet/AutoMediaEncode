import os
import time
import json
import shlex
import traceback
import subprocess
import re
from pathlib import Path
from PySide6.QtCore import QThread
from ffmpeg_progress_yield import FfmpegProgress

from ...common.signal_bus import signalBus
from ...common.logger import logger
from ..tool_service import ToolService
from ..error_service import ErrorService
from .desubsetting_service import SubtitleProcessService

class DemuxWorker(QThread):
    def __init__(self, payload: dict, parent=None):
        super().__init__(parent)
        self.payload = payload
        self._is_cancelled = False
        self._current_ff_process = None

        self._codec_ext_map = {
            # 视频
            "avc": ".h264", "hevc": ".h265", "v_mpeg4/iso/avc": ".h264", "v_mpegh/iso/hevc": ".h265", "vp8": ".lvf", "vp9": ".ivf", "av1": ".ivf", "mpeg-4 visual": ".mkv", "ffv1": ".ffv1",
            # 音频
            "aac": ".aac", "alac": ".caf", "flac": ".flac", "opus": ".opus", "vorbis": ".ogg", "pcm": ".wav", "mpeg audio": ".mp3", "mpega": ".mp3", "mp3": ".mp3",
            "ac-3": ".ac3", "e-ac-3": ".eac3", "dts": ".dts", "dts-hd": ".dts", 
            "truehd": ".thd", "mlp fba": ".thd",
            # 字幕
            "ass": ".ass", "advanced ssa": ".ass", "ssa": ".ssa", "subrip": ".srt", "srt": ".srt", "vtt": ".vtt", "pgs": ".sup", "hdmv pgs": ".sup", "vobsub": ".sub"
        }

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
        task_start_time = time.time()
        
        logger.info(f"\n\n\n{'='*20} 抽流任务开始编排: {task_id} {'='*20}")
        logger.info(f"包含文件数: {total_files}")
        logger.debug(f"Payload 详情:\n{json.dumps(self.payload, indent=4, ensure_ascii=False)}")

        for idx, f_path in enumerate(files, start=1):
            if self._is_cancelled:
                logger.info(f"已中止任务: {task_id}")
                break
                
            self._process_single_file(task_id, f_path, idx, total_files)

        if not self._is_cancelled:
            run_duration = time.time() - task_start_time
            logger.info(f"{'='*20} 抽流任务全部完成: {task_id}, 总耗时: {run_duration:.2f}s {'='*20}\n")
            signalBus.taskCompleted.emit(task_id)

    def _process_single_file(self, task_id: str, f_path: str, idx: int, total_files: int):
        """处理单个文件的抽流逻辑"""
        states = self.payload.get("states", {})
        tracks_state = states.get("tracks_state", {})
        option_state = states.get("option_state", {})
        output_state = states.get("output_state", {})

        file_path = Path(f_path)
        tracks = tracks_state.get(f_path, [])
        
        if not tracks:
            logger.warning(f"文件没有选中任何提取轨道，跳过: {f_path}")
            return

        out_dir = output_state.get('output_dir', '')
        if output_state.get('use_source_dir', True) or not out_dir:
            out_dir_path = file_path.parent
        else:
            out_dir_path = Path(out_dir)
            out_dir_path.mkdir(parents=True, exist_ok=True)

        fname = file_path.stem
        in_ext = file_path.suffix.lower()
        
        is_matroska = in_ext in ['.mkv', '.mka', '.mks']
        mkvextract_path = ToolService.get_tool_path('mkvextract')
        
        if is_matroska and mkvextract_path:
            self._extract_with_mkvextract(task_id, file_path, fname, out_dir_path, tracks, option_state, idx, total_files, mkvextract_path)
        else:
            self._extract_with_ffmpeg(task_id, file_path, fname, out_dir_path, tracks, option_state, idx, total_files)

    def _extract_with_mkvextract(self, task_id: str, file_path: Path, fname: str, out_dir_path: Path, tracks: list, option_state: dict, idx: int, total_files: int, mkvextract_path: str):
        """mkvextract 组装参数"""
        logger.info(f"[{task_id}] 检测到 Matroska 格式，使用 mkvextract 处理: {file_path.name}")
        
        cmd_list = [mkvextract_path, file_path.as_posix()]
        
        tracks_args = []
        attachments_args = []
        chapter_args = []
        
        generated_ass_files = []

        for track in tracks:
            t_type = track.get("type")
            
            # 独立处理章节抽取
            if t_type == "chapter":
                ch_format = option_state.get("chapter_suffix", "XML").lower()
                ch_ext = f".{ch_format}"
                ch_out = out_dir_path / f"{fname}_chapters{ch_ext}"
                if ch_format in ["txt", "ogm"]:
                    chapter_args.extend(["-s", ch_out.as_posix()])
                else:
                    chapter_args.append(ch_out.as_posix())
                continue
                
            if t_type == "attachment":
                a_idx = track.get("idx", 1)  # attachment 本身的 1-based index
                a_name = track.get("filename", f"attachment_{a_idx}")
                out_file = out_dir_path / f"{a_name}"
                attachments_args.append(f"{a_idx}:{out_file.as_posix()}")
                continue
                
            t_id = track.get("id", "")
            if str(t_id) == "":
                continue
                
            t_codec = track.get("codec", "").lower()
            out_ext = self._codec_ext_map.get(t_codec)
            if not out_ext:
                if t_type == "video": out_ext = ".mkv"
                elif t_type == "audio": out_ext = ".mka"
                elif t_type == "subtitle": out_ext = ".ass"
                else: continue
                
            out_file = out_dir_path / f"{fname}_track_{t_type}_{t_id}{out_ext}"
            out_posix = out_file.as_posix()
            
            tracks_args.append(f"{t_id}:{out_posix}")
            
            if t_type == "subtitle" and option_state.get("desubsetting"):
                generated_ass_files.append(out_posix)

        # 组装最终命令
        has_content = False
        if tracks_args:
            cmd_list.append("tracks")
            cmd_list.extend(tracks_args)
            has_content = True
            
        if attachments_args:
            cmd_list.append("attachments")
            cmd_list.extend(attachments_args)
            has_content = True
            
        if chapter_args:
            cmd_list.append("chapters")
            cmd_list.extend(chapter_args)
            has_content = True

        if has_content:
            logger.info(f"[Task {task_id}] mkvextract command:\n" + shlex.join(cmd_list))
            self._run_cli_with_progress(task_id, idx, total_files, file_path.name, cmd_list, "mkvextract")
            
        # 后处理字幕
        self._post_process_subtitles(generated_ass_files)

    def _extract_with_ffmpeg(self, task_id: str, file_path: Path, fname: str, out_dir_path: Path, tracks: list, option_state: dict, idx: int, total_files: int):
        """Fmpeg 组装参数"""
        ffmpeg_bin_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_bin_path:
            ffmpeg_bin_path = 'ffmpeg'
            logger.warning("未在配置或Path中找到ffmpeg对应的程序文件, 回退使用系统指令'ffmpeg'")

        cmd_list = [ffmpeg_bin_path, "-y", "-i", file_path.as_posix()]

        generated_ass_files = []
        type_map = {"video": "v", "audio": "a", "subtitle": "s"}
        

        for track in tracks:
            t_type = track.get("type")
            t_idx = track.get("idx", 0)
            t_codec = track.get("codec", "").lower()
            
            # 不处理附加在此处的章节事件
            if t_type not in type_map:
                continue

            ffmpeg_stream_type = type_map.get(t_type)
            stream_specifier = f"0:{ffmpeg_stream_type}:{t_idx}"
            
            out_ext = self._codec_ext_map.get(t_codec)
            if not out_ext:
                if t_type == "video": out_ext = ".mkv"
                elif t_type == "audio": out_ext = ".mka"
                elif t_type == "subtitle": out_ext = ".ass"
                else: continue

            out_file = out_dir_path / f"{fname}_track_{t_type}_{t_idx}{out_ext}"
            out_posix = out_file.as_posix()
            
            cmd_list.extend(["-map", stream_specifier])
            
            # m2ts PCM 处理特判策略
            if file_path.suffix.lower() in [".m2ts", ".ts"] and "pcm" in t_codec:
                cmd_list.extend(["-c:a", "pcm_s24le"])
                if not out_posix.endswith(".wav"):
                    out_posix = out_posix.rsplit(".", 1)[0] + ".wav"
            else:
                cmd_list.extend(["-c", "copy"])
                
            cmd_list.append(out_posix)

            if t_type == "subtitle" and option_state.get("desubsetting"):
                generated_ass_files.append(out_posix)

        logger.info(f"[Task {task_id}] FFmpeg command:\n" + shlex.join(cmd_list))

        self._run_cli_with_progress(task_id, idx, total_files, file_path.name, cmd_list, "ffmpeg")
        self._post_process_subtitles(generated_ass_files)
        
    def _post_process_subtitles(self, generated_ass_files: list):
        if not self._is_cancelled and generated_ass_files:
            for ass_f in generated_ass_files:
                if Path(ass_f).exists():
                    logger.info(f"正在进行字幕去子集化处理: {ass_f}")
                    success = SubtitleProcessService.process_file(ass_f)
                    if success:
                        logger.info(f"字幕去子集化成功: {ass_f}")
                    else:
                        logger.error(f"字幕去子集化失败: {ass_f}")

    @staticmethod
    def format_time(seconds: float) -> str:
        if seconds < 0: return "--:--"
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    
    def _run_cli_with_progress(self, task_id: str, file_idx: int, total_files: int, file_name: str, cmd_list: list, tool_type="ffmpeg"):
        """收集参数并使用对应工具处理, 转换progress"""
        if tool_type == "ffmpeg":
            self._run_ffmpeg_task_with_progress(task_id, file_idx, total_files, file_name, cmd_list)
            return
            
        # MKVEXTRACT 使用原生 subprocess 轮询解析 stdout 中的 Progress: XX%
        start_time = time.time()
        
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0 
        try:
            self._current_ff_process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                creationflags=creation_flags, 
                text=True, 
                encoding='utf-8', 
                errors='replace'
            )
            
            progress_pattern = re.compile(r"Progress:\s*(\d+)%")
            
            for line in self._current_ff_process.stdout:
                if self._is_cancelled:
                    self._current_ff_process.kill()
                    break
                    
                match = progress_pattern.search(line)
                if match:
                    prg_value = float(match.group(1))
                    
                    time_left_str = "--:--"
                    if prg_value > 0 and prg_value <= 100:
                        elapsed = time.time() - start_time
                        prg_decimal = prg_value / 100.0
                        total_est = elapsed / prg_decimal
                        rem_time = total_est - elapsed
                        time_left_str = DemuxWorker.format_time(rem_time)

                    signalBus.taskProgressUpdated.emit(
                        task_id, file_idx, total_files, file_name, prg_value, time_left_str
                    )
            
            self._current_ff_process.wait()
            
            if not self._is_cancelled:
                signalBus.taskProgressUpdated.emit(task_id, file_idx, total_files, file_name, 100.0, "00:00:00")
                
        except Exception as e:
            if not self._is_cancelled:
                error_msg = f"处理时发生错误: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                signalBus.taskError.emit(task_id, str(e))
        finally:
            self._current_ff_process = None


    def _run_ffmpeg_task_with_progress(self, task_id: str, file_idx: int, total_files: int, file_name: str, cmd_list: list):
        start_time = time.time()

        try:
            self._current_ff_process = FfmpegProgress(cmd_list)
            for progress in self._current_ff_process.run_command_with_progress():
                if self._is_cancelled:
                    self._current_ff_process.quit()
                    break
                
                time_left_str = "--:--"
                # 避免出现除以0产生的异常
                if progress and float(progress) > 0 and float(progress) <= 100:
                    elapsed = time.time() - start_time
                    prg_value = float(progress) / 100.0
                    total_est = elapsed / prg_value
                    rem_time = total_est - elapsed
                    time_left_str = DemuxWorker.format_time(rem_time)

                signalBus.taskProgressUpdated.emit(
                    task_id,
                    file_idx,
                    total_files,
                    file_name,
                    float(progress),
                    time_left_str
                )
                
            if not self._is_cancelled:
                signalBus.taskProgressUpdated.emit(task_id, file_idx, total_files, file_name, 100.0, "00:00:00")

        except Exception as e:
            if not self._is_cancelled:
                err_msg = str(e)
                logger.error(err_msg)
                main_error = ErrorService.ffmpeg_error(err_msg)
                error_msg = f"文件 [{file_name}] 处理失败\n[可能因为]: {main_error}"
                signalBus.taskError.emit(task_id, error_msg)
        finally:
            self._current_ff_process = None
