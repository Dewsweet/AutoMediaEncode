import subprocess, shlex, time
from pathlib import Path
from app.services.tool_service import ToolService
from app.common.logger import logger
from app.services.setting.preset_service import preset_service
from app.services.error_service import ErrorService

def _do_cli_encode(node, inputs, temp_dir, tool_key, ext):
    """x264/x265/SVTAV1 通用 CLI 编码（支持文件输入和管道输入）"""
    logger.info('\n' * 2 + '=' * 40 + f' [{node.NODE_NAME}] ' + '=' * 40)
    inp = inputs.get('input', [''])
    src_raw = inp[0] if inp else ''

    if not src_raw:
        logger.warning(f'[{node.NODE_NAME}] 没有输入文件')
        return None

    cli_p = ToolService.get_tool_path(tool_key)
    if not cli_p:
        logger.error(f'[{node.NODE_NAME}] 找不到 {tool_key} 编码器')
        return None
    
    ff_p = ToolService.get_tool_path('ffmpeg')
    if not ff_p:
        logger.error(f'[{node.NODE_NAME}] 找不到 ffmpeg')
        return None    


    dst = Path(temp_dir) / f'{tool_key}_{node.id}{ext}'
    cli_args = _build_cli_args(node, tool_key)
    try:
        args = shlex.split(cli_args) if cli_args else []
    except ValueError:
        args = cli_args.split() if cli_args else []
    cf = subprocess.CREATE_NO_WINDOW
    cancelled = getattr(node, '_ame_cancelled', lambda: False)
    paused = getattr(node, '_ame_paused', None)

    # ── 管道模式 (vspipe → x264/x265/svtav1) ──
    is_pipe = isinstance(src_raw, dict) and src_raw.get('pipe')
    if is_pipe:
        pipe_cmd = src_raw['cmd']
        if tool_key.lower() == 'svtav1':
            enc_cmd = [cli_p, '-i', '-']
            enc_cmd.extend(args)
            enc_cmd.extend(['-b', str(dst)])
        elif tool_key.lower() == 'x265':
            enc_cmd = [cli_p, '--y4m', '--input', '-']
            enc_cmd.extend(args)
            enc_cmd.extend(['--output', str(dst)])
        else:
            enc_cmd = [cli_p, '--demuxer', 'y4m']
            enc_cmd.extend(args)
            enc_cmd.extend(['-o', str(dst), '-'])

        logger.info(f'[{node.NODE_NAME}] 编码命令: {" ".join(enc_cmd)}')
        try:
            if dst.exists(): # 确保目标文件不存在，避免某些编码器拒绝覆盖
                dst.unlink()
            
            r, err_msg = _run_pipe(pipe_cmd, {}, enc_cmd,
                          {'stderr': subprocess.STDOUT, 'text': True, 'bufsize': 1},
                          node)
            if r is None: return None
            if r == 0 and dst.is_file() and dst.stat().st_size > 0:
                logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
                return {'video': [str(dst)]}
            else:
                logger.error(f'[{node.NODE_NAME}] 编码失败: returncode={r}')
                node._last_error = ErrorService.cli_error(tool_key, err_msg)
                return None
        except Exception as e:
            logger.error(f'[{node.NODE_NAME}] 管道编码异常: {e}')
            return None

    # ── 文件模式 ──
    src = str(src_raw)
    logger.info(f'[{node.NODE_NAME}] 输入文件: {src}')

    if tool_key.lower() == 'svtav1':
        ff_cmd = [ff_p, '-i', src, '-f', 'yuv4mpegpipe', '-strict', 'unofficial', '-']
        av1_cmd = [cli_p, '-i', '-']
        av1_cmd.extend(args)
        av1_cmd.extend(['-b', str(dst)])
        logger.info(f'[{node.NODE_NAME}] FFmpeg 命令: {" ".join(ff_cmd)}')
        logger.info(f'[{node.NODE_NAME}] SvtAv1 命令: {" ".join(av1_cmd)}')
        try:
            if dst.exists():
                dst.unlink()

            r, err_msg = _run_pipe(ff_cmd, {'stderr': subprocess.DEVNULL},
                          av1_cmd, {'stderr': subprocess.STDOUT, 'text': True, 'bufsize': 1},
                          node)
            if r is None: return None
            if r == 0 and dst.is_file() and dst.stat().st_size > 0:
                logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
                return {'video': [str(dst)]}
            else:
                logger.error(f'[{node.NODE_NAME}] 编码失败: returncode={r}')
                node._last_error = ErrorService.cli_error(tool_key, err_msg)
                return None
        except Exception as e:
            logger.error(f'[{node.NODE_NAME}] 编码异常: {e}')
            return None
    else:
        cmd = [cli_p]
        cmd.extend(args)
        cmd.extend(['-o', str(dst), src])

        logger.info(f'[{node.NODE_NAME}] 命令: {" ".join(str(c) for c in cmd)}')
        try:
            r, rstdout = _run_with_progress(cmd, cancelled, paused, timeout=14400)
            if r is None:  # 用户取消
                logger.info(f'[{node.NODE_NAME}] 已取消')
                return None
            if r == 0 and dst.is_file() and dst.stat().st_size > 0:
                logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
                return {'video': [str(dst)]}
            else:
                logger.error(f'[{node.NODE_NAME}] 编码失败: returncode={r}')
                node._last_error = ErrorService.cli_error(tool_key, f'returncode={rstdout}')
                return None
        except Exception as e:
            logger.error(f'[{node.NODE_NAME}] 编码异常: {e}')
            node._last_error = ErrorService.cli_error(tool_key, str(rstdout))
            return None

def _do_qaac_encode(node, inputs, temp_dir, ext):
    """QAAC 通用 CLI 编码"""
    logger.info('\n' * 2 + '=' * 40 + f' [AAC] ' + '=' * 40)
    src = (inputs.get('input') or [''])[0]
    logger.info(f'[AAC] 输入文件: {src}')

    if not src:
        logger.warning(f'[AAC] 没有输入文件')
        return None
    
    qaac = ToolService.get_tool_path('qaac')
    if not qaac:
        logger.error(f'[AAC] 找不到 qaac 编码器')
        return None
    
    dst = Path(temp_dir) / f'qaac_{node.id}{ext}'
    wdata = node.property('Audio_codec', {})
    if isinstance(wdata, dict):
        bitrate = wdata.get('bitrate', '192')
        custom_cli = wdata.get('custom_cli', '')

    cmd = [qaac]
    if custom_cli:
        custom_cmd = shlex.split(custom_cli)
        cmd.extend(custom_cmd)
        cmd.extend(['-o', dst, src])
    else:
        cmd.extend(['-i', '-V', bitrate, '-q 2', '--no-delay', '-o', dst, src])

    logger.info(f'[{node.NODE_NAME}] 命令: {" ".join(str(c) for c in cmd)}')
    try:
        cancelled = getattr(node, '_ame_cancelled', lambda: False)
        paused = getattr(node, '_ame_paused', None)
        r, err_msg = _run_with_progress(cmd, cancelled, paused, timeout=14400)
        if r is None:
            return None  # 用户取消
        if r == 0 and dst.is_file() and dst.stat().st_size > 0:
            logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
            return {'audio': [dst]}
        else:
            logger.error(f'[{node.NODE_NAME}] 失败: returncode={r}')
            node._last_error = ErrorService.cli_error('qaac', str(err_msg))
            return None
    except Exception as e:
        logger.error(f'[{node.NODE_NAME}] 编码异常: {e}')
        return None


def _do_ffmpeg_audio(node, inputs, temp_dir, default_codec, default_ext):
    """通用 FFmpeg 音频编码"""
    logger.info('\n' * 2 + '=' * 40 + f' [{node.NODE_NAME}] ' + '=' * 40)
    src = (inputs.get('input') or [''])[0]
    logger.info(f'[{node.NODE_NAME}] 输入文件: {src}')

    if not src:
        logger.warning(f'[{node.NODE_NAME}] 没有输入文件')
        return None
    ff = ToolService.get_tool_path('ffmpeg')
    if not ff:
        logger.error(f'[{node.NODE_NAME}] 找不到 ffmpeg')
        return None
    
    widget_data = node.property('Audio_codec', {})
    if isinstance(widget_data, dict):
        if default_codec:
            codec = default_codec
        else:
            codec = widget_data.get('encoder', default_codec)
        bitrate = widget_data.get('bitrate', '')
        compression_level = widget_data.get('compression_level', '')
        custom_options = widget_data.get('custom_cli', '')
        try:
            args = shlex.split(custom_options) if custom_options else []
        except ValueError:
            args = custom_options.split() if custom_options else []

    if default_ext:
        ext = default_ext
    else:
        ext = _codec_to_ext(codec)
    dst = Path(temp_dir) / f'a_{node.id}{ext}'
    cmd = [ff, '-i', src, '-c:a', codec, '-vn', dst, '-y']
    if custom_options:
        cmd[-3:-3] = args
    else:
        if bitrate:
            cmd[-3:-3] = ['-b:a', bitrate + 'k']
        if compression_level and default_codec == 'flac':
            cmd[-3:-3] = ['-compression_level', str(compression_level)]
    logger.info(f'[{node.NODE_NAME}] 组装命令: {" ".join(str(c) for c in cmd)}')
    try:
        cancelled = getattr(node, '_ame_cancelled', lambda: False)
        paused = getattr(node, '_ame_paused', None)
        r, err_msg = _run_with_progress(cmd, cancelled, paused, timeout=14400)
        if r is None:
            return None  # 用户取消
        if r == 0 and dst.is_file() and dst.stat().st_size > 0:
            logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
            return {'audio': [dst]}
        else:
            logger.error(f'[{node.NODE_NAME}] 编码失败: returncode={r}')
            node._last_error = ErrorService.cli_error('ffmpeg', str(err_msg))
            return None
    except Exception as e:
        logger.error(f'[{node.NODE_NAME}] 编码异常: {e}')
        return None

def _do_ffmpeg_video(node, inputs, temp_dir):
    """通用 FFmpeg 视频编码"""
    widget_data = node.property('Video_codec', {})
    if isinstance(widget_data, dict):
        codec = widget_data.get('encoder', 'libx264')
        custom_options = widget_data.get('custom_cli', '')
        try:
            args = shlex.split(custom_options) if custom_options else []
        except ValueError:
            args = custom_options.split() if custom_options else []
        

    logger.info('\n' * 2 + '=' * 40 + f' [{codec}] ' + '=' * 40)
    src = (inputs.get('input') or [''])[0]
    logger.info(f'[{codec}] 输入文件: {src}')
    if not src:
        logger.warning(f'[{codec}] 没有输入文件')
        return None
    
    ff = ToolService.get_tool_path('ffmpeg')
    if not ff:
        logger.error(f'[{codec}] 找不到 ffmpeg')
        return None

    ext = _codec_to_ext(codec)
    dst = Path(temp_dir) / f'v_{node.id}{ext}'
    cmd = [ff, '-i', src, '-c:v', codec, '-an', dst, '-y']
    if custom_options:
        cmd[-3:-3] = args
    logger.info(f'[{codec}] 组装命令: {" ".join(str(c) for c in cmd)}')
    try:
        cancelled = getattr(node, '_ame_cancelled', lambda: False)
        paused = getattr(node, '_ame_paused', None)
        r, err_msg = _run_with_progress(cmd, cancelled, paused, timeout=14400)
        if r is None:
            return None  # 用户取消
        if r == 0 and dst.is_file() and dst.stat().st_size > 0:
            logger.info(f'[{codec}] 编码成功: {dst}')
            return {'video': [dst]}
        else:
            logger.error(f'[{codec}] 编码失败: returncode={r}')
            node._last_error = ErrorService.ffmpeg_error(str(err_msg))
            return None
    except Exception as e:
        logger.error(f'[{codec}] 编码异常: {e}')
        return None


def _codec_to_ext(codec: str) -> str:
    c = codec.lower().replace('_', '')
    m = {
        'h264': '.h264', 'avc': '.h264', 'libx264': '.h264', 'h264_nvenc': '.h264', 'h264_qsv': '.h264', 'h264_amf': '.h264',
        'hevc': '.h265', 'h265': '.h265', 'libx265': '.h265', 'h265_nvenc': '.h265', 'h265_qsv': '.h265', 'h265_amf': '.h265',
        'av1': '.ivf', 'vp9': '.ivf', 'libsvtav1': '.ivf', 'svtav1': '.ivf', 'libvpx-vp9': '.ivf', 'libvp8': '.ivf',
        'av1_qsv': '.ivf', 'av1_nvenc': '.ivf', 'av1_amf': '.ivf',
        'aac': '.aac', 'flac': '.flac',
        'opus': '.opus', 'vorbis': '.ogg', 'pcm': '.wav', 'mp3': '.mp3',
        'ac3': '.ac3', 'eac3': '.eac3', 'dts': '.dts', 'ass': '.ass',
        'srt': '.srt', 'vtt': '.vtt',
    }
    for k, v in m.items():
        if k in c:
            return v
    return '.mkv'


def _build_cli_args(node, tool_key):
    """从节点属性中提取 CLI 参数 (preset/custom_cli)"""
    pcfg = node.property('preset_cfg', {})
    use_p = pcfg.get('use_preset', True) if isinstance(pcfg, dict) else True
    pname = pcfg.get('preset', '') if isinstance(pcfg, dict) and use_p else ''
    cli_args = node.property('custom_cli', '')
    if use_p and pname:
        presets = preset_service.get_presets_by_encoder(tool_key)
        cli_args = presets.get(pname, '')
    return cli_args


def _run_with_progress(cmd, cancelled, paused=None, timeout=14400, text=True):
    """Popen 轮询执行命令，支持取消和暂停检测"""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=text, creationflags=subprocess.CREATE_NO_WINDOW, bufsize=1)
    start = time.time()

    output_lines = []

    for line in proc.stdout:
        output_lines.append(line)

        if paused and paused():
            while paused():
                time.sleep(0.1)
                if cancelled():
                    proc.terminate()
                    try: proc.wait(timeout=3)
                    except subprocess.TimeoutExpired: proc.kill()
                    return None
        if cancelled():
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill()
            return None
        if timeout and time.time() - start > timeout:
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill()
            return -1
    proc.wait()
    full_output = "".join(output_lines)
    return proc.returncode, full_output


def _run_pipe(cmd1, kw1, cmd2, kw2, node, timeout=14400):
    """双进程管道: proc1 stdout → proc2 stdin. 支持取消/暂停. 返回 proc2.returncode 或 None"""
    cancelled = getattr(node, '_ame_cancelled', lambda: False)
    paused = getattr(node, '_ame_paused', None)
    cf = subprocess.CREATE_NO_WINDOW

    kw2 = kw2 or {}
    kw2['stdout'] = subprocess.PIPE
    kw2['stderr'] = subprocess.STDOUT
    kw2['text'] = True
    kw2['bufsize'] = 1

    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, **(kw1 or {}), creationflags=cf) # kw1 是字典，
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, **(kw2 or {}), creationflags=cf)
    p1.stdout.close()

    start = time.time()
    out_lines = []

    for line in p2.stdout:
        out_lines.append(line)
        
        if paused and paused():
            while paused():
                time.sleep(0.1)
                if cancelled():
                    p2.terminate(); p1.terminate()
                    for p in (p2, p1):
                        try: p.wait(timeout=3)
                        except subprocess.TimeoutExpired: p.kill()
                    return None
        if cancelled():
            p2.terminate(); p1.terminate()
            for p in (p2, p1):
                try: p.wait(timeout=3)
                except subprocess.TimeoutExpired: p.kill()
            return None
        if timeout and time.time() - start > timeout:
            p2.terminate(); p1.terminate()
            for p in (p2, p1):
                try: p.wait(timeout=3)
                except subprocess.TimeoutExpired: p.kill()
            return -1
        time.sleep(0.1)

    if p1.poll() is None:
        p1.terminate()
        try: p1.wait(timeout=5)
        except subprocess.TimeoutExpired: p1.kill()
    full_output = "".join(out_lines)
    return p2.returncode, full_output