from math import log
from re import sub
import subprocess, shlex
from pathlib import Path
from app.services.tool_service import ToolService
from app.common.logger import logger
from app.services.setting.preset_service import preset_service
from app.services.recode.native_cli_parser import NativeCliParser

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
            # x264
            enc_cmd = [cli_p, '--demuxer', 'y4m']
            enc_cmd.extend(args)
            enc_cmd.extend(['-o', str(dst), '-'])

        logger.info(f'[{node.NODE_NAME}] 编码命令: {" ".join(enc_cmd)}')
        try:
            vs_proc = subprocess.Popen(pipe_cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE, creationflags=cf)
            enc_proc = subprocess.Popen(enc_cmd, stdin=vs_proc.stdout, creationflags=cf)
            vs_proc.stdout.close() 
            enc_proc.wait() 
            if enc_proc.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
                logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
                return {'video': [str(dst)]}
            else:
                logger.error(f'[{node.NODE_NAME}] 编码失败: returncode={enc_proc.returncode}')
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
            ff_proc = subprocess.Popen(ff_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=cf)
            av1_proc = subprocess.Popen(av1_cmd, stdin=ff_proc.stdout, creationflags=cf)
            ff_proc.stdout.close()
            av1_proc.wait()
            if av1_proc.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
                logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
                return {'video': [str(dst)]}
            else:
                logger.error(f'[{node.NODE_NAME}] 编码失败: returncode={av1_proc.returncode}')
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
        r = subprocess.run(cmd, creationflags=cf, capture_output=True, timeout=14400)
        if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
            logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
            return {'video': [str(dst)]}
        else:
            logger.error(f'[{node.NODE_NAME}] 编码失败: returncode={r.returncode}, stderr={r.stderr[:200]}')
            return None
    except Exception as e:
        logger.error(f'[{node.NODE_NAME}] 编码异常: {e}')
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
    
    dst = temp_dir / f'qaac_{node.id}{ext}'
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
        r = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, timeout=14400)
        if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
            logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
            return {'audio': [dst]}
        else:
            logger.error(f'[{node.NODE_NAME}] 失败: {r.stderr[:200]}')
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
        r = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, timeout=14400)
        if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
            logger.info(f'[{node.NODE_NAME}] 编码成功: {dst}')
            return {'audio': [dst]}
        else:
            logger.error(f' [{node.NODE_NAME}] 编码失败: returncode={r.returncode}, stderr={r.stderr[:200]}')
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
        r = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, timeout=14400)
        if r.returncode == 0 and dst.is_file() and dst.stat().st_size > 0:
            logger.info(f'[{codec}] 编码成功: {dst}')
            return {'video': [dst]}
        else:
            logger.error(f' [{codec}] 编码失败: returncode={r.returncode}, stderr={r.stderr[:200]}')
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
