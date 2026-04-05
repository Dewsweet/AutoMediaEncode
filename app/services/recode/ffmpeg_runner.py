# coding: utf-8
import os
import ffmpeg
from pathlib import Path
from ...common.media_utils import classify_files
from .ffmpeg_builder import FFmpegBuilder

class FFmpegRunner:
    def __init__(self):
        self.builder = FFmpegBuilder()

    def test_build_commands(self, files: list, video_state: dict, audio_state: dict, image_state: dict, subtitle_state: dict, output_state: dict):
        """
        Debug：专门用于接收界面参数，组装出命令并打印测试。
        之后接入正式的线程时，可以在本类下增加 run_command 等方法。
        """
        print("\n\n====== [FFmpeg-Python 参数装配测试] ======")
        print(f"UI Video State: {video_state}\n")
        print(f"UI Audio State: {audio_state}\n")
        
        if not files:
            print("未检测到文件，请先载入文件或右键重载测试文件。")
            return

        for f_path in files:
            file_path = Path(f_path)
            print(f"\n[处理文件]: {file_path.as_posix()}")
            
            # --- 1. 获取文件基础分类（判断是视频还是音频等） ---
            classification = classify_files([file_path.as_posix()])
            is_video = bool(classification['video'])
            is_audio = bool(classification['audio']) and not is_video # 独立音频文件
            
            # --- 2. 获取当前参数池 ---
            audio_kwargs, audio_container = self.builder.build_audio_kwargs(audio_state)

            # --- 3. 组装输入输出路径 ---
            in_path_str = file_path.as_posix()
            
            out_ext = file_path.suffix
            if is_video:
                out_ext = "." + video_state.get('container', 'mp4').lower()
            elif is_audio:
                out_ext = ("." + audio_container).lower() if audio_container else file_path.suffix
            
            out_dir = output_state.get('output_dir', '')
            if output_state.get('use_source_dir', True) or not out_dir:
                out_dir_path = file_path.parent
            else:
                out_dir_path = Path(out_dir)
            
            fname = file_path.stem
            if output_state.get('use_custom_suffix') and output_state.get('custom_suffix'):
                fname += output_state.get('custom_suffix', '')
                
            out_path = out_dir_path / (fname + out_ext)
            out_path_str = out_path.as_posix()

            # --- 4. 生成不同媒体类型的命令 ---
            if is_video:
                v_kwargs_list = self.builder.build_video_kwargs(video_state)
                for i, v_kw in enumerate(v_kwargs_list):
                    # 复制一份当前遍的视频参数
                    merged_kw = v_kw.copy()
                    
                    # 音频参数合并进视频参数中
                    # 如果是 2-pass 的第 1 遍占位符，通常不处理音频
                    if merged_kw.get("pass") == 1 or merged_kw.get("pass") == "1":
                        merged_kw["an"] = None
                        out_path_compile = "NUL" if os.name == 'nt' else "/dev/null"
                        merged_kw["f"] = "null"
                    else:
                        out_path_compile = out_path_str
                        # 合并音频参数
                        merged_kw.update(audio_kwargs)

                    print(f">> [视频处理 - Pass {i+1}] Kwargs 详情: {merged_kw}")
                    try:
                        stream = ffmpeg.input(in_path_str)
                        stream = ffmpeg.output(stream, out_path_compile, **merged_kw)
                        cmd_list = ffmpeg.compile(stream, overwrite_output=True)
                        print(">> 生成的真实命令:", ' '.join(cmd_list))
                    except Exception as e:
                        print(">> FFmpeg-python 编译失败:", str(e))
            
            elif is_audio:
                # 纯音频文件处理逻辑（屏蔽视频流）
                merged_kw = audio_kwargs.copy()
                merged_kw["vn"] = None
                
                print(f">> [独立音频处理] Kwargs 详情: {merged_kw}")
                try:
                    stream = ffmpeg.input(in_path_str)
                    stream = ffmpeg.output(stream, out_path_str, **merged_kw)
                    cmd_list = ffmpeg.compile(stream, overwrite_output=True)
                    print(">> 生成的真实命令:", ' '.join(cmd_list))
                except Exception as e:
                    print(">> FFmpeg-python 编译失败:", str(e))

        print("============================\n\n")
