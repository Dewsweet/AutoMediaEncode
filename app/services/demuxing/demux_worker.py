import os
import time
import json
import shlex
import traceback
import subprocess
import re
from collections import deque
from uuid import uuid4
from pathlib import Path
from PySide6.QtCore import QThread
from ffmpeg_progress_yield import FfmpegProgress

from ...common.signal_bus import signalBus
from ...common.logger import logger
from ..tool_service import ToolService
from ..error_service import ErrorService
from .desubsetting_service import SubtitleProcessService
from ..output_service import OutputTransaction, safe_filename
from ..process_service import kill_process

class DemuxWorker(QThread):
    def __init__(self, payload: dict, parent=None):
        super().__init__(parent)
        self.payload = payload
        self._is_cancelled = False
        self._has_error = False
        self._current_ff_process = None

        self._codec_ext_map = {
            # 视频
            "avc": ".h264", "hevc": ".h265", "v_mpeg4/iso/avc": ".h264", "v_mpegh/iso/hevc": ".h265", "vp8": ".ivf", "vp9": ".ivf", "av1": ".ivf", "mpeg-4 visual": ".mkv", "ffv1": ".mkv",
            # 音频
            "aac": ".aac", "alac": ".caf", "flac": ".flac", "opus": ".opus", "vorbis": ".ogg", "pcm": ".wav", "mpeg audio": ".mp3", "mpega": ".mp3", "mp3": ".mp3",
            "ac-3": ".ac3", "e-ac-3": ".eac3", "dts": ".dts", "dts-hd": ".dts", 
            "truehd": ".thd", "mlp fba": ".thd",
            # 字幕
            "ass": ".ass", "advanced ssa": ".ass", "ssa": ".ssa", "subrip": ".srt", "srt": ".srt", "utf-8": ".srt", "timed text": ".srt", "webvtt": ".vtt", "vtt": ".vtt", "pgs": ".sup", "hdmv pgs": ".sup", "vobsub": ".sub"
        }

    def stop(self):
        """外部调用以强制停止任务"""
        self._is_cancelled = True
        kill_process(self._current_ff_process)

    def _fail(self, task_id, message):
        if not self._is_cancelled and not self._has_error:
            self._has_error = True
            signalBus.taskError.emit(task_id, message)

    def _output_dir(self, file_path):
        output = self.payload.get("states", {}).get("output_state", {})
        return file_path.parent if output.get("use_source_dir", True) else Path(output.get("output_dir") or file_path.parent)

    def _track_output(self, file_path, track):
        kind = track.get("type")
        options = self.payload.get("states", {}).get("option_state", {})
        matroska = file_path.suffix.lower() in {".mkv", ".mka", ".mks"}
        if kind == "attachment":
            if not matroska:
                raise ValueError(self.tr("仅支持从 Matroska 文件提取附件"))
            name = safe_filename(track.get("filename") or f"attachment_{track.get('idx', 1)}")
        elif kind == "chapter":
            name = safe_filename(f"{file_path.stem}_chapters.{options.get('chapter_suffix', 'XML').lower()}")
        elif kind in {"video", "audio", "subtitle"}:
            codec = str(track.get("codec") or "").lower()
            ext = self._codec_ext_map.get(codec)
            if file_path.suffix.lower() in {".m2ts", ".ts"} and kind == "audio" and "pcm" in codec:
                ext = ".wav"
            if not ext:
                if matroska:
                    raise ValueError(self.tr("不支持的抽流编码格式: {codec}").format(codec=codec))
                ext = {"video": ".mkv", "audio": ".mka", "subtitle": ".srt"}[kind]
            index = track.get("id", "") if matroska else track.get("idx", 0)
            name = safe_filename(f"{file_path.stem}_track_{kind}_{index}{ext}")
        else:
            raise ValueError(self.tr("不支持的抽流轨道类型: {type}").format(type=kind))
        return self._output_dir(file_path) / name

    def run(self):
        task_id = self.payload.get("task_id")
        files = self.payload.get("files", [])
        total_files = len(files)
        task_start_time = time.time()
        
        logger.info(f"\n\n\n{'='*20} 抽流任务开始编排: {task_id} {'='*20}")
        logger.info(f"包含文件数: {total_files}")
        logger.debug(f"Payload 详情:\n{json.dumps(self.payload, indent=4, ensure_ascii=False)}")

        self._outputs = OutputTransaction(files)
        try:
            for f_path in files:
                file_path = Path(f_path)
                for track in self.payload.get("states", {}).get("tracks_state", {}).get(f_path, []):
                    target = self._track_output(file_path, track)
                    self._outputs.plan(target)
                    if target.suffix == ".sub" and file_path.suffix.lower() in {".mkv", ".mka", ".mks"}:
                        self._outputs.plan(target.with_suffix(".idx"))
            for idx, f_path in enumerate(files, start=1):
                if self._is_cancelled or self._has_error:
                    break
                self._process_single_file(task_id, f_path, idx, total_files)
            if not self._is_cancelled and not self._has_error:
                self._outputs.commit()
        except Exception as exc:
            logger.exception(f"[Task {task_id}] 抽流任务失败")
            self._fail(task_id, self.tr("任务执行失败: {error}").format(error=str(exc)))
        finally:
            self._outputs.cleanup()

        if not self._is_cancelled and not self._has_error:
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
        
        if is_matroska:
            # mkvextract 不支持 V_FFV1 的裸流导出，使用 FFmpeg 无损复制为独立 MKV。
            ffmpeg_tracks = [t for t in tracks if t.get("type") == "video" and str(t.get("codec", "")).lower() == "ffv1"]
            native_tracks = [t for t in tracks if t not in ffmpeg_tracks]
            if native_tracks:
                self._extract_with_mkvextract(task_id, file_path, fname, out_dir_path, native_tracks, option_state, idx, total_files)
            if ffmpeg_tracks and not self._has_error and not self._is_cancelled:
                self._extract_with_ffmpeg(task_id, file_path, fname, out_dir_path, ffmpeg_tracks, option_state, idx, total_files)
        else:
            self._extract_with_ffmpeg(task_id, file_path, fname, out_dir_path, tracks, option_state, idx, total_files)

    def _extract_with_mkvextract(self, task_id: str, file_path: Path, fname: str, out_dir_path: Path, tracks: list, option_state: dict, idx: int, total_files: int):
        """mkvextract 组装参数"""
        mkvextract_path = ToolService.get_tool_path('mkvextract')
        if not mkvextract_path:
            logger.error(f"[{task_id}] 未找到 MkvExtract 可执行文件, 停止运行")
            self._fail(task_id, self.tr("未找到 MkvExtract 可执行文件, 请检查相关设置或查看 log"))
            return

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
                ch_out = self._outputs.stage(self._track_output(file_path, track))
                if ch_format in ["txt", "ogm"]:
                    chapter_args.extend(["-s", ch_out.as_posix()])
                else:
                    chapter_args.append(ch_out.as_posix())
                continue
                
            if t_type == "attachment":
                a_idx = track.get("idx", 1)  # attachment 本身的 1-based index
                out_file = self._outputs.stage(self._track_output(file_path, track))
                attachments_args.append(f"{a_idx}:{out_file.as_posix()}")
                continue
                
            t_id = track.get("id", "")
            if str(t_id) == "":
                continue
                
            out_file = self._outputs.stage(self._track_output(file_path, track))
            out_posix = out_file.as_posix()
            
            tracks_args.append(f"{t_id}:{out_posix}")
            
            if out_file.suffix in {".ass", ".ssa"} and option_state.get("desubsetting"):
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
            logger.error(f"[{task_id}] 未找到 ffmpeg 可执行文件, 停止运行")
            self._fail(task_id, self.tr("未找到 FFMpeg 可执行文件, 请检查相关设置或查看 log"))
            return

        cmd_list = [ffmpeg_bin_path, "-y", "-i", file_path.as_posix()]

        generated_ass_files = []
        chapter_ffmeta = None
        chapter_out = None
        ch_format = None
        type_map = {"video": "v", "audio": "a", "subtitle": "s"}

        for track in tracks:
            t_type = track.get("type")
            t_idx = track.get("idx", 0)
            t_codec = track.get("codec", "").lower()
            
            if t_type == "chapter":
                ch_format = option_state.get("chapter_suffix", "XML").lower()
                chapter_out = self._outputs.stage(self._track_output(file_path, track))
                chapter_ffmeta = chapter_out.parent / f".ame-chapters-{uuid4().hex}.txt"
                cmd_list.extend(["-f", "ffmetadata", chapter_ffmeta.as_posix()])
                continue

            if t_type not in type_map:
                continue

            ffmpeg_stream_type = type_map.get(t_type)
            stream_specifier = f"0:{ffmpeg_stream_type}:{t_idx}"
            
            out_file = self._outputs.stage(self._track_output(file_path, track))
            out_posix = out_file.as_posix()
            
            cmd_list.extend(["-map", stream_specifier])
            
            # m2ts PCM 处理特判策略
            if file_path.suffix.lower() in [".m2ts", ".ts"] and "pcm" in t_codec:
                cmd_list.extend(["-c:a", "pcm_s24le"])
                if not out_posix.endswith(".wav"):
                    out_posix = out_posix.rsplit(".", 1)[0] + ".wav"
            elif t_type == "subtitle" and out_file.suffix in {".srt", ".ass", ".ssa", ".vtt"}:
                encoder = {".srt": "srt", ".ass": "ass", ".ssa": "ass", ".vtt": "webvtt"}[out_file.suffix]
                cmd_list.extend(["-c:s", encoder])
            else:
                cmd_list.extend(["-c", "copy"])
                
            cmd_list.append(out_posix)

            if out_file.suffix in {".ass", ".ssa"} and option_state.get("desubsetting"):
                generated_ass_files.append(out_posix)

        has_valid_tracks = chapter_ffmeta is not None or any(t.get("type") in ("video", "audio", "subtitle") for t in tracks)

        if has_valid_tracks:
            # 
            logger.info(f"[Task {task_id}] FFmpeg command:\n" + shlex.join(cmd_list))
            self._run_cli_with_progress(task_id, idx, total_files, file_path.name, cmd_list, "ffmpeg")

        if chapter_ffmeta is not None and chapter_ffmeta.exists() and not self._is_cancelled and not self._has_error:
            chapters_raw = []
            cur = None
            for line in chapter_ffmeta.read_text("utf-8").splitlines():
                stripped = line.strip()
                if stripped == "[CHAPTER]":
                    cur = {}
                    chapters_raw.append(cur)
                elif cur is not None and "=" in stripped:
                    k, v = stripped.split("=", 1)
                    cur[k.strip()] = v.strip()

            if chapters_raw:
                if ch_format == "xml":
                    DemuxWorker._write_chapters_xml(chapters_raw, chapter_out)
                else:
                    DemuxWorker._write_chapters_txt(chapters_raw, chapter_out)
                logger.info(f"[{task_id}] 章节提取成功: {chapter_out.name}")

            chapter_ffmeta.unlink(missing_ok=True)

        self._post_process_subtitles(generated_ass_files)

    @staticmethod
    def _write_chapters_xml(chapters: list, out_path: Path):
        import xml.etree.ElementTree as ET

        def _ms_to_ts(ms: int) -> str:
            h, r = divmod(ms, 3600000)
            m, r = divmod(r, 60000)
            s, ms_p = divmod(r, 1000)
            return f"{h:02d}:{m:02d}:{s:02d}.{ms_p:03d}"

        def _value_to_ms(value_str: str, timebase_str: str) -> int:
            value = int(value_str)
            parts = timebase_str.split("/")
            num = int(parts[0])
            den = int(parts[1])
            return int(value * 1000 * num / den)

        root = ET.Element("Chapters")
        edition = ET.SubElement(root, "EditionEntry")

        for ch in chapters:
            atom = ET.SubElement(edition, "ChapterAtom")
            tb = ch.get("TIMEBASE", "1/1000")
            start_ms = _value_to_ms(ch.get("START", "0"), tb)
            end_ms = _value_to_ms(ch.get("END", "0"), tb)
            ET.SubElement(atom, "ChapterTimeStart").text = _ms_to_ts(start_ms)
            ET.SubElement(atom, "ChapterTimeEnd").text = _ms_to_ts(end_ms)
            display = ET.SubElement(atom, "ChapterDisplay")
            ET.SubElement(display, "ChapterString").text = ch.get("title", "")

        tree = ET.ElementTree(root)
        tree.write(out_path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _write_chapters_txt(chapters: list, out_path: Path):
        def _ms_to_ts(ms: int) -> str:
            h, r = divmod(ms, 3600000)
            m, r = divmod(r, 60000)
            s, ms_p = divmod(r, 1000)
            return f"{h:02d}:{m:02d}:{s:02d}.{ms_p:03d}"

        def _value_to_ms(value_str: str, timebase_str: str) -> int:
            value = int(value_str)
            parts = timebase_str.split("/")
            num = int(parts[0])
            den = int(parts[1])
            return int(value * 1000 * num / den)

        lines = []
        for i, ch in enumerate(chapters, start=1):
            tb = ch.get("TIMEBASE", "1/1000")
            start_ms = _value_to_ms(ch.get("START", "0"), tb)
            lines.append(f"CHAPTER{i:02d}={_ms_to_ts(start_ms)}")
            lines.append(f"CHAPTER{i:02d}NAME={ch.get('title', '')}")

        out_path.write_text("\n".join(lines), encoding="utf-8")

    def _post_process_subtitles(self, generated_ass_files: list):
        if not self._is_cancelled and not self._has_error and generated_ass_files:
            for ass_f in generated_ass_files:
                if Path(ass_f).exists():
                    logger.info(f"正在进行字幕去子集化处理: {ass_f}")
                    success = SubtitleProcessService.process_file(ass_f)
                    if success:
                        logger.info(f"字幕去子集化成功: {ass_f}")
                    else:
                        raise RuntimeError(self.tr("字幕去子集化失败: {path}").format(path=ass_f))

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
            process = subprocess.Popen(
                cmd_list,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                creationflags=creation_flags, 
                text=True, 
                encoding='utf-8', 
                errors='replace'
            )
            self._current_ff_process = process
            output_lines = deque(maxlen=100)
            if self._is_cancelled:
                kill_process(process)
            progress_pattern = re.compile(r"Progress:\s*(\d+)%")
            
            for line in process.stdout:
                output_lines.append(line)
                if self._is_cancelled:
                    kill_process(process)
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
            
            returncode = process.wait()
            if not self._is_cancelled and returncode not in (0, 1):
                main_error = ErrorService.cli_error("mkvextract", "".join(output_lines))
                self._fail(task_id, self.tr("文件 [{filename}] 抽流失败 (code {code}):\n{error}").format(filename=file_name, code=returncode, error=main_error))
            elif not self._is_cancelled:
                signalBus.taskProgressUpdated.emit(task_id, file_idx, total_files, file_name, 100.0, "00:00:00")
                
        except Exception as e:
            if not self._is_cancelled:
                error_msg = self.tr("处理时发生错误: {error}\n{traceback}").format(error=str(e), traceback=traceback.format_exc())
                logger.error(error_msg)
                main_error = ErrorService.cli_error("mkvextract", str(error_msg))
                main_error_msg = self.tr("文件 [{filename}] 处理失败\n[可能因为]: {error}").format(filename=file_name, error=main_error)
                self._fail(task_id, main_error_msg)
        finally:
            if 'process' in locals():
                kill_process(process)
                process.wait()
                process.stdout.close()
            self._current_ff_process = None


    def _run_ffmpeg_task_with_progress(self, task_id: str, file_idx: int, total_files: int, file_name: str, cmd_list: list):
        start_time = time.time()

        popen_kwargs = {}
        if os.name == 'nt':
            popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            popen_kwargs['stdin'] = subprocess.DEVNULL

        try:
            self._current_ff_process = FfmpegProgress(cmd_list)
            for progress in self._current_ff_process.run_command_with_progress(popen_kwargs=popen_kwargs):
                if self._is_cancelled:
                    kill_process(self._current_ff_process)
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
                error_msg = self.tr("文件 [{filename}] 处理失败\n[可能因为]: {error}").format(filename=file_name, error=main_error)
                self._fail(task_id, error_msg)
        finally:
            self._current_ff_process = None
