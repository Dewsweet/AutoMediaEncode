import os
import time
import json
import shlex
import traceback
from pathlib import Path
from PySide6.QtCore import QThread
from ffmpeg_progress_yield import FfmpegProgress

from ...common.signal_bus import signalBus
from ...common.logger import logger
from ..tool_service import ToolService
from .desubsetting_service import SubtitleProcessService

class DemuxWorker(QThread):
    def __init__(self, payload: dict, parent=None):
        super().__init__(parent)
        self.payload = payload
        self._is_cancelled = False
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
        """对 Matroska 格式使用 mkvextract 进行轨道抽取"""
        logger.info(f"[{task_id}] 检测到 Matroska 格式，使用 mkvextract 处理: {file_path.name}")
        
        # 常见编码与推荐后缀的映射字典
        codec_ext_map = {
            "avc": ".h264", "hevc": ".h265", "v_mpeg4/iso/avc": ".h264", "v_mpegh/iso/hevc": ".h265",
            "aac": ".aac", "ac-3": ".ac3", "e-ac-3": ".eac3", "dts": ".dts", "dts-hd": ".dts", 
            "truehd": ".thd", "flac": ".flac", "pcm": ".wav", "mpeg audio": ".mp3",
            "ass": ".ass", "subrip": ".srt", "pgs": ".sup"
        }
        
        tracks_cmd = [mkvextract_path, file_path.as_posix(), "tracks"]
        generated_ass_files = []
        has_tracks = False
        
        chapter_cmd = None

        for track in tracks:
            t_type = track.get("type")
            
            # 独立处理章节抽取
            if t_type == "chapter":
                ch_ext = "." + option_state.get("chapter_suffix", "XML").lower()
                ch_out = out_dir_path / f"{fname}_chapters{ch_ext}"
                chapter_cmd = [mkvextract_path, file_path.as_posix(), "chapters", ch_out.as_posix()]
                continue
                
            t_id = track.get("id", "")
            if t_id == "":
                continue
                
            t_codec = track.get("codec", "").lower()
            out_ext = codec_ext_map.get(t_codec)
            if not out_ext:
                if t_type == "video": out_ext = ".mkv"
                elif t_type == "audio": out_ext = ".mka"
                elif t_type == "subtitle": out_ext = ".ass"
                else: continue
                
            # mkvextract 需要对应的实际流 ID
            out_file = out_dir_path / f"{fname}_track_{t_type}_{t_id}{out_ext}"
            out_posix = out_file.as_posix()
            
            tracks_cmd.append(f"{t_id}:{out_posix}")
            has_tracks = True
            
            if t_type == "subtitle" and option_state.get("sub_departition"):
                generated_ass_files.append(out_posix)

        # 1. 抽取轨道
        if has_tracks:
            logger.info(f"[Task {task_id}] mkvextract command:\n" + shlex.join(tracks_cmd))
            self._run_cli_with_progress(task_id, idx, total_files, file_path.name, tracks_cmd, "mkvextract")

        # 2. 抽取章节
        if chapter_cmd and not self._is_cancelled:
            logger.info(f"[Task {task_id}] mkvextract chapters command:\n" + shlex.join(chapter_cmd))
            # 章节抽取极快，没必要再专门解析进度栏
            import subprocess
            subprocess.run(chapter_cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
        # 3. 后处理字幕
        self._post_process_subtitles(generated_ass_files)

    def _extract_with_ffmpeg(self, task_id: str, file_path: Path, fname: str, out_dir_path: Path, tracks: list, option_state: dict, idx: int, total_files: int):
        """常规的 FFmpeg 回退抽取 (支持针对 m2ts pcm 进行转码修复)"""
        ffmpeg_bin_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_bin_path:
            ffmpeg_bin_path = 'ffmpeg'
            logger.warning("未在配置或Path中找到ffmpeg对应的程序文件, 回退使用系统指令'ffmpeg'")

        cmd_list = [ffmpeg_bin_path, "-y", "-i", file_path.as_posix()]

        generated_ass_files = []
        type_map = {"video": "v", "audio": "a", "subtitle": "s"}
        
        codec_ext_map = {
            "avc": ".264", "hevc": ".hevc", "mpeg-4 visual": ".mkv", "vp9": ".ivf", "av1": ".ivf",
            "aac": ".aac", "mp3": ".mp3", "ac-3": ".ac3", "e-ac-3": ".eac3", "dts": ".dts", "mlp fba": ".thd",
            "dts-hd": ".dts", "truehd": ".thd", "flac": ".flac", "opus": ".opus", 
            "vorbis": ".ogg", "pcm": ".wav", "mpeg audio": ".mp3", "mpega": ".mp3",
            "ass": ".ass", "advanced ssa": ".ass", "ssa": ".ssa",
            "subrip": ".srt", "srt": ".srt", "pgs": ".sup", "hdmv pgs": ".sup", "vobsub": ".sub"
        }

        for track in tracks:
            t_type = track.get("type")
            t_idx = track.get("idx", 0)
            t_codec = track.get("codec", "").lower()
            
            # 不处理附加在此处的章节事件
            if t_type not in type_map:
                continue

            ffmpeg_stream_type = type_map.get(t_type)
            stream_specifier = f"0:{ffmpeg_stream_type}:{t_idx}"
            
            out_ext = codec_ext_map.get(t_codec)
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
                # 遇到 m2ts/ts 封装中的 PCM 音频时强制使用 pcm_s24le 以免 ffmpeg -c copy 报错
                cmd_list.extend(["-c:a", "pcm_s24le"])
                # 如果后缀还没有改成wav，强行改一下
                if not out_posix.endswith(".wav"):
                    out_posix = out_posix.rsplit(".", 1)[0] + ".wav"
            else:
                cmd_list.extend(["-c", "copy"])
                
            cmd_list.append(out_posix)

            if t_type == "subtitle" and option_state.get("sub_departition"):
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

    def _run_cli_with_progress(self, task_id: str, file_idx: int, total_files: int, file_name: str, cmd_list: list, tool_type="ffmpeg"):
        # FFMPEG 继续使用 ffmpeg_progress_yield 库
        if tool_type == "ffmpeg":
            self._run_long_task_with_progress(task_id, file_idx, total_files, file_name, cmd_list)
            return
            
        # MKVEXTRACT 使用原生 subprocess 轮询解析 stdout 中的 Progress: XX%
        start_time = time.time()
        
        def format_time(seconds: float) -> str:
            if seconds < 0: return "--:--"
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"

        import subprocess
        import re
        
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
                        time_left_str = format_time(rem_time)

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


    def _run_long_task_with_progress(self, task_id: str, file_idx: int, total_files: int, file_name: str, cmd_list: list):
        start_time = time.time()
        
        def format_time(seconds: float) -> str:
            if seconds < 0: return "--:--"
            m, s = divmod(int(seconds), 60)
            h, m = divmod(m, 60)
            if h > 0:
                return f"{h:02d}:{m:02d}:{s:02d}"
            return f"{m:02d}:{s:02d}"

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
                    time_left_str = format_time(rem_time)

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
                error_msg = f"处理时发生错误: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                signalBus.taskError.emit(task_id, str(e))
        finally:
            self._current_ff_process = None
