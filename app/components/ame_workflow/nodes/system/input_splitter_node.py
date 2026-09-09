"""视频规范化输入节点:
- 仅允许输入视频文件
- 默认无输出端口
- 选择输入文件后自动 ffmpeg 探测轨道，动态追加 video_N/audio_N/subtitle_N 输出端口
- 探测结果随工作流保存，重新打开时直接用缓存重建端口（不重跑 ffmpeg）
"""
import subprocess
from pathlib import Path

from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FileBrowseWidget
from app.services.tool_service import ToolService
from app.services.error_service import ErrorService
from app.common.logger import logger
from app.common.media_utils import VIDEO_EXTS


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


class InputVideoNormalizerNode(AMENodeBase):
    """选择文件后自动探测轨道并生成输出端口的输入源节点"""

    NODE_NAME = '视频规范化输入'
    DESCRIPTION = '选择文件后自动探测轨道并生成输出端口'
    CATEGORY = '输入'; CATEGORY_COLOR = C['Gray']
    MENU_KEY = 'input_video_normalizer'
    INPUTS  = [('path', P['any'])]
    OUTPUTS = []

    def _setup_widgets(self):
        self._last_probed = ''
        self.set_port_deletion_allowed(True)

        # 缓存属性必须先于文件 widget 注册：加载工作流时 custom properties
        # 按 JSON 键序恢复，input_file widget 恢复(set_value)触发本节点回调时
        # 即可直接读到 tracks 缓存重建端口，无需重跑 ffmpeg
        self.create_property('tracks_src', '', widget_type=HIDDEN, tab='')
        self.create_property('tracks', [], widget_type=HIDDEN, tab='')

        EXT = "视频文件 (" + ' '.join(f'*{e}' for e in VIDEO_EXTS) + ');;'
        w = FileBrowseWidget(self.view, 'input_file', '选择输入文件', exts=EXT)
        self.add_custom_widget(w)
        # add_custom_widget 已将 value_changed 接到 set_property，这里额外挂自动探测回调
        w.value_changed.connect(lambda k, v: self._on_file_changed(v))

    def _on_file_changed(self, fp):
        fp = str(fp or '').strip()
        if not fp or fp == self._last_probed:
            # 直接返回: 空路径或与上次探测一致
            return
        if not Path(fp).is_file():
            logger.warning(f'[InputVideoNormalizerNode] 无效文件路径, 跳过探测: {fp}')
            return
        self._last_probed = fp

        # 恢复路径: 缓存与当前文件一致时直接重建端口, 不重跑 ffmpeg
        if fp == self.property('tracks_src', '') and self.property('tracks'):
            self._rebuild_ports(self.property('tracks'))
            return

        ff = ToolService.get_tool_path('ffmpeg')
        if not ff:
            logger.warning('[InputVideoNormalizerNode] 找不到 ffmpeg, 跳过轨道探测')
            return
        tracks = self._probe_streams(ff, fp)
        if not tracks:
            logger.warning(f'[InputVideoNormalizerNode] 未探测到任何轨道: {fp}')
            return
        self.set_property('tracks_src', fp, push_undo=False)
        self.set_property('tracks', tracks, push_undo=False)
        logger.info(f'[InputVideoNormalizerNode] 探测到 {len(tracks)} 条轨道: '
                    f'{[(t["type"], t["idx"]) for t in tracks]}')
        self._rebuild_ports(tracks)

    # 动态端口重建: 同名保留/多余删除/缺失追加 
    def _rebuild_ports(self, tracks):
        names = self._port_names(tracks)
        keep = {n for n, _ in names}
        for pn in list(self.outputs().keys()):
            if pn in keep:
                continue
            try:
                port = self.outputs().get(pn)
                for cp in list(port.connected_ports()):
                    try:
                        port.disconnect_from(cp)
                    except Exception:
                        pass
                self.delete_output(pn)
                logger.info(f'[InputVideoNormalizerNode] 移除多余端口: {pn}')
            except Exception as e:
                logger.warning(f'[InputVideoNormalizerNode] 移除端口失败: {pn}, {e}')
        for pn, tt in names:
            if pn in self.outputs():
                continue
            self.add_output(pn, color=P.get(tt, P['any']))
            logger.info(f'[InputVideoNormalizerNode] 追加端口: {pn}')
        self.view.draw_node()

    @staticmethod
    def _port_names(tracks) -> list:
        """按轨道类型出现顺序分组计数 → [(video_1, video), (audio_1, audio), ...]"""
        type_count = {}
        for t in tracks:
            tt = t.get('type', '')
            if tt:
                type_count[tt] = type_count.get(tt, 0) + 1
        return [(f"{tt}_{i}", tt) for tt, count in type_count.items()
                for i in range(1, count + 1)]

    def _probe_streams(self, ff: str, src: str) -> list:
        """ffmpeg -i 解析 stderr, 提取轨道 type/idx/codec/depth"""
        tracks = []
        try:
            cmd = [ff, '-i', src, '-hide_banner']
            r = subprocess.run(cmd, capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=60)
            if not r.stderr:
                return tracks
            stderr_text = r.stderr.decode('utf-8', errors='replace')
            for ln in stderr_text.split('\n'):
                if 'Stream #0:' not in ln:
                    continue
                try:
                    idx = int(ln.split('Stream #0:')[1].split('[')[0].split('(')[0].strip().split(':')[0])
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
                except (IndexError, ValueError):
                    continue
        except Exception as e:
            logger.error(f'[InputVideoNormalizerNode] 探测失败: {e}')
        return tracks

    def execute(self, inputs: dict, temp_dir: str) -> dict | None:
        logger.info('\n' * 2 + '=' * 40 + ' [InputVideoNormalizerNode] ' + '=' * 40)
        src = str(self.property('input_file', '') or '').strip()
        if not src or not Path(src).is_file():
            self._last_error = '输入分离器未设置有效的输入文件'
            return None
        ff = ToolService.get_tool_path('ffmpeg')
        if not ff:
            self._last_error = '分离器找不到 ffmpeg，请检查工具路径'
            return None

        # 优先使用与当前文件一致的探测缓存, 否则现探测(不写回属性, execute 运行于子线程)
        tracks = []
        if self.property('tracks_src', '') == src:
            tracks = self.property('tracks') or []
        if not tracks:
            tracks = self._probe_streams(ff, src)
        if not tracks:
            self._last_error = f'未能从文件探测到轨道: {src}'
            return None
        logger.info(f'[InputVideoNormalizerNode] 共 {len(tracks)} 条轨道: '
                    f'{[(t["type"], t["idx"]) for t in tracks]}')

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
            logger.info(f'[InputVideoNormalizerNode] 提取: {" ".join(str(c) for c in cmd)}')
            try:
                r = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW,
                                   capture_output=True, timeout=300)
                if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
                    result.setdefault(pn, []).append(dst)
                    logger.info(f'[InputVideoNormalizerNode] 提取成功: {dst}')
                else:
                    logger.warning(f'[InputVideoNormalizerNode] 提取失败: {pn}, returncode={r.returncode}')
            except Exception as e:
                logger.error(f'[InputVideoNormalizerNode] 提取异常: {e}')

        if not result:
            self._last_error = ErrorService.cli_error('ffmpeg', '未能提取任何已连接的轨道')
        return result if result else None
