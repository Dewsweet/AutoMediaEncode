import subprocess
from pathlib import Path
from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import ActionButtonWidget
from app.services.tool_service import ToolService
from app.common.logger import logger


class SplitterNode(AMENodeBase):
    NODE_NAME = '分离器'
    DESCRIPTION = '默认 video_1 + audio_1。探测后按实际轨道动态追加 video_2/audio_2/subtitle_1 等'
    CATEGORY = '工具'; CATEGORY_COLOR = C['Orange']
    MENU_KEY = 'splitter'
    INPUTS  = [('input', P['any'])]
    OUTPUTS = [('video_1', P['video']), ('audio_1', P['audio'])]

    def _setup_widgets(self):
        self.add_custom_widget(ActionButtonWidget(self.view, 'probe_btn', '探测轨道', self._on_probe))
        self.create_property('cached_tracks', [], widget_type=HIDDEN, tab='')

    def _on_probe(self):
        """探测输入文件的轨道信息，动态调整输出端口"""
        in_port = self.inputs().get('input')
        if not in_port:
            return
        connected = in_port.connected_ports()
        if not connected:
            return
        src_node = connected[0].node()
        fp = src_node.property('input_file', '')
        if not fp or not Path(fp).is_file():
            fp = src_node.property('input_multi', '')
            if fp: fp = fp.split('\n')[0].strip()
            if not fp or not Path(fp).is_file():
                logger.warning(f'[Splitter] 上游节点没有有效文件路径')
                return

        ff = ToolService.get_tool_path('ffmpeg')
        if not ff: return

        tracks = self._probe(ff, fp)
        logger.info(f'[Splitter] 探测到 {len(tracks)} 条轨道: {[(t["type"], t["idx"]) for t in tracks]}')
        self.set_property('cached_tracks', tracks, push_undo=False)

        type_count = {}
        for t in tracks:
            tt = t['type']
            type_count[tt] = type_count.get(tt, 0) + 1

        for tt, count in type_count.items():
            for i in range(1, count + 1):
                pn = f"{tt}_{i}"
                if pn not in self.outputs():
                    self.add_output(pn, color=P.get(tt, P['any']))
                    logger.info(f'[Splitter] 追加端口: {pn}')

        self.view.draw_node()

    def execute(self, inputs: dict, temp_dir: str) -> dict | None:
        logger.info('\n' * 2 + '=' * 40 + ' [Splitter] ' + '=' * 40)
        src_files = inputs.get('input', [])
        if not src_files:
            return None
        src = src_files[0]
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff: return None

        tracks = self._probe(ff, src)
        logger.info(f'[Splitter] 执行探测: {len(tracks)} 条轨道')

        result = {}
        type_idx = {}
        for t in tracks:
            tt = t['type']
            ci = type_idx.get(tt, 0)
            type_idx[tt] = ci + 1
            pn = f"{tt}_{ci + 1}"
            port = self.outputs().get(pn)
            if not port or not port.connected_ports():
                continue

            ext = _codec_ext(t['codec'])
            dst = Path(temp_dir) / f"track_{pn}{ext}"
            codec_param = _resolve_codec(t['codec'], t.get('depth', ''))
            cmd = [ff, '-i', src, '-map', f"0:{t['idx']}", *codec_param, dst, '-y']
            logger.info(f'[Splitter] 提取: {" ".join(cmd)}')
            try:
                r = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, timeout=300)
                if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
                    result.setdefault(pn, []).append(dst)
                    logger.info(f'[Splitter] 提取成功: {dst}')
            except Exception as e:
                logger.error(f'[Splitter] 提取异常: {e}')

        return result if result else None

    def _probe(self, ff: str, src: str) -> list:
        tracks = []
        try:
            cmd = [ff, '-i', src, '-hide_banner']
            r = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
            for ln in r.stderr.split('\n'):
                if 'Stream #0:' not in ln:
                    continue
                try:
                    idx = int(ln.split('Stream #0:')[1].split('[')[0].split('(')[0].strip().split(':')[0])
                except (IndexError, ValueError):
                    continue
                if 'Video:' in ln:
                    codec = ln.split('Video:')[1].split()[0].split(',')[0]
                    tracks.append({'type': 'video', 'idx': idx, 'codec': codec})
                elif 'Audio:' in ln:
                    codec = ln.split('Audio:')[1].split()[0].split(',')[0]
                    depth = ''
                    if 'pcm_bluray' in codec:
                        if 's16' in ln: depth = 's16'
                        elif 's32' in ln: depth = 's32'
                        elif 's24' in ln: depth = 's24'
                    tracks.append({'type': 'audio', 'idx': idx, 'codec': codec, 'depth': depth})
                elif 'Subtitle:' in ln:
                    codec = ln.split('Subtitle:')[1].split()[0].split(',')[0]
                    tracks.append({'type': 'subtitle', 'idx': idx, 'codec': codec})
        except Exception as e:
            logger.error(f'[Splitter] 探测失败: {e}')
        return tracks


def _resolve_codec(codec: str, depth: str) -> list:
    c = codec.lower().replace('_', '')
    if 'pcm_bluray' in c or 'pcm' in c:
        if depth == 's32': return ['-c:a', 'pcm_s32le']
        elif depth == 's24': return ['-c:a', 'pcm_s24le']
        else: return ['-c:a', 'pcm_s16le']
    return ['-c', 'copy']


def _codec_ext(codec: str) -> str:
    c = codec.lower().replace('_', '')
    m = {'h264': '.h264', 'avc': '.h264', 'hevc': '.h265', 'h265': '.h265',
         'av1': '.ivf', 'vp9': '.ivf', 'aac': '.aac', 'flac': '.flac',
         'opus': '.opus', 'vorbis': '.ogg', 'pcm': '.wav', 'mp3': '.mp3',
         'ac3': '.ac3', 'eac3': '.eac3', 'dts': '.dts', 'ass': '.ass',
         'srt': '.srt', 'vtt': '.vtt'}
    for k, v in m.items():
        if k in c: return v
    return '.mkv'
