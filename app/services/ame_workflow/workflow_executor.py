import os
import time
import uuid
import subprocess
import json
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .workflow_validator import WorkflowValidator
from app.components.ame_workflow.node_item import AMENodeItem
from app.components.ame_workflow.node_edge import AMEEdge
from app.services.tool_service import ToolService
from app.services.error_service import ErrorService
from app.common.logger import logger


class AMEWorkflowExecutor(QThread):
    progress_updated = Signal(int)
    node_status_changed = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(self, nodes: list, edges: list, parent=None):
        super().__init__(parent)
        self._nodes = list(nodes)
        self._edges = list(edges)
        self._cancelled = False
        self._node_map = {n.node_id(): n for n in self._nodes}
        self._output_data = {}
        self._temp_dir = ""

    def cancel(self):
        self._cancelled = True

    def run(self):
        validator = WorkflowValidator()
        if not validator.validate(self._nodes, self._edges):
            self.error_occurred.emit("; ".join(validator.errors))
            return

        execution_order = validator.get_topological_order(self._nodes, self._edges)

        connected_ids = set()
        for e in self._edges:
            sp = e.source_port()
            tp = e.target_port()
            if sp and tp:
                connected_ids.add(sp.node().node_id())
                connected_ids.add(tp.node().node_id())
        execution_order = [n for n in execution_order if n.node_id() in connected_ids]
        if not execution_order:
            execution_order = [n for n in self._nodes if n.node_type() == 'output']
        total = len(execution_order) if execution_order else 1

        self._resolve_temp_dir()

        for i, node in enumerate(execution_order):
            if self._cancelled:
                return

            self.node_status_changed.emit(node.node_id(), "running")
            self._collect_inputs(node)
            success = self._execute_node(node)

            if self._cancelled:
                return

            if success:
                self.node_status_changed.emit(node.node_id(), "done")
            else:
                self.node_status_changed.emit(node.node_id(), "error")
                self.error_occurred.emit(f"节点 {node.node_name()} 执行失败")
                return

            self.progress_updated.emit(int((i + 1) / total * 100))

    def _resolve_temp_dir(self):
        for node in self._nodes:
            if node.node_type() == 'workspace':
                wd = node.params().get('work_dir', '')
                if wd and os.path.isdir(wd):
                    self._temp_dir = os.path.join(wd, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return

        for node in self._nodes:
            if node.node_type() == 'output':
                op = node.params().get('output_path', '')
                if op:
                    out_dir = os.path.dirname(op) or os.path.abspath('.')
                    self._temp_dir = os.path.join(out_dir, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return

        for node in self._nodes:
            if node.node_type() == 'input_file':
                fp = node.params().get('file_path', '')
                if fp and os.path.isfile(fp):
                    src_dir = os.path.dirname(fp) or os.path.abspath('.')
                    self._temp_dir = os.path.join(src_dir, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return

        self._temp_dir = os.path.join(os.path.abspath('.'), 'temp')
        os.makedirs(self._temp_dir, exist_ok=True)

    def _collect_inputs(self, node: AMENodeItem):
        for e in self._edges:
            tp = e.target_port()
            sp = e.source_port()
            if tp is None or sp is None:
                continue
            if tp.node().node_id() == node.node_id():
                src_key = (sp.node().node_id(), sp.port_name())
                tgt_key = (node.node_id(), tp.port_name())
                if src_key in self._output_data:
                    self._output_data[tgt_key] = self._output_data[src_key]

    def _store_output(self, node: AMENodeItem, port_name: str, data: dict):
        key = (node.node_id(), port_name)
        self._output_data[key] = data

    def _get_input_for(self, node: AMENodeItem, port_name: str):
        for e in self._edges:
            tp = e.target_port()
            sp = e.source_port()
            if tp is None or sp is None:
                continue
            if tp.node().node_id() == node.node_id() and tp.port_name() == port_name:
                src_key = (sp.node().node_id(), sp.port_name())
                if src_key in self._output_data:
                    return self._output_data[src_key]
        return None

    def _execute_node(self, node: AMENodeItem) -> bool:
        node_type = node.node_type()
        params = node.params()
        try:
            if node_type == 'workspace':
                return True
            elif node_type == 'input_file':
                return self._do_input_file(node, params)
            elif node_type == 'splitter':
                return self._do_splitter(node, params)
            elif node_type in ('encoder_x264', 'encoder_x265', 'encoder_svtav1'):
                return self._do_cli_encoder(node, node_type, params)
            elif node_type == 'encoder_ffmpeg_video':
                return self._do_ffmpeg_video(node, params)
            elif node_type == 'encoder_ffmpeg_audio':
                return self._do_ffmpeg_audio(node, params)
            elif node_type == 'muxer_mkvmerge':
                return self._do_muxer_mkvmerge(node, params)
            elif node_type == 'muxer_ffmpeg':
                return self._do_muxer_ffmpeg(node, params)
            elif node_type == 'output':
                return True
            else:
                return True
        except Exception:
            import traceback
            logger.error(f"Node {node.node_name()} failed: {traceback.format_exc()}")
            return False

    def _do_input_file(self, node, params):
        fp = params.get('file_path', '')
        if not fp or not os.path.isfile(fp):
            return False

        old_wd = os.getcwd()

        from app.common.media_utils import classify_files
        classified = classify_files([fp])

        data_video = {"files": [], "type": "video"}
        data_audio = {"files": [], "type": "audio"}
        data_sub = {"files": [], "type": "subtitle"}
        data_chap = {"files": [], "type": "chapter"}

        ext = Path(fp).suffix.lower()
        if classified.get('video') or ext in {'.m2ts', '.ts', '.mts', '.mkv', '.mp4', '.avi', '.mov', '.h264', '.h265', '.ivf'}:
            data_video["files"] = [fp]
            data_video["meta"] = {"source": fp}
            self._store_output(node, 'video', data_video)
        if classified.get('audio') or ext in {'.aac', '.flac', '.wav', '.opus', '.mp3', '.ac3', '.dts', '.eac3', '.ogg'}:
            data_audio["files"] = [fp]
            data_audio["meta"] = {"source": fp}
            self._store_output(node, 'audio', data_audio)
        if classified.get('subtitle') or ext in {'.ass', '.srt', '.vtt', '.lrc'}:
            data_sub["files"] = [fp]
            self._store_output(node, 'subtitle', data_sub)
        if ext in {'.xml', '.txt', '.cue'}:
            data_chap["files"] = [fp]
            self._store_output(node, 'chapter', data_chap)

        if old_wd:
            try:
                os.chdir(old_wd)
            except OSError:
                pass

        return True

    def _do_splitter(self, node, params):
        input_data = self._get_input_for(node, 'input')
        if not input_data:
            return False
        files = input_data.get('files', [])
        if not files:
            return False

        src = files[0]
        tool = params.get('tool', 'ffmpeg')
        mode = params.get('mode', 'extract')

        tool_path = ToolService.get_tool_path('ffmpeg')
        ls_wd = os.getcwd()
        if mode == 'refer':
            self._store_output(node, 'video', {"files": [src], "type": "video", "mode": "refer"})
            self._store_output(node, 'audio', {"files": [src], "type": "audio", "mode": "refer"})
            self._store_output(node, 'subtitle', {"files": [src], "type": "subtitle", "mode": "refer"})
            self._store_output(node, 'chapter', {"files": [src], "type": "chapter", "mode": "refer"})
            if ls_wd:
                try:
                    os.chdir(ls_wd)
                except OSError:
                    pass
            return True

        video_files, audio_files, sub_files, chap_files = self._probe_tracks(tool_path, src)
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        extracted_video = []
        extracted_audio = []
        extracted_sub = []
        extracted_chap = []

        for idx, codec in video_files:
            ext = self._codec_to_ext(codec)
            dst = os.path.join(self._temp_dir, f"track_video_{idx}{ext}")
            cmd = [tool_path, '-i', src, '-map', f'0:{idx}', '-c', 'copy', dst, '-y']
            try:
                subprocess.run(cmd, creationflags=creation_flags, capture_output=True,
                             timeout=300, cwd=os.path.dirname(tool_path) or None)
                if os.path.isfile(dst):
                    extracted_video.append(dst)
            except Exception:
                pass

        for idx, codec in audio_files:
            ext = self._codec_to_ext(codec)
            dst = os.path.join(self._temp_dir, f"track_audio_{idx}{ext}")
            cmd = [tool_path, '-i', src, '-map', f'0:{idx}', '-c', 'copy', dst, '-y']
            try:
                subprocess.run(cmd, creationflags=creation_flags, capture_output=True,
                             timeout=300, cwd=os.path.dirname(tool_path) or None)
                if os.path.isfile(dst):
                    extracted_audio.append(dst)
            except Exception:
                pass

        for idx, codec in sub_files:
            ext = self._codec_to_ext(codec)
            dst = os.path.join(self._temp_dir, f"track_subtitle_{idx}{ext}")
            cmd = [tool_path, '-i', src, '-map', f'0:{idx}', '-c', 'copy', dst, '-y']
            try:
                subprocess.run(cmd, creationflags=creation_flags, capture_output=True,
                             timeout=300, cwd=os.path.dirname(tool_path) or None)
                if os.path.isfile(dst):
                    extracted_sub.append(dst)
            except Exception:
                pass

        if extracted_video:
            self._store_output(node, 'video', {"files": extracted_video, "type": "video"})
        if extracted_audio:
            self._store_output(node, 'audio', {"files": extracted_audio, "type": "audio"})
        if extracted_sub:
            self._store_output(node, 'subtitle', {"files": extracted_sub, "type": "subtitle"})
        if extracted_chap:
            self._store_output(node, 'chapter', {"files": extracted_chap, "type": "chapter"})

        if ls_wd:
            try:
                os.chdir(ls_wd)
            except OSError:
                pass

        return True

    def _probe_tracks(self, ffmpeg_path, src):
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        video, audio, sub, chap = [], [], [], []
        try:
            result = subprocess.run(
                [ffmpeg_path, '-i', src, '-hide_banner'],
                capture_output=True, text=True, creationflags=creation_flags, timeout=60,
                cwd=os.path.dirname(ffmpeg_path) or None
            )
            for line in result.stderr.split('\n'):
                line = line.strip()
                if not line or not line.startswith('  Stream'):
                    continue
                parts = line.split('Stream #0:')[1].split('[')[0]
                stream_idx = parts.split('(')[0].strip().split(':')[0]
                try:
                    idx = int(stream_idx)
                except ValueError:
                    continue
                codec = ''
                if 'Video:' in line:
                    codec = line.split('Video:')[1].split()[0].split(',')[0]
                    video.append((idx, codec))
                elif 'Audio:' in line:
                    codec = line.split('Audio:')[1].split()[0].split(',')[0]
                    audio.append((idx, codec))
                elif 'Subtitle:' in line:
                    codec = line.split('Subtitle:')[1].split()[0].split(',')[0]
                    sub.append((idx, codec))
        except Exception:
            pass
        return video, audio, sub, chap

    def _codec_to_ext(self, codec):
        codec = codec.lower().replace('_', '')
        mapping = {
            'h264': '.h264', 'avc': '.h264',
            'hevc': '.h265', 'h265': '.h265',
            'av1': '.ivf', 'vp9': '.ivf', 'vp8': '.ivf',
            'aac': '.aac', 'flac': '.flac', 'opus': '.opus',
            'vorbis': '.ogg', 'pcm': '.wav', 'mp3': '.mp3',
            'ac3': '.ac3', 'eac3': '.eac3', 'dts': '.dts',
            'dtshd': '.dts', 'truehd': '.thd',
            'ass': '.ass', 'srt': '.srt', 'vtt': '.vtt',
            'subrip': '.srt', 'webvtt': '.vtt',
            'movtext': '.srt', 'hdmvpgs': '.sup',
            'mjpeg': '.mjpeg', 'mpeg4': '.m4v',
            'mpeg2video': '.m2v', 'vc1': '.vc1',
            'wmv3': '.wmv', 'prores': '.mov',
            'png': '.png', 'bmp': '.bmp',
            'ttf': '.ttf', 'otf': '.otf',
        }
        for k, v in mapping.items():
            if k in codec:
                return v
        return '.mkv'

    def _do_cli_encoder(self, node, node_type, params):
        input_data = self._get_input_for(node, 'input')
        if not input_data:
            return False
        files = input_data.get('files', [])
        if not files:
            return False

        src = files[0]
        ext_map = {'encoder_x264': '.h264', 'encoder_x265': '.h265', 'encoder_svtav1': '.ivf'}
        ext = ext_map.get(node_type, '.h264')
        tool_key_map = {'encoder_x264': 'x264', 'encoder_x265': 'x265', 'encoder_svtav1': 'SvtAv1'}
        tool_key = tool_key_map.get(node_type, 'x264')
        dst = os.path.join(self._temp_dir, f"encoded_{node.node_id()}{ext}")

        cli_path = ToolService.get_tool_path(tool_key)
        if not cli_path or not os.path.isfile(cli_path):
            logger.warning(f"CLI tool {tool_key} not found")
            return False

        preset_name = params.get('preset', '')
        custom_cli = params.get('custom_cli', '')

        if preset_name:
            from app.services.setting.preset_service import preset_service
            encoder_map = {'encoder_x264': 'x264', 'encoder_x265': 'x265', 'encoder_svtav1': 'SVTAV1'}
            enc_key = encoder_map.get(node_type, 'x264')
            presets = preset_service.get_presets_by_encoder(enc_key)
            if presets and preset_name in presets:
                cli_args = presets[preset_name]
            else:
                cli_args = preset_name
        elif custom_cli:
            cli_args = custom_cli
        else:
            cli_args = ''

        import shlex
        try:
            args_list = shlex.split(cli_args) if cli_args else []
        except ValueError:
            args_list = cli_args.split() if cli_args else []

        cmd = [cli_path, '-o', dst] + args_list + [src]
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, creationflags=creation_flags, capture_output=True, text=True,
                timeout=14400, cwd=os.path.dirname(cli_path) or None
            )
            if result.returncode != 0 and result.returncode != 1:
                err = ErrorService.ffmpeg_error(result.stderr) if hasattr(ErrorService, 'ffmpeg_error') else result.stderr[:200]
                logger.error(f"CLI encoder failed: {err}")
                return False
            if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
                return False
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

        self._store_output(node, node.output_ports()[0].port_name() if node.output_ports() else 'encoded',
                          {"files": [dst], "type": "video"})
        return True

    def _do_ffmpeg_video(self, node, params):
        input_data = self._get_input_for(node, 'input')
        if not input_data:
            return False
        files = input_data.get('files', [])
        if not files:
            return False

        src = files[0]
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path:
            return False

        codec = params.get('codec', 'libx264')
        ext = '.h264' if 'x264' in codec else '.h265' if 'x265' in codec or 'hevc' in codec else '.mkv'
        dst = os.path.join(self._temp_dir, f"encoded_video_{node.node_id()}{ext}")

        cmd = [ffmpeg_path, '-i', src]
        cmd.extend(['-c:v', codec])

        rc_mode = params.get('rc_mode', 'crf')
        if rc_mode == 'crf':
            cmd.extend(['-crf', str(params.get('quality_val', 23))])
        elif rc_mode == 'abr':
            cmd.extend(['-b:v', params.get('bitrate', '5000k')])
        elif rc_mode == 'cqp':
            cmd.extend(['-qp', str(params.get('quality_val', 23))])

        preset = params.get('preset', '')
        if preset:
            cmd.extend(['-preset', preset])
        profile = params.get('profile', '')
        if profile:
            cmd.extend(['-profile:v', profile])
        tune = params.get('tune', '')
        if tune:
            cmd.extend(['-tune', tune])
        custom = params.get('custom_options', '')
        if custom:
            import shlex
            try:
                cmd.extend(shlex.split(custom))
            except ValueError:
                cmd.extend(custom.split())

        cmd.extend(['-an', dst, '-y'])
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        try:
            result = subprocess.run(
                cmd, creationflags=creation_flags, capture_output=True, text=True,
                timeout=14400, cwd=os.path.dirname(ffmpeg_path) or None
            )
            if result.returncode != 0:
                return False
            if not os.path.isfile(dst):
                return False
        except Exception:
            return False

        self._store_output(node, 'video', {"files": [dst], "type": "video"})
        return True

    def _do_ffmpeg_audio(self, node, params):
        input_data = self._get_input_for(node, 'input')
        if not input_data:
            return False
        files = input_data.get('files', [])
        if not files:
            return False

        src = files[0]
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path:
            return False

        codec = params.get('codec', 'aac')
        ext_map = {'aac': '.aac', 'libmp3lame': '.mp3', 'flac': '.flac', 'opus': '.opus', 'libvorbis': '.ogg', 'ac3': '.ac3'}
        ext = ext_map.get(codec, '.m4a')
        dst = os.path.join(self._temp_dir, f"encoded_audio_{node.node_id()}{ext}")

        cmd = [ffmpeg_path, '-i', src, '-c:a', codec]

        rc_mode = params.get('rc_mode', 'cbr')
        if rc_mode == 'cbr':
            cmd.extend(['-b:a', params.get('bitrate', '192k')])
        elif rc_mode == 'abr':
            cmd.extend(['-b:a', params.get('bitrate', '192k')])
        elif rc_mode == 'quality':
            cmd.extend(['-q:a', str(params.get('quality_val', 5))])

        custom = params.get('custom_options', '')
        if custom:
            import shlex
            try:
                cmd.extend(shlex.split(custom))
            except ValueError:
                cmd.extend(custom.split())

        cmd.extend(['-vn', dst, '-y'])
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        try:
            result = subprocess.run(
                cmd, creationflags=creation_flags, capture_output=True, text=True,
                timeout=14400, cwd=os.path.dirname(ffmpeg_path) or None
            )
            if result.returncode != 0:
                return False
            if not os.path.isfile(dst):
                return False
        except Exception:
            return False

        self._store_output(node, 'audio', {"files": [dst], "type": "audio"})
        return True

    def _do_muxer_mkvmerge(self, node, params):
        mkvmerge_path = ToolService.get_tool_path('mkvmerge')
        if not mkvmerge_path:
            return False

        video_input = self._get_input_for(node, 'video')
        audio_input = self._get_input_for(node, 'audio')
        sub_input = self._get_input_for(node, 'subtitle')
        chap_input = self._get_input_for(node, 'chapter')
        attach_input = self._get_input_for(node, 'attachment')

        video_files = video_input.get('files', []) if video_input else []
        audio_files = audio_input.get('files', []) if audio_input else []
        sub_files = sub_input.get('files', []) if sub_input else []
        chap_files = chap_input.get('files', []) if chap_input else []
        attach_files = attach_input.get('files', []) if attach_input else []

        output_path = self._resolve_output_path(node)
        if not output_path:
            return False

        cmd = [mkvmerge_path, '-o', output_path]

        for f in video_files:
            cmd.extend(['-d', '0', f])
        for f in audio_files:
            cmd.extend(['-a', '0', f])
        for f in sub_files:
            cmd.extend(['-s', '0', f])
        for f in chap_files:
            cmd.extend(['--chapters', f])
        for f in attach_files:
            cmd.extend(['--attach-file', f])

        if not video_files and not audio_files and not sub_files and not chap_files:
            for f in video_files:
                cmd.append(f)
            for f in audio_files:
                cmd.append(f)

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        try:
            result = subprocess.run(
                cmd, creationflags=creation_flags, capture_output=True, text=True,
                timeout=14400, cwd=os.path.dirname(mkvmerge_path) or None
            )
            if result.returncode not in (0, 1):
                return False
            if not os.path.isfile(output_path):
                return False
        except Exception:
            return False

        self._store_output(node, 'output', {"files": [output_path], "type": "container"})
        return True

    def _do_muxer_ffmpeg(self, node, params):
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path:
            return False

        video_input = self._get_input_for(node, 'video')
        audio_input = self._get_input_for(node, 'audio')

        video_files = video_input.get('files', []) if video_input else []
        audio_files = audio_input.get('files', []) if audio_input else []

        container = params.get('container', 'mp4')
        output_path = self._resolve_output_path(node)
        if not output_path:
            ext = '.mp4' if container == 'mp4' else '.mov'
            output_path = os.path.join(self._temp_dir, f"muxed_{node.node_id()}{ext}")

        cmd = [ffmpeg_path]
        for src in video_files:
            cmd.extend(['-i', src])
        for src in audio_files:
            cmd.extend(['-i', src])

        stream_idx = 0
        for _ in video_files:
            cmd.extend(['-map', str(stream_idx)])
            stream_idx += 1
        for _ in audio_files:
            cmd.extend(['-map', str(stream_idx)])
            stream_idx += 1

        cmd.extend(['-c', 'copy'])
        if container == 'mp4' and params.get('faststart', False):
            cmd.extend(['-movflags', '+faststart'])
        cmd.extend([output_path, '-y'])

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        try:
            result = subprocess.run(
                cmd, creationflags=creation_flags, capture_output=True, text=True,
                timeout=14400, cwd=os.path.dirname(ffmpeg_path) or None
            )
            if result.returncode != 0:
                return False
            if not os.path.isfile(output_path):
                return False
        except Exception:
            return False

        self._store_output(node, 'output', {"files": [output_path], "type": "container"})
        return True

    def _resolve_output_path(self, node):
        for n in self._nodes:
            if n.node_type() == 'output':
                op = n.params().get('output_path', '')
                template = n.params().get('filename_template', '{input_name}_encoded')
                if op:
                    return op
                elif template:
                    ext = '.mkv'
                    for p in node.input_ports():
                        data = self._get_input_for(node, p.port_name())
                        if data and data.get('files'):
                            src_first = os.path.basename(data['files'][0])
                            base = os.path.splitext(src_first)[0]
                            return os.path.join(self._temp_dir, template.replace('{input_name}', base) + ext)
        ext = '.mkv'
        return os.path.join(self._temp_dir, f"output_{uuid.uuid4().hex[:8]}{ext}")
