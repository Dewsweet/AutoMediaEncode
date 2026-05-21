import os, subprocess
from .._base import AMENodeBase, C, P, HIDDEN
from app.services.tool_service import ToolService


class SplitterNode(AMENodeBase):
    # ── SECTION 1: Metadata ──
    NODE_NAME       = '分离器'
    DESCRIPTION     = '用 ffmpeg -i 探测输入文件轨道，执行时按连接端口用 -map 分离'
    CATEGORY        = '处理'
    CATEGORY_COLOR  = C['处理']
    MENU_KEY        = 'splitter'

    # ── SECTION 2: Port I/O ──
    INPUTS  = [('input', P['any'])]
    OUTPUTS = [('video', P['video']), ('audio', P['audio']), ('subtitle', P['subtitle'])]

    # ── SECTION 3: __init__ — handled by AMENodeBase ──

    # ── SECTION 4: Inline Widgets ──
    def _setup_widgets(self):
        self.create_property('cached_tracks', [], widget_type=HIDDEN, tab='')

    # ── SECTION 5: Dynamic Ports — deferred ──

    # ── SECTION 6: Execute ──
    def execute(self, inputs: dict, temp_dir: str) -> dict | None:
        src_files = inputs.get('input', [])
        if not src_files:
            return None
        src = src_files[0]
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff:
            return None

        tracks = self._probe(ff, src)
        self.set_property('cached_tracks', tracks, push_undo=False)

        result = {}
        cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        for t in tracks:
            port_name = t['type']
            if port_name not in self.outputs():
                port_name = f"{t['type']}_{t['idx']}"
            if port_name not in self.outputs():
                continue
            port = self.outputs()[port_name]
            if not port.connected_ports():
                continue

            ext = _codec_ext(t['codec'])
            dst = os.path.join(temp_dir, f"track_{port_name}{ext}")
            cmd = [ff, '-i', src, '-map', f"0:{t['idx']}", '-c', 'copy', dst, '-y']
            try:
                r = subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=300)
                if r.returncode == 0 and os.path.isfile(dst) and os.path.getsize(dst) > 0:
                    result.setdefault(port_name, []).append(dst)
            except Exception:
                pass

        return result if result else None

    def _probe(self, ff: str, src: str) -> list:
        tracks = []
        try:
            cf = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            r = subprocess.run(
                [ff, '-i', src, '-hide_banner'],
                capture_output=True, text=True, creationflags=cf, timeout=60,
            )
            for ln in r.stderr.split('\n'):
                if not ln.strip().startswith('  Stream'):
                    continue
                part = ln.split('Stream #0:')[1]
                s = part.split('[')[0].split('(')[0].strip().split(':')[0]
                try:
                    idx = int(s)
                except ValueError:
                    continue
                if 'Video:' in ln:
                    codec = ln.split('Video:')[1].split()[0].split(',')[0]
                    tracks.append({'type': 'video', 'idx': idx, 'codec': codec})
                elif 'Audio:' in ln:
                    codec = ln.split('Audio:')[1].split()[0].split(',')[0]
                    tracks.append({'type': 'audio', 'idx': idx, 'codec': codec})
                elif 'Subtitle:' in ln:
                    codec = ln.split('Subtitle:')[1].split()[0].split(',')[0]
                    tracks.append({'type': 'subtitle', 'idx': idx, 'codec': codec})
        except Exception:
            pass
        return tracks


def _codec_ext(codec: str) -> str:
    c = codec.lower().replace('_', '')
    m = {
        'h264': '.h264', 'avc': '.h264', 'hevc': '.h265', 'h265': '.h265',
        'av1': '.ivf', 'vp9': '.ivf', 'aac': '.aac', 'flac': '.flac',
        'opus': '.opus', 'vorbis': '.ogg', 'pcm': '.wav', 'mp3': '.mp3',
        'ac3': '.ac3', 'eac3': '.eac3', 'dts': '.dts', 'ass': '.ass',
        'srt': '.srt', 'vtt': '.vtt',
    }
    for k, v in m.items():
        if k in c:
            return v
    return '.mkv'
