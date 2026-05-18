import os
import uuid
import re
import subprocess

from PySide6.QtCore import QThread, Signal

from .workflow_validator import WorkflowValidator
from app.services.tool_service import ToolService
from app.services.error_service import ErrorService
from app.common.logger import logger


class AMEWorkflowExecutor(QThread):
    progress_updated = Signal(int)
    node_status_changed = Signal(str, str)
    node_progress_updated = Signal(str, float)
    error_occurred = Signal(str)

    def __init__(self, nodes: list, edges: list, parent=None):
        super().__init__(parent)
        self._nodes = list(nodes)
        self._edges = list(edges)
        self._cancelled = False
        self._node_map = {n.id: n for n in self._nodes}
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
        for fn, fp, tid, tp in self._edges:
            connected_ids.add(fn.id)
            connected_ids.add(tid)
        execution_order = [n for n in execution_order if n.id in connected_ids]
        if not execution_order:
            execution_order = [n for n in self._nodes if 'OutputNode' in n.type_]
        total = len(execution_order) if execution_order else 1

        self._resolve_temp_dir()

        for i, node in enumerate(execution_order):
            if self._cancelled:
                return
            self.node_status_changed.emit(node.id, "running")
            self._collect_inputs(node)
            success = self._execute_node(node)
            if self._cancelled:
                return
            self.node_progress_updated.emit(node.id, 100.0)
            if success:
                self.node_status_changed.emit(node.id, "done")
            else:
                self.node_status_changed.emit(node.id, "error")
                self.error_occurred.emit(f"节点 {node.name()} 执行失败")
                return
            self.progress_updated.emit(int((i + 1) / total * 100))

    def _prop(self, node, key, default=None):
        try:
            v = node.get_property(key)
            return v if v is not None else default
        except Exception:
            return default

    def _resolve_temp_dir(self):
        for node in self._nodes:
            if 'WorkspaceNode' in node.type_:
                wd = self._prop(node, 'work_dir', '')
                if wd and os.path.isdir(wd):
                    self._temp_dir = os.path.join(wd, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return
        for node in self._nodes:
            if 'OutputNode' in node.type_:
                op = self._prop(node, 'output_path', '')
                if op:
                    out_dir = os.path.dirname(op) or os.path.abspath('.')
                    self._temp_dir = os.path.join(out_dir, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return
        for node in self._nodes:
            if 'Input' in node.type_:
                fp = self._prop(node, 'file_path', '')
                if fp and os.path.isfile(fp):
                    src_dir = os.path.dirname(fp) or os.path.abspath('.')
                    self._temp_dir = os.path.join(src_dir, 'temp')
                    os.makedirs(self._temp_dir, exist_ok=True)
                    return
        self._temp_dir = os.path.join(os.path.abspath('.'), 'temp')
        os.makedirs(self._temp_dir, exist_ok=True)

    def _collect_inputs(self, node):
        for fn, fp, tid, tp in self._edges:
            if tid == node.id:
                src_key = (fn.id, fp)
                tgt_key = (node.id, tp)
                if src_key in self._output_data:
                    self._output_data[tgt_key] = self._output_data[src_key]

    def _store_output(self, node, port_name, data):
        self._output_data[(node.id, port_name)] = data

    def _get_input_for(self, node, port_name):
        return self._output_data.get((node.id, port_name))

    def _execute_node(self, node):
        tn = node.type_
        try:
            if 'Workspace' in tn:
                return True
            elif 'Input' in tn:
                return self._do_input(node)
            elif 'Splitter' in tn:
                return self._do_splitter(node)
            elif 'VPYLoader' in tn:
                return self._do_vpy_loader(node)
            elif 'VSPipe' in tn:
                return self._do_vspipe(node)
            elif 'FFmpegProcessor' in tn:
                return self._do_ffmpeg_processor(node)
            elif 'EncoderX' in tn or 'EncoderSvt' in tn:
                return self._do_cli_encoder(node)
            elif 'EncoderFFmpegVideo' in tn:
                return self._do_ffmpeg_video(node)
            elif 'EncoderFFmpegAudio' in tn or 'EncoderAAC' in tn or 'EncoderFlac' in tn or 'EncoderOpus' in tn:
                return self._do_ffmpeg_audio(node)
            elif 'MuxerMkvmerge' in tn:
                return self._do_muxer_mkvmerge(node)
            elif 'MuxerFFmpeg' in tn:
                return self._do_muxer_ffmpeg(node)
            elif 'Output' in tn:
                return True
            return True
        except Exception:
            import traceback
            logger.error(f"Node {node.name()} failed: {traceback.format_exc()}")
            return False

    def _do_input(self, node):
        fp = self._prop(node, 'file_path', '')
        if not fp or not os.path.isfile(fp):
            return False
        ext = os.path.splitext(fp)[1].lower()
        video_exts = {'.mkv','.mp4','.m2ts','.ts','.mts','.avi','.mov','.wmv','.flv','.webm','.h264','.h265','.ivf','.vc1'}
        audio_exts = {'.aac','.flac','.wav','.opus','.mp3','.ac3','.dts','.eac3','.ogg','.thd','.mka'}
        sub_exts = {'.ass','.srt','.vtt','.lrc','.ssa'}
        chap_exts = {'.xml','.txt','.cue'}
        if ext in video_exts:
            self._store_output(node, 'video', {"files":[fp],"type":"video"})
        if ext in audio_exts:
            self._store_output(node, 'audio', {"files":[fp],"type":"audio"})
        if ext in sub_exts:
            self._store_output(node, 'subtitle', {"files":[fp],"type":"subtitle"})
        if ext in chap_exts:
            self._store_output(node, 'chapter', {"files":[fp],"type":"chapter"})
        return True

    def _do_splitter(self, node):
        inp = self._get_input_for(node, 'input')
        if not inp:
            return False
        files = inp.get('files', [])
        if not files:
            return False
        src = files[0]
        mode = self._prop(node, 'mode', 'extract')
        tool_path = ToolService.get_tool_path('ffmpeg')
        if mode == 'refer':
            self._store_output(node, 'video', {"files":[src],"type":"video","mode":"refer"})
            self._store_output(node, 'audio', {"files":[src],"type":"audio","mode":"refer"})
            self._store_output(node, 'subtitle', {"files":[src],"type":"subtitle","mode":"refer"})
            return True
        if not tool_path:
            return False
        video_idx, audio_idx, sub_idx = self._probe_tracks(tool_path, src)
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        ev, ea, es = [], [], []
        for idx, c in video_idx:
            d = os.path.join(self._temp_dir, f"track_video_{idx}{self._codec_to_ext(c)}")
            subprocess.run([tool_path,'-i',src,'-map',f'0:{idx}','-c','copy',d,'-y'], creationflags=cf, capture_output=True, timeout=300)
            if os.path.isfile(d): ev.append(d)
        for idx, c in audio_idx:
            d = os.path.join(self._temp_dir, f"track_audio_{idx}{self._codec_to_ext(c)}")
            subprocess.run([tool_path,'-i',src,'-map',f'0:{idx}','-c','copy',d,'-y'], creationflags=cf, capture_output=True, timeout=300)
            if os.path.isfile(d): ea.append(d)
        for idx, c in sub_idx:
            d = os.path.join(self._temp_dir, f"track_subtitle_{idx}{self._codec_to_ext(c)}")
            subprocess.run([tool_path,'-i',src,'-map',f'0:{idx}','-c','copy',d,'-y'], creationflags=cf, capture_output=True, timeout=300)
            if os.path.isfile(d): es.append(d)
        if ev: self._store_output(node, 'video', {"files":ev,"type":"video"})
        if ea: self._store_output(node, 'audio', {"files":ea,"type":"audio"})
        if es: self._store_output(node, 'subtitle', {"files":es,"type":"subtitle"})
        return True

    def _do_vpy_loader(self, node):
        vpy = self._prop(node, 'vpy_path', '')
        if not vpy or not os.path.isfile(vpy):
            return False
        inp = self._get_input_for(node, 'input')
        src = inp.get('files',[''])[0] if inp else ''
        self._store_output(node, 'script', {"files":[vpy],"type":"script","source":src})
        return True

    def _do_vspipe(self, node):
        inp = self._get_input_for(node, 'script')
        if not inp:
            return False
        files = inp.get('files', [])
        if not files:
            return False
        self._store_output(node, 'video', {"files":files,"type":"video","from_vspipe":True})
        return True

    def _do_ffmpeg_processor(self, node):
        inp = self._get_input_for(node, 'input')
        if not inp:
            return False
        files = inp.get('files', [])
        if not files:
            return False
        src = files[0]
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path:
            return False
        cli = self._prop(node, 'cli_args', '')
        import shlex
        try:
            extra = shlex.split(cli) if cli else []
        except ValueError:
            extra = cli.split() if cli else []
        dst = os.path.join(self._temp_dir, f"processed_{node.id}.mkv")
        cmd = [ffmpeg_path, '-i', src] + extra + [dst, '-y']
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        result = subprocess.run(cmd, creationflags=cf, capture_output=True, text=True, timeout=3600)
        if result.returncode != 0 or not os.path.isfile(dst):
            return False
        self._store_output(node, 'output', {"files":[dst],"type":"any"})
        return True

    def _probe_tracks(self, ffmpeg_path, src):
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        video, audio, sub = [], [], []
        try:
            result = subprocess.run([ffmpeg_path, '-i', src, '-hide_banner'],
                                    capture_output=True, text=True, creationflags=cf, timeout=60)
            for line in result.stderr.split('\n'):
                if not line.strip().startswith('  Stream'):
                    continue
                sidx = line.split('Stream #0:')[1].split('[')[0].split('(')[0].strip().split(':')[0]
                try: idx = int(sidx)
                except ValueError: continue
                if 'Video:' in line:
                    video.append((idx, line.split('Video:')[1].split()[0].split(',')[0]))
                elif 'Audio:' in line:
                    audio.append((idx, line.split('Audio:')[1].split()[0].split(',')[0]))
                elif 'Subtitle:' in line:
                    sub.append((idx, line.split('Subtitle:')[1].split()[0].split(',')[0]))
        except Exception:
            pass
        return video, audio, sub

    def _codec_to_ext(self, codec):
        codec = codec.lower().replace('_', '')
        m = {'h264':'.h264','avc':'.h264','hevc':'.h265','h265':'.h265','av1':'.ivf','vp9':'.ivf','vp8':'.ivf',
             'aac':'.aac','flac':'.flac','opus':'.opus','vorbis':'.ogg','pcm':'.wav','mp3':'.mp3',
             'ac3':'.ac3','eac3':'.eac3','dts':'.dts','ass':'.ass','srt':'.srt','vtt':'.vtt',
             'subrip':'.srt','webvtt':'.vtt'}
        for k, v in m.items():
            if k in codec: return v
        return '.mkv'

    def _do_cli_encoder(self, node):
        inp = self._get_input_for(node, 'input')
        if not inp: return False
        files = inp.get('files', [])
        if not files: return False
        src = files[0]
        tn = node.type_
        ext_map = {'EncoderX264':'h264','EncoderX265':'h265','EncoderSvt':'svtav1'}
        ext = next((v for k,v in ext_map.items() if k in tn), 'h264')
        ext_str = {'h264': '.h264', 'h265': '.h265', 'svtav1': '.ivf'}.get(ext, '.h264')
        tool_key_map = {'h264':'x264','h265':'x265','svtav1':'SvtAv1'}
        tool_key = tool_key_map.get(ext, 'x264')
        dst = os.path.join(self._temp_dir, f"encoded_{node.id}{ext_str}")
        cli_path = ToolService.get_tool_path(tool_key)
        if not cli_path or not os.path.isfile(cli_path):
            logger.warning(f"CLI tool {tool_key} not found")
            return False

        use_preset = self._prop(node, 'use_preset', True)
        preset_name = self._prop(node, 'preset', '') if use_preset else ''
        custom_cli = self._prop(node, 'custom_cli', '')

        if preset_name:
            from app.services.setting.preset_service import preset_service
            enc_key = {'h264':'x264','h265':'x265','svtav1':'SVTAV1'}.get(ext, 'x264')
            presets = preset_service.get_presets_by_encoder(enc_key)
            cli_args = presets.get(preset_name, preset_name) if presets else preset_name
        elif custom_cli:
            cli_args = custom_cli
        else:
            cli_args = ''

        import shlex
        try:
            args_list = shlex.split(cli_args) if cli_args else []
        except ValueError:
            args_list = cli_args.split() if cli_args else []

        cmd = [cli_path, '--output', dst] if tool_key == 'SvtAv1' else [cli_path, '-o', dst]
        cmd.extend(args_list)
        cmd.append(src)
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            self._run_cli_with_progress(node, cmd, cf)
            if not os.path.isfile(dst) or os.path.getsize(dst) == 0:
                return False
        except (subprocess.TimeoutExpired, Exception):
            return False
        self._store_output(node, 'video', {"files":[dst],"type":"video"})
        return True

    def _run_cli_with_progress(self, node, cmd, cf):
        p = subprocess.Popen(cmd, creationflags=cf, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in p.stdout:
            if self._cancelled:
                p.terminate()
                return
            m = re.search(r'(\d+)/(\d+)', line)
            if m:
                cur = int(m.group(1)); total = int(m.group(2))
                if total > 0:
                    self.node_progress_updated.emit(node.id, cur / total * 100.0)
        p.wait()

    def _do_ffmpeg_video(self, node):
        inp = self._get_input_for(node, 'input')
        if not inp: return False
        files = inp.get('files', [])
        if not files: return False
        src = files[0]
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path: return False
        codec = self._prop(node, 'codec', 'libx264')
        ext = '.h264' if 'x264' in codec else '.h265' if 'x265' in codec or 'hevc' in codec else '.mkv'
        dst = os.path.join(self._temp_dir, f"encoded_video_{node.id}{ext}")
        cmd = [ffmpeg_path, '-i', src, '-c:v', codec]
        rc = self._prop(node, 'rc_mode', 'crf')
        if rc == 'crf': cmd.extend(['-crf', str(self._prop(node, 'quality_val', 23))])
        elif rc == 'abr': cmd.extend(['-b:v', self._prop(node, 'bitrate', '5000k')])
        elif rc == 'cqp': cmd.extend(['-qp', str(self._prop(node, 'quality_val', 23))])
        preset = self._prop(node, 'preset', '')
        if preset: cmd.extend(['-preset', preset])
        custom = self._prop(node, 'custom_options', '')
        if custom:
            import shlex
            try: cmd.extend(shlex.split(custom))
            except ValueError: cmd.extend(custom.split())
        cmd.extend(['-an', dst, '-y'])
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            self._run_ffmpeg_with_progress(node, cmd, cf)
            if not os.path.isfile(dst): return False
        except Exception: return False
        self._store_output(node, 'video', {"files":[dst],"type":"video"})
        return True

    def _do_ffmpeg_audio(self, node):
        inp = self._get_input_for(node, 'input')
        if not inp: return False
        files = inp.get('files', [])
        if not files: return False
        src = files[0]
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path: return False
        codec = self._prop(node, 'codec', 'aac')
        em = {'aac':'.aac','libmp3lame':'.mp3','flac':'.flac','opus':'.opus','libvorbis':'.ogg','ac3':'.ac3'}
        ext = em.get(codec, '.m4a')
        dst = os.path.join(self._temp_dir, f"encoded_audio_{node.id}{ext}")
        cmd = [ffmpeg_path, '-i', src, '-c:a', codec]
        rc = self._prop(node, 'rc_mode', 'cbr')
        bitrate = self._prop(node, 'bitrate', '')
        if rc in ('cbr','abr') and bitrate: cmd.extend(['-b:a', bitrate])
        elif rc == 'quality': cmd.extend(['-q:a', str(self._prop(node, 'quality_val', 5))])
        custom = self._prop(node, 'custom_options', '')
        if custom:
            import shlex
            try: cmd.extend(shlex.split(custom))
            except ValueError: cmd.extend(custom.split())
        cmd.extend(['-vn', dst, '-y'])
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            self._run_ffmpeg_with_progress(node, cmd, cf)
            if not os.path.isfile(dst): return False
        except Exception: return False
        self._store_output(node, 'audio', {"files":[dst],"type":"audio"})
        return True

    def _run_ffmpeg_with_progress(self, node, cmd, cf):
        try:
            from ffmpeg_progress_yield import FfmpegProgress
            ff = FfmpegProgress(cmd)
            for progress in ff.run_command_with_progress(creationflags=cf, stdin=subprocess.DEVNULL):
                if self._cancelled: return
                pct = float(progress) if progress else 0
                self.node_progress_updated.emit(node.id, pct)
        except ImportError:
            subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=14400)

    def _do_muxer_mkvmerge(self, node):
        mkvmerge_path = ToolService.get_tool_path('mkvmerge')
        if not mkvmerge_path: return False
        video_files = []; audio_files = []; sub_files = []; attach_files = []
        for pname in node.inputs():
            data = self._get_input_for(node, pname)
            if not data: continue
            flist = data.get('files', [])
            if pname.startswith('video'): video_files.extend(flist)
            elif pname.startswith('audio'): audio_files.extend(flist)
            elif pname.startswith('subtitle'): sub_files.extend(flist)
            elif pname.startswith('attachment'): attach_files.extend(flist)
        output_path = self._resolve_output_path(node)
        if not output_path: return False
        cmd = [mkvmerge_path, '-o', output_path]
        for f in video_files: cmd.extend(['-d', '0', f])
        for f in audio_files: cmd.extend(['-a', '0', f])
        for f in sub_files: cmd.extend(['-s', '0', f])
        for f in attach_files: cmd.extend(['--attach-file', f])
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            result = subprocess.run(cmd, creationflags=cf, capture_output=True, text=True, timeout=14400)
            if result.returncode not in (0, 1) or not os.path.isfile(output_path): return False
        except Exception: return False
        self._store_output(node, 'output', {"files":[output_path],"type":"container"})
        return True

    def _do_muxer_ffmpeg(self, node):
        ffmpeg_path = ToolService.get_tool_path('ffmpeg')
        if not ffmpeg_path: return False
        vi = self._get_input_for(node, 'video'); ai = self._get_input_for(node, 'audio')
        vf = vi.get('files', []) if vi else []; af = ai.get('files', []) if ai else []
        output_path = self._resolve_output_path(node)
        if not output_path:
            container = self._prop(node, 'container', 'mp4')
            ext = '.mp4' if container == 'mp4' else '.mov'
            output_path = os.path.join(self._temp_dir, f"muxed_{node.id}{ext}")
        cmd = [ffmpeg_path]
        for s in vf: cmd.extend(['-i', s])
        for s in af: cmd.extend(['-i', s])
        si = 0
        for _ in vf: cmd.extend(['-map', str(si)]); si += 1
        for _ in af: cmd.extend(['-map', str(si)]); si += 1
        cmd.extend(['-c', 'copy', output_path, '-y'])
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            self._run_ffmpeg_with_progress(node, cmd, cf)
            if not os.path.isfile(output_path): return False
        except Exception: return False
        self._store_output(node, 'output', {"files":[output_path],"type":"container"})
        return True

    def _resolve_output_path(self, node):
        for n in self._nodes:
            if 'OutputNode' in n.type_:
                op = self._prop(n, 'output_path', '')
                if op: return op
        ext = '.mkv'
        return os.path.join(self._temp_dir, f"output_{uuid.uuid4().hex[:8]}{ext}")
