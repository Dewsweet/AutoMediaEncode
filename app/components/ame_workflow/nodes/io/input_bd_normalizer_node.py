"""BD 规范化输入节点 — Blu-ray 原盘 (.m2ts/.mpls) 输入与轨道规范化。

- 选择输入文件后自动用 eac3to 探测轨道，动态追加 video_N/audio_N/subtitle_N/chapter_N 输出端口
- m2ts 输入：单流无裁剪概念，始终走 eac3to（m2ts 无章节属正常现象）
- 连体盘识别：mpls 引用的 m2ts 总时长 > playlist 报告时长（容差 2s）⇒ playlist 含 IN/OUT
  时间裁剪（连体盘子分集），eac3to 会忽略裁剪输出完整拼接流 ⇒ 整节点切换 mkvmerge
  （mkvmerge v14+ 读取 playlist 时遵循 IN/OUT 时间戳，可正确输出裁剪段拼接）
- 三层切换时机：探测预判(时长对比) → 扫描回退(eac3to 失败用 mkvmerge -J) → 运行时兜底(单轨提取失败重试)
- 探测结果与 backend 随工作流保存，重新打开时用缓存重建端口（不重跑 eac3to）
"""
import json
import re
import subprocess
from pathlib import Path
from typing import Text

from PySide6.QtCore import QThread, Signal
from pymediainfo import MediaInfo

from .._base import AMENodeBase, C, P, HIDDEN
from .._widgets import FileBrowseWidget, NodeTextComboBoxWidget
from app.services.tool_service import ToolService
from app.services.error_service import ErrorService
from app.common.logger import logger

# 连体盘判定容差(秒): m2ts 总时长 - playlist 时长 > 容差 ⇒ 存在 IN/OUT 裁剪
INTERLEAVED_TOLERANCE_S = 2.0
BD_INPUT_EXTS = ('.m2ts', '.mts', '.mpls')
MKVMERGE_EXTS = {'video': '.mkv', 'audio': '.mka', 'subtitle': '.mks'}


def _eac3to_ext(track: dict) -> str:
    """按轨道编码选择 eac3to 原生输出扩展名(裸流=纯 demux 无转码), 未识别兜底 .mkv 容器。

    匹配顺序关键: truehd 先于 ac3('TrueHD/AC3' 含 ac3 子串), e-ac3 先于 ac3,
    dts-hd 家族先于 dts; 匹配前去除空格与下划线。
    """
    if track.get('type', '') == 'chapter':
        return '.txt'
    c = track.get('codec', '').lower().replace('_', '').replace(' ', '')
    if 'truehd' in c: return '.thd'       # TrueHD/AC3 → .thd (TrueHD 原生, 内含 AC3 core)
    if 'e-ac3' in c or 'eac3' in c: return '.eac3'
    if 'dtshd' in c or 'masteraudio' in c or 'dtsexpress' in c: return '.dtshd'
    if 'dts' in c: return '.dts'
    if 'ac3' in c: return '.ac3'
    if 'pcm' in c: return '.w64'
    if 'h264' in c or 'avc' in c: return '.h264'
    if 'h265' in c or 'hevc' in c: return '.hevc'
    if 'vc-1' in c or 'vc1' in c: return '.vc1'
    if 'mpeg2' in c or 'mpeg-2' in c: return '.m2v'
    if 'subtitle' in c or 'pgs' in c: return '.sup'
    return '.mkv'

def _parse_ts(text: str) -> float:
    """ HH:MM:SS to seconds """
    m = re.search(r'(\d{1,3}):(\d{2}):(\d{2})', text)
    if not m:
        return 0.0
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))


def _expand_m2ts(field: str) -> list:
    """展开 playlist 头行/段列表行中的 m2ts 段名 → ['00401.m2ts', '00402.m2ts']"""
    f = field.strip()
    m = re.fullmatch(r'\[([0-9+]+)\]\s*\.m2ts', f)
    if m:  # 括号格式: [401+402+403].m2ts
        return [n.zfill(5) + '.m2ts' for n in m.group(1).split('+')]
    segs = []
    for part in f.split('+'):  # 直接格式: 00002.m2ts+00006.m2ts / 00600.m2ts
        m2 = re.fullmatch(r'([0-9]{3,5})\s*\.m2ts', part.strip())
        if m2:
            segs.append(m2.group(1).zfill(5) + '.m2ts')
    return segs


def _extract_lang(desc: str) -> str:
    """轨道描述中的语言: 优先 [eng] 形式, 其次常见英文语言词"""
    m = re.search(r'\[([a-z]{2,3})\]', desc)
    if m:
        return f'[{m.group(1)}]'
    for w in ('English', 'Japanese', 'French', 'German', 'Spanish', 'Italian',
              'Chinese', 'Mandarin', 'Cantonese', 'Korean', 'Thai', 'Portuguese',
              'Russian', 'Dutch', 'Polish', 'Swedish', 'Danish', 'Norwegian',
              'Finnish', 'Hindi', 'Arabic', 'Turkish'):
        if re.search(rf'\b{w}\b', desc, re.IGNORECASE):
            return w
    return ''


def _make_track(idx: int, desc: str) -> dict | None:
    """eac3to 轨道描述行 → Track 字典; 无法识别的类型返回 None"""
    d = desc.strip()
    codec = d.split(',')[0].strip()
    c = codec.lower()
    low = d.lower()
    if c.startswith('chapters'):
        m = re.search(r'(\d+)\s+chapters', low)
        return {'type': 'chapter', 'idx': idx, 'codec': f'{m.group(1)} chapters' if m else 'chapters', 'lang': ''}
    if c.startswith('subtitle'):
        return {'type': 'subtitle', 'idx': idx, 'codec': codec, 'lang': _extract_lang(d)}
    if ('h264/avc' in c or 'h265/hevc' in c or c.startswith('mpeg2')
            or c.startswith('mpeg-2') or 'vc-1' in c):
        return {'type': 'video', 'idx': idx, 'codec': codec, 'lang': _extract_lang(d)}
    if ('channels' in low or any(k in c for k in ('dts', 'truehd', 'ac3', 'pcm', 'lpcm', 'mpeg audio'))):
        return {'type': 'audio', 'idx': idx, 'codec': codec, 'lang': _extract_lang(d)}
    return None


def _parse_eac3to_scan(text: str, is_mpls: bool) -> tuple:
    """解析 eac3to 扫描输出 → (tracks, m2ts段列表, playlist时长秒)

    兼容两种行格式:
    - m2ts 模式: 'M2TS, ...' 汇总行 + 'N: <描述>' 编号行
    - mpls 模式: 'N) <mpls>, <m2ts列表>, <时长>' 头行 + '   - <描述>' 缩进行(行序即编号)
    """
    tracks: list = []
    segments: list = []
    dur_s = 0.0
    auto_idx = 0
    for raw in text.split('\n'):
        raw = _ANSI_RE.sub('', raw)
        raw = _CTRL_RE.sub('', raw)
        s = raw.strip()
        if not s:
            continue
        if s.startswith('('):  # (core: ...)/(embedded: ...) 折行续行
            continue
        m = re.match(r'^(\d+)\)\s*(.+)$', s)  # playlist 头行
        if m:
            tracks.clear()  # 单文件输入只有一块, 防御性取最后一块
            segments.clear()
            auto_idx = 0
            for field in m.group(2).split(','):
                field = field.strip()
                if re.fullmatch(r'\d{1,3}:\d{2}:\d{2}', field):
                    dur_s = _parse_ts(field)
                else:
                    segments.extend(_expand_m2ts(field))
            continue
        if re.fullmatch(r'\[[0-9+]+\]\s*\.m2ts', s):  # 独立段列表行(肉酱盘)
            segments.extend(_expand_m2ts(s))
            continue
        m = re.match(r'^(\d+):\s*(.+)$', s)  # m2ts 模式编号行
        if m:
            t = _make_track(int(m.group(1)), m.group(2))
            if t:
                tracks.append(t)
            continue
        m = re.match(r'^-\s+(.+)$', s)  # 缩进行(mpls 模式; m2ts 输出无此行, 不设门禁防后缀误判)
        if m:
            auto_idx += 1
            t = _make_track(auto_idx, m.group(1))
            if t:
                tracks.append(t)
    return tracks, segments, dur_s


# eac3to 管道输出可能包含 ANSI 转义序列(\x1b[2K 擦除等)与控制字符(如 NUL),
# 肉眼/日志不可见但会破坏行首正则匹配导致 0 轨道, 解析前必须剥离
_ANSI_RE = re.compile(r'\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[=>]')
_CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def _ogm_from_json_chapters(chapters: list) -> str:
    """mkvmerge -J 的 chapters JSON → OGM 章节 txt 内容"""
    lines = []
    for i, ch in enumerate(chapters, 1):
        start = str(ch.get('start', '00:00:00.000'))[:12]  # 'HH:MM:SS.mmm'
        lines.append(f'CHAPTER{i:02d}={start}')
        lines.append(f'CHAPTER{i:02d}NAME=')
    return '\n'.join(lines)


class _ProbeThread(QThread):
    """后台探测线程: eac3to/mkvmerge 扫描与 MediaInfo 解析均为外部调用,
    移出 UI 线程避免探测期间界面卡顿; 结果经信号回主线程处理。"""

    probe_done = Signal(int, str, list, str)  # seq, src, tracks, backend

    def __init__(self, node, src: str, seq: int):
        super().__init__()
        self._node = node
        self._src = src
        self._seq = seq

    def run(self):
        try:
            # _resolve_tracks 仅做子进程调用与 pymediainfo 解析, 无 UI 操作
            tracks, backend = self._node._resolve_tracks(self._src)
        except Exception as e:
            logger.error(f'[InputBD] 后台探测异常: {e}')
            tracks, backend = None, None
        self.probe_done.emit(self._seq, self._src, tracks or [], backend or '')


class InputBDNormalizerNode(AMENodeBase):
    """选择 m2ts/mpls 后自动 eac3to 探测轨道并生成输出端口的 BD 输入节点"""

    NODE_NAME = 'BD 规范化输入'
    DESCRIPTION = 'm2ts/mpls 输入, eac3to 探测轨道; 连体盘自动切换 mkvmerge'
    CATEGORY = '输入'; CATEGORY_COLOR = C['Gray']
    MENU_KEY = 'input_bd_normalizer'
    INPUTS  = [('workspace', P['any'])]
    OUTPUTS = []

    def _setup_widgets(self):
        self._last_probed = ''
        self._probe_seq = 0       # 探测请求序号(防竞态: 过期结果丢弃)
        self._probe_threads = []  # 持引用防 QThread 运行中被 GC
        self.set_port_deletion_allowed(True)

        # 缓存属性必须先于文件 widget 注册：加载工作流时 custom properties 按 JSON
        # 键序恢复，input_file widget 恢复(set_value)触发本节点回调时即可直接读到
        # tracks/tracks_src 缓存重建端口，无需重跑 eac3to（backend 由下拉 widget 自注册）
        self.create_property('tracks_src', '', widget_type=HIDDEN, tab='')
        self.create_property('tracks', [], widget_type=HIDDEN, tab='')
        # 探测决策结果与用户下拉选择(backend)分离: set_property 经
        # PropertyChangedCmd 会同步 widget.set_value, 若写入 backend 会覆盖下拉框
        self.create_property('resolved_backend', '', widget_type=HIDDEN, tab='')

        EXT = "蓝光 M2TS (*.m2ts *.mts);;蓝光播放列表 MPLS (*.mpls);;所有文件 (*.*)"
        w_file = FileBrowseWidget(self.view, 'input_file', '选择输入文件', exts=EXT)
        self.add_custom_widget(w_file)
        # add_custom_widget 已将 value_changed 接到 set_property，这里额外挂自动探测回调
        w_file.value_changed.connect(lambda k, v: self._on_file_changed(v))

        w_backend = NodeTextComboBoxWidget(self.view, 'backend', ['Auto', 'Eac3to', 'Mkvmerge'],'提取程序: ')
        self.add_custom_widget(w_backend)
        w_backend.value_changed.connect(lambda k, v: self._on_backend_changed(v))

    def set_ports(self, port_data):
        """拦截工作流载入时的端口重建。

        NodeGraphQt _deserialize 的顺序是: 恢复 custom properties(此时
        _on_file_changed 已做过一次颜色校正) → add_node → set_ports;
        set_ports 会清空并重建全部端口且不支持颜色(默认墨绿), 覆盖掉
        之前的校正, 因此重建完成后需按缓存轨道再校正一次。
        """
        super().set_ports(port_data)
        # 静态输入端口同样被 set_ports 重建为默认色, 按类定义 INPUTS 恢复颜色
        # (输入端口不参与动态增减, 仅做颜色恢复)
        for name, color in self.INPUTS:
            port = self.inputs().get(name)
            if port is None:
                continue
            try:
                port.view.color = color
                port.view.border_color = [min(255, max(0, i + 80)) for i in color]
            except Exception as e:
                logger.warning(f'[InputBD] 校正输入端口颜色失败: {name}, {e}')
        tracks = self.property('tracks') or []
        if tracks:
            try:
                self._rebuild_ports(tracks)
                logger.info(f'[InputBD] 载入重建端口完成, 已校正 {len(tracks)} 条端口颜色')
            except Exception as e:
                logger.warning(f'[InputBD] 载入后校正端口颜色失败: {e}')

    def _on_file_changed(self, fp):
        fp = str(fp or '').strip()
        if not fp:
            return
        fp = str(Path(fp).resolve())  # eac3to/mkvmerge 为 Windows 工具, 统一反斜杠
        if fp == self._last_probed:
            return
        if not Path(fp).is_file():
            logger.warning(f'[InputBD] 无效文件路径, 跳过探测: {fp}')
            return
        if Path(fp).suffix.lower() not in BD_INPUT_EXTS:
            logger.warning(f'[InputBD] 仅支持 m2ts/mpls 输入, 跳过: {fp}')
            return
        self._last_probed = fp

        # 恢复路径: 缓存与当前文件一致时直接重建端口, 不重跑 eac3to
        if fp == self.property('tracks_src', '') and self.property('tracks'):
            self._rebuild_ports(self.property('tracks'))
            return

        # 后台探测(子进程+MediaInfo 可能耗时数秒), 避免阻塞 UI
        self._start_probe(fp)


    # ── 后台探测 ──
    def _start_probe(self, fp: str):
        self._probe_seq += 1
        th = _ProbeThread(self, fp, self._probe_seq)
        self._probe_threads.append(th)
        th.probe_done.connect(self._on_probe_done)
        th.finished.connect(th.deleteLater)
        th.finished.connect(lambda t=th: self._cleanup_probe_thread(t))
        th.start()
        logger.info(f'[InputBD] 后台探测中(界面不阻塞): {fp}')

    def _cleanup_probe_thread(self, th):
        try:
            self._probe_threads.remove(th)
        except ValueError:
            pass


    def _on_probe_done(self, seq: int, src: str, tracks: list, backend: str):
        """后台探测完成回调: 过期结果丢弃, 有效结果写入缓存并重建端口"""
        if seq != self._probe_seq:
            return  # 过期结果(探测期间切换了文件或引擎)
        if not tracks or backend not in ('eac3to', 'mkvmerge'):
            logger.warning(f'[InputBD] 未探测到任何轨道: {src}')
            return
        self.set_property('tracks_src', src, push_undo=False)
        self.set_property('tracks', tracks, push_undo=False)
        # 决策结果写 resolved_backend(HIDDEN), 不触碰 backend 下拉
        self.set_property('resolved_backend', backend, push_undo=False)
        if self.property('input_file', '') != src:
            self.set_property('input_file', src, push_undo=False)  # 路径统一为反斜杠
        logger.info(f'[InputBD] 探测完成: {len(tracks)} 条轨道, backend={backend}, '
                    f'{[(t["type"], t["idx"]) for t in tracks]}')
        self._rebuild_ports(tracks)

    # ── backend 下拉变化 → 重新探测 ──
    def _on_backend_changed(self, v):
        fp = str(self.property('input_file', '') or '').strip()
        if fp:
            fp = str(Path(fp).resolve())
        if fp and Path(fp).is_file() and Path(fp).suffix.lower() in BD_INPUT_EXTS:
            self._last_probed = ''  # 强制重新探测
            self._on_file_changed(fp)

    # ── 探测 + backend 决策 ──
    def _resolve_tracks(self, src: str) -> tuple:
        """返回 (tracks, backend) 或 (None, None)。

        auto: eac3to 扫描 → mpls 连体盘判定(时长对比) → 命中则 mkvmerge -J 重探测;
              eac3to 扫描失败/无轨道 → mkvmerge -J 回退。
        手动 eac3to/mkvmerge: 仅走指定 backend, 失败不静默降级。
        """
        manual = str(self.property('backend', 'auto') or 'auto').strip().lower()
        probe = None
        tracks = []
        if manual != 'mkvmerge':
            eac = ToolService.get_tool_path('eac3to')
            if not eac:
                logger.warning('[InputBD] 找不到 eac3to, 请检查工具路径')
            else:
                probe = self._probe_eac3to(eac, src)
                tracks = probe.get('tracks', [])
        if tracks and manual == 'auto' and probe and probe.get('is_mpls'):
            verdict = self._detect_interleaved(Path(src), probe.get('segments', []),
                                               probe.get('playlist_dur_s', 0.0))
            if verdict == 'yes':
                logger.info('[InputBD] 检测到连体盘(playlist 含 IN/OUT 裁剪), 切换 mkvmerge')
                tracks = []
        if not tracks:
            if manual == 'eac3to':
                return None, None
            tracks = self._probe_mkvmerge(src)
            if not tracks:
                return None, None
            return tracks, 'mkvmerge'
        return tracks, 'eac3to'

    def _probe_eac3to(self, exe: str, src: str) -> dict:
        """eac3to 扫描, 返回 {tracks, segments, playlist_dur_s, is_mpls}"""
        probe = {'tracks': [], 'segments': [], 'playlist_dur_s': 0.0,
                 'is_mpls': Path(src).suffix.lower() == '.mpls'}
        try:
            cmd = [exe, src]
            logger.info(f'[InputBD] eac3to 扫描: {" ".join(str(c) for c in cmd)}')
            # cwd 固定为工具目录: eac3to 会向 CWD 写 log.txt, 避免散落到 temp/主程序目录
            r = subprocess.run(cmd, capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=300,
                               cwd=str(Path(exe).parent))
            text = ((r.stdout or b'') + (r.stderr or b'')).decode('utf-8', errors='replace')
            if not text.strip():
                logger.warning(f'[InputBD] eac3to 无输出, returncode={r.returncode}, '
                               f'请对比命令行 "{exe}" "{src}" 手动排查')
                return probe
            tracks, segments, dur_s = _parse_eac3to_scan(text, probe['is_mpls'])
            probe['tracks'] = tracks
            probe['segments'] = segments
            probe['playlist_dur_s'] = dur_s
            if not tracks:
                # 用 repr 显示, ANSI/控制字符等不可见内容会以 \x1b 形式暴露
                logger.warning(f'[InputBD] eac3to 输出中未解析到轨道, returncode={r.returncode}, '
                               f'输出尾部(repr): {text[-400:]!r}')
            else:
                logger.info(f'[InputBD] eac3to 扫描: {len(tracks)} 条轨道, '
                            f'm2ts 段={len(segments)}, playlist 时长={dur_s:.0f}s')
        except Exception as e:
            logger.error(f'[InputBD] eac3to 扫描异常: {e}')
        return probe

    def _mkvmerge_identify(self, src: str) -> dict | None:
        mk = ToolService.get_tool_path('mkvmerge')
        if not mk:
            logger.warning('[InputBD] 找不到 mkvmerge, 请检查工具路径')
            return None
        try:
            r = subprocess.run([mk, '-J', src], capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=300)
            if r.returncode != 0:
                logger.warning(f'[InputBD] mkvmerge -J 失败: returncode={r.returncode}, '
                               f'{(r.stderr or b"").decode("utf-8", errors="replace")[-300:]}')
                return None
            return json.loads((r.stdout or b'{}').decode('utf-8', errors='replace'))
        except Exception as e:
            logger.error(f'[InputBD] mkvmerge -J 异常: {e}')
            return None

    def _probe_mkvmerge(self, src: str) -> list:
        """mkvmerge -J JSON 识别轨道 (id 为 0 基, 与 eac3to 的 1 基编号互不混用)"""
        data = self._mkvmerge_identify(src)
        if not data:
            return []
        tracks = []
        for t in data.get('tracks', []):
            tt = {'subtitles': 'subtitle'}.get(t.get('type', ''), t.get('type', ''))
            if tt not in ('video', 'audio', 'subtitle'):
                continue
            props = t.get('properties', {}) or {}
            tracks.append({'type': tt, 'idx': int(t.get('id', 0)),
                           'codec': props.get('codec_id', '') or t.get('codec', ''),
                           'lang': props.get('language', '') or ''})
        chs = data.get('chapters', []) or []
        if chs:
            tracks.append({'type': 'chapter', 'idx': 0,
                           'codec': f'{len(chs)} chapters', 'lang': ''})
        logger.info(f'[InputBD] mkvmerge -J 识别: {[(t["type"], t["idx"]) for t in tracks]}')
        return tracks

    def _detect_interleaved(self, mpls: Path, segments: list, playlist_dur_s: float) -> str:
        """连体盘判定: 各 m2ts 总时长 > playlist 时长+容差 ⇒ 含 IN/OUT 裁剪 → 'yes'。

        返回 'yes' | 'no' | 'unknown'(目录不完整/读取失败, 交由运行时兜底)。
        """
        if not segments or playlist_dur_s <= 0:
            return 'unknown'
        stream_dir = None
        if mpls.parent.name.lower() == 'playlist':
            stream_dir = mpls.parent.parent / 'STREAM'
        if not stream_dir or not stream_dir.is_dir():
            logger.info('[InputBD] 无法定位 BDMV/STREAM 目录, 跳过连体盘判定')
            return 'unknown'
        mi = ToolService.get_tool_path('mediainfo')
        if not mi:
            return 'unknown'
        total_s = 0.0
        for seg in segments:
            p = stream_dir / seg
            if not p.is_file():
                logger.info(f'[InputBD] 引用的 m2ts 不存在, 跳过连体盘判定: {p}')
                return 'unknown'
            try:
                info = MediaInfo.parse(str(p), library_file=mi)
                gen = info.general_tracks[0] if info.general_tracks else None
                if gen is None or gen.duration is None:
                    return 'unknown'
                total_s += float(gen.duration) / 1000.0
            except Exception as e:
                logger.warning(f'[InputBD] MediaInfo 读取失败: {p}, {e}')
                return 'unknown'
        diff = total_s - playlist_dur_s
        logger.info(f'[InputBD] 连体盘判定: m2ts 总时长={total_s:.0f}s, '
                    f'playlist 时长={playlist_dur_s:.0f}s, 差值={diff:.0f}s')
        if diff > INTERLEAVED_TOLERANCE_S:
            return 'yes'
        return 'no'


    # ── 动态端口重建: 同名保留/多余删除/缺失追加 ──
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
                logger.info(f'[InputBD] 移除多余端口: {pn}')
            except Exception as e:
                logger.warning(f'[InputBD] 移除端口失败: {pn}, {e}')
        for pn, tt in names:
            port = self.outputs().get(pn)
            color = P.get(tt, P['any'])
            if port is None:
                self.add_output(pn, color=color)
                logger.info(f'[InputBD] 追加端口: {pn}')
            elif list(port.view.color[:3]) != list(color):
                # 工作流载入时 set_ports 重建端口不带颜色(官方序列化格式无 color),
                # 端口会回到默认墨绿, 这里按轨道类型校正(含 chapter 端口)
                try:
                    port.view.color = color
                    port.view.border_color = [min(255, max(0, i + 80)) for i in color]
                    logger.info(f'[InputBD] 校正端口颜色: {pn}')
                except Exception as e:
                    logger.warning(f'[InputBD] 校正端口颜色失败: {pn}, {e}')
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


    # ── 执行: eac3to 提取 ──
    def _extract_eac3to(self, src: str, tracks: list, temp_dir: str) -> dict | None:
        eac = ToolService.get_tool_path('eac3to')
        if not eac:
            logger.error('[InputBD] 找不到 eac3to, 请检查工具路径')
            return None
        result = {}
        nth = {}
        mk_tracks = None  # 兜底轨道惰性探测
        video_file = None
        for t in tracks:
            tt = t['type']
            if tt == 'chapter':
                continue
            nth[tt] = nth.get(tt, 0) + 1
            i = nth[tt]
            pn = f"{tt}_{i}"
            port = self.outputs().get(pn)
            if not port or not port.connected_ports():
                continue
            dst = Path(temp_dir) / f"track_{pn}{_eac3to_ext(t)}"
            ok = False
            try:
                cmd = [eac, src, f"{t['idx']}:{dst}"]
                logger.info(f'[InputBD] eac3to 提取: {" ".join(str(c) for c in cmd)}')
                # cwd 固定为工具目录: 避免 eac3to 的 log.txt 写入 temp 目录
                r = subprocess.run(cmd, capture_output=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW, timeout=14400,
                                   cwd=str(Path(eac).parent))
                if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
                    result.setdefault(pn, []).append(dst)
                    if tt == 'video' and video_file is None:
                        video_file = dst
                    logger.info(f'[InputBD] 提取成功: {dst}')
                    ok = True
                else:
                    err = ((r.stderr or b'') + (r.stdout or b'')).decode('utf-8', errors='replace')[-400:]
                    logger.warning(f'[InputBD] eac3to 提取失败: {pn}, returncode={r.returncode}, {err}')
            except Exception as e:
                logger.error(f'[InputBD] eac3to 提取异常: {pn}, {e}')
            if not ok:
                # 运行时兜底: 该轨道改用 mkvmerge 重试(类型内第 i 条)
                if mk_tracks is None:
                    mk_tracks = self._probe_mkvmerge(src)
                cand = [x for x in mk_tracks if x['type'] == tt]
                if len(cand) >= i:
                    f = self._extract_mkvmerge_track(src, tt, cand[i - 1]['idx'], pn, temp_dir)
                    if f:
                        result.setdefault(pn, []).append(f)
                        if tt == 'video' and video_file is None:
                            video_file = f
        # 章节轨(eac3to 章节即编号轨道, 输出 OGM txt)
        for t in tracks:
            if t['type'] != 'chapter':
                continue
            pn = 'chapter_1'
            port = self.outputs().get(pn)
            if not port or not port.connected_ports():
                continue
            dst = Path(temp_dir) / f"track_{pn}{_eac3to_ext(t)}"
            ok = False
            try:
                cmd = [eac, src, f"{t['idx']}:{dst}"]
                logger.info(f'[InputBD] eac3to 提取章节: {" ".join(str(c) for c in cmd)}')
                # cwd 固定为工具目录: 避免 eac3to 的 log.txt 写入 temp 目录
                r = subprocess.run(cmd, capture_output=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW, timeout=14400,
                                   cwd=str(Path(eac).parent))
                if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
                    result.setdefault(pn, []).append(dst)
                    logger.info(f'[InputBD] 章节提取成功: {dst}')
                    ok = True
                else:
                    logger.warning(f'[InputBD] eac3to 章节提取失败: returncode={r.returncode}')
            except Exception as e:
                logger.error(f'[InputBD] eac3to 章节提取异常: {e}')
            if not ok:  # 兜底: mkvmerge/mkvextract 路径
                f = self._extract_chapters_mkvmerge(src, video_file, temp_dir, pn)
                if f:
                    result.setdefault(pn, []).append(f)
        return result or None

    # ── 执行: mkvmerge 提取 (连体盘 / eac3to 失败回退) ──
    def _extract_mkvmerge(self, src: str, tracks: list, temp_dir: str) -> dict | None:
        result = {}
        nth = {}
        video_file = None
        for t in tracks:
            tt = t['type']
            if tt == 'chapter':
                continue
            nth[tt] = nth.get(tt, 0) + 1
            i = nth[tt]
            pn = f"{tt}_{i}"
            port = self.outputs().get(pn)
            if not port or not port.connected_ports():
                continue
            f = self._extract_mkvmerge_track(src, tt, t['idx'], pn, temp_dir)
            if f:
                result.setdefault(pn, []).append(f)
                if tt == 'video' and video_file is None:
                    video_file = f
        for t in tracks:
            if t['type'] != 'chapter':
                continue
            pn = 'chapter_1'
            port = self.outputs().get(pn)
            if not port or not port.connected_ports():
                continue
            f = self._extract_chapters_mkvmerge(src, video_file, temp_dir, pn)
            if f:
                result.setdefault(pn, []).append(f)
        return result or None

    def _extract_mkvmerge_track(self, src: str, tt: str, tid: int, pn: str, temp_dir: str):
        """mkvmerge 单轨输出, 显式排除其他轨道(否则默认全部封装)"""
        mk = ToolService.get_tool_path('mkvmerge')
        if not mk:
            logger.error('[InputBD] 找不到 mkvmerge, 请检查工具路径')
            return None
        ext = MKVMERGE_EXTS.get(tt, '.mks')
        dst = Path(temp_dir) / f"track_{pn}{ext}"
        if tt == 'video':
            sel, no = ['--video-tracks', str(tid)], ['-A', '-S', '--no-chapters']
        elif tt == 'audio':
            # mkvmerge 无 -n 选项(no-video 短选项为 -D), 误用会被当作输入文件名
            sel, no = ['--audio-tracks', str(tid)], ['-D', '-S', '--no-chapters']
        else:
            sel, no = ['--subtitle-tracks', str(tid)], ['-D', '-A', '--no-chapters']
        cmd = [mk, '-o', str(dst), *no, *sel, '--no-buttons', src]
        logger.info(f'[InputBD] mkvmerge 提取: {" ".join(str(c) for c in cmd)}')
        try:
            r = subprocess.run(cmd, capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=14400)
            if r.returncode in (0, 1) and dst.is_file() and dst.stat().st_size > 0:
                logger.info(f'[InputBD] mkvmerge 提取成功: {dst}')
                return dst
            logger.warning(f'[InputBD] mkvmerge 提取失败: {pn}, returncode={r.returncode}, '
                           f'{(r.stderr or b"").decode("utf-8", errors="replace")[-400:]}')
        except Exception as e:
            logger.error(f'[InputBD] mkvmerge 提取异常: {pn}, {e}')
        return None

    def _extract_chapters_mkvmerge(self, src: str, video_file, temp_dir: str, pn: str):
        """mkvmerge backend 的章节: 优先 mkvextract 从已输出容器抽取, 回退 -J JSON 生成 OGM"""
        dst = Path(temp_dir) / f"track_{pn}.txt"
        mkx = ToolService.get_tool_path('mkvextract')
        if mkx and video_file and Path(video_file).is_file():
            try:
                r = subprocess.run([mkx, 'chapters', str(video_file)], capture_output=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW, timeout=300)
                txt = (r.stdout or b'').decode('utf-8', errors='replace')
                if txt.strip() and 'CHAPTER' in txt:
                    dst.write_text(txt, encoding='utf-8')
                    logger.info(f'[InputBD] mkvextract 章节提取成功: {dst}')
                    return dst
                logger.warning('[InputBD] mkvextract 未输出章节, 回退 -J 生成')
            except Exception as e:
                logger.warning(f'[InputBD] mkvextract 章节提取异常: {e}')
        data = self._mkvmerge_identify(src)
        if data:
            chs = data.get('chapters', []) or []
            if chs:
                dst.write_text(_ogm_from_json_chapters(chs), encoding='utf-8')
                logger.info(f'[InputBD] 由 mkvmerge -J 生成 OGM 章节: {dst}')
                return dst
        logger.warning('[InputBD] 源中未发现章节')
        return None


    def execute(self, inputs: dict, temp_dir: str) -> dict | None:
        logger.info('\n' * 2 + '=' * 40 + ' [InputBD] ' + '=' * 40)
        src = str(self.property('input_file', '') or '').strip()
        if not src:
            self._last_error = 'BD 规范化输入未设置有效的输入文件'
            return None
        src = str(Path(src).resolve())  # 统一 Windows 反斜杠
        if not Path(src).is_file():
            self._last_error = 'BD 规范化输入未设置有效的输入文件'
            return None
        if Path(src).suffix.lower() not in BD_INPUT_EXTS:
            self._last_error = f'BD 规范化输入仅支持 m2ts/mpls, 收到: {Path(src).suffix}'
            return None

        tracks = []
        backend = ''
        if self.property('tracks_src', '') == src:
            tracks = self.property('tracks') or []
            backend = str(self.property('resolved_backend', '') or '').strip().lower()
        if not tracks or backend not in ('eac3to', 'mkvmerge'):
            # 缓存缺失或决策缺失 → 现探测(运行于子线程, 不写回属性)
            tracks, backend = self._resolve_tracks(src)
        if not tracks:
            self._last_error = f'未能从文件探测到轨道: {src}'
            return None
        logger.info(f'[InputBD] backend={backend}, 共 {len(tracks)} 条轨道: '
                    f'{[(t["type"], t["idx"]) for t in tracks]}')

        if backend == 'mkvmerge':
            result = self._extract_mkvmerge(src, tracks, temp_dir)
        else:
            result = self._extract_eac3to(src, tracks, temp_dir)
        if not result:
            self._last_error = ErrorService.cli_error(backend, '未能提取任何已连接的轨道')
        return result or None
