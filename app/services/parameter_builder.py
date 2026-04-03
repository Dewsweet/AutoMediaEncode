import json
import os
import re

class SafeFormatDict(dict):
    """一个安全的字典，在格式化字符串时如果遇到找不到的键，就原样保留 {key} 而不报错"""
    def __missing__(self, key):
        return "{" + key + "}"

class MediaParameterBuilder:
    def __init__(self):
        # 初始化时加载本地的参数映射JSON表
        self.common_path = os.path.join(os.path.dirname(__file__), '..', 'common')
        config_path = os.path.join(self.common_path, 'encoder_config.json')
        preset_path = os.path.join(self.common_path, 'custom_preset.json')
        
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            self.config = json.load(f)
            
        try:
            with open(preset_path, 'r', encoding='utf-8-sig') as f:
                self.custom_preset_config = json.load(f)
        except Exception:
            self.custom_preset_config = {}

    def parse_cli_to_ffmpeg_params(self, cli_str: str) -> str:
        """
        这个函数按您的要求可以不再用于有原生编码器的地方，
        但为防其他（如SVT如果不叫svtav1而在ffmpeg里还要用）暂留，
        或者根据要求，若确认这些都不用转ffmpeg，只走原生则可以直接禁用调用。
        """
        if not cli_str:
            return ""
            
        matches = re.finditer(r'--([a-zA-Z0-9_-]+)(?:\s+([^-][^\s]*))?', cli_str)
        params = []
        for match in matches:
            key = match.group(1)
            val = match.group(2)
            if val:
                params.append(f"{key}={val}")
            else:
                params.append(f"{key}=1") # 类似 --weightb 这种单独的开关，转成 weightb=1
                
        return ":".join(params)


    def _get_preset_key(self, encoder: str):
        if "x264" in encoder: return "x264"
        elif "x265" in encoder: return "x265"
        elif "AV1" in encoder: return "SVT-AV1"
        return ""

    def build_video_args(self, video_state: dict) -> list:
        # 返回的是一个由参数列表组成的列表（例如2pass时可能需要执行两次会有两组命令参数）
        encoder = video_state.get('encoder_format', 'Copy')
        
        if encoder not in self.config.get("Video", {}):
            return [["-c:v", "copy"]]
            
        video_config = self.config["Video"][encoder]
        base_cmd = video_config.get("base_cmd", [])
        
        # 检查是否使用原生编码器
        encoder_names = video_config.get("encoder_name", [])
        is_native_encoder = False
        if any(name in ["x264", "x265", "svtav1"] for name in encoder_names):
            is_native_encoder = True
        
        if encoder in ["Copy", "FFV1"]:
            return [base_cmd[:]]

        # 用户自定义参数
        custom_options = video_state.get('custom_options', '')
        if custom_options:
            import shlex
            args = base_cmd[:]
            args.extend(shlex.split(custom_options))
            return [args]
        
        args = base_cmd[:]

        # 2. 判断是否使用了 custom预设
        use_preset = video_state.get('use_preset', False)
        preset_name = video_state.get('preset_name', '')
        
        # 针对 x264/x265 等如果启用预设, 走不通 ffmpeg -x264-params 形式，直接用他们的标准cli
        if use_preset and preset_name and is_native_encoder:
            preset_key = self._get_preset_key(encoder)
            if preset_key and preset_key in self.custom_preset_config:
                cli_str = self.custom_preset_config[preset_key].get(preset_name, "")
                if cli_str:
                    # 如果是原生编码器调用方式，应当返回特别标识，提示外部使用对应工具，或
                    # 按需求，仍然需要返回给调用方，但是不用转换成ffmpeg格式。这里根据上下文要求“直接使用原生编码器”。
                    # 但是由于当前是返回组装ffmpeg参数，需要一种方式返回原生命令，或者将原生CLI作为 "-x264-params", 但需求1说“不兼容ffmpeg不能转...启用预设就不调用ffmpeg，使用原生编码器”。
                    # 意味着如果启用预设，`build_video_args` 应当通知外面不要用 ffmpeg，或者返回原生命令结构。
                    return [{"is_native": True, "encoder_exe": encoder_names[0], "cli_params": cli_str}]
        elif use_preset and preset_name:
            preset_key = self._get_preset_key(encoder)
            if preset_key and preset_key in self.custom_preset_config:
                cli_str = self.custom_preset_config[preset_key].get(preset_name, "")
                if cli_str:
                    parsed_params = self.parse_cli_to_ffmpeg_params(cli_str)
                    if parsed_params:
                        args.extend([f"-{preset_key.lower()}-params", f'"{parsed_params}"'])
                    return [args]


        # 3. 获取并填充码率控制模板
        rc_mode = video_state.get('rc_mode', '')
        rc_templates = video_config.get("rate_control", {}).get(rc_mode, [])
        
        # 安全替换占位符
        format_data = SafeFormatDict({
            "quality_val": video_state.get("quality_val", 20),
            "bitrate": video_state.get("bitrate", 1000),
            "preset_name": video_state.get("preset_val", ""),
            "profile_name": video_state.get("profile_name", ""),
            "level_val": video_state.get("level_val", ""),
            "tuning_name": video_state.get("tuning_name", "")
        })
        
        rc_generated = [tmpl.format_map(format_data) for tmpl in rc_templates]
            
        # 4. 获取并填充 options 部分 (preset, profile, level, tune)
        options_dict = video_config.get("options", {})
        options_args = []
        
        # 处理 Presets
        ui_preset = video_state.get("preset_val", "")
        if "presets" in options_dict and ui_preset and ui_preset.lower() not in ["none", "auto"]:
            conf_presets = options_dict["presets"]
            if isinstance(conf_presets, dict):
                if ui_preset in conf_presets:
                    options_args.extend(conf_presets[ui_preset])
                elif f"preset_{ui_preset}" in conf_presets:
                    options_args.extend(conf_presets[f"preset_{ui_preset}"])
            elif isinstance(conf_presets, list):
                for p in conf_presets:
                    options_args.append(p.format_map(format_data))
                    
        # 处理 profile, level, tune
        for key, ui_val in [
            ("profiles", video_state.get("profile_name", "")),
            ("levels", video_state.get("level_val", "")),
            ("tune", video_state.get("tuning_name", ""))
        ]:
            if key in options_dict and ui_val and ui_val.lower() not in ["none", "auto"]:
                conf_val = options_dict[key]
                if isinstance(conf_val, list):
                    for p in conf_val:
                        options_args.append(p.format_map(format_data))

        # 5. 2-pass 逻辑处理
        is_2pass = video_state.get('is_2pass', False)
        if is_2pass:
            rate_config = video_config.get("rate_control", {})
            if "2pass_1" in rate_config and "2pass_2" in rate_config:
                pass1 = rate_config["2pass_1"]
                pass2 = rate_config["2pass_2"]
                cmd1 = base_cmd[:] + rc_generated + options_args + [p.format_map(format_data) for p in pass1]
                cmd2 = base_cmd[:] + rc_generated + options_args + [p.format_map(format_data) for p in pass2]
                return [cmd1, cmd2]
            elif "2pass" in rate_config:
                pass_single = rate_config["2pass"]
                return [base_cmd[:] + rc_generated + options_args + [p.format_map(format_data) for p in pass_single]]

        args.extend(rc_generated)
        args.extend(options_args)
        return [args]

    def build_audio_args(self, audio_state: dict) -> list:
        args = []
        encoder = audio_state.get('encoder_format', 'Copy')
        
        if encoder not in self.config.get("Audio", {}):
            return ["-c:a", "copy"]
            
        audio_config = self.config["Audio"][encoder]
        args.extend(audio_config.get("base_cmd", []))
        
        if encoder in ["Copy", "WAV", "FLAC", "ALAC"]:
            return args
            
        rc_mode = audio_state.get('rc_mode', '')
        rc_templates = audio_config.get("rate_control", {}).get(rc_mode, [])
        
        format_data = SafeFormatDict({
            "quality_val": audio_state.get("quality_val", 5),
            "bitrate": audio_state.get("bitrate", 128)
        })
        
        for tmpl in rc_templates:
            args.append(tmpl.format_map(format_data))
            
        return args

    def build_image_args(self, image_state: dict, input_resolution: tuple = None) -> list:
        args = []
        encoder = image_state.get('encoder_format', 'JPEG')
        
        if encoder not in self.config.get("Image", {}):
            return []

        image_config = self.config["Image"][encoder]
        args.extend(image_config.get("base_cmd", []))

        is_lossless = image_state.get('is_lossless', False)
        if is_lossless and "lossless" in image_config:
            args.extend(image_config["lossless"])
        elif not is_lossless and "quality" in image_config:
            format_data = SafeFormatDict({
                "quality_val": image_state.get("quality_val", 75)
            })
            args.extend([p.format_map(format_data) for p in image_config["quality"]])

        # Image filters
        filters = []
        filter_config = self.config.get("iamge_filters", {})
        
        # 1. Rotate
        rotate = image_state.get("rotate", "")
        # 注意：json中的key是小写 "rotate"
        if rotate and rotate in filter_config.get("rotate", {}):
            filters.extend(filter_config["rotate"][rotate])
            
        # 2. Flip
        flip = image_state.get("flip", "")
        # 注意：json中的key是小写 "flip"
        if flip and flip in filter_config.get("flip", {}):
            filters.extend(filter_config["flip"][flip])

        # 3. Crop
        crop_w = image_state.get("crop_w")
        crop_h = image_state.get("crop_h")

        if crop_w and crop_h:
            format_data = SafeFormatDict({"width": crop_w, "height": crop_h})
            
            use_resize = True # 默认使用缩放以确保输出尺寸
            
            if input_resolution:
                iw, ih = input_resolution
                try:
                    cw, ch = int(crop_w), int(crop_h)
                    # 如果输入分辨率足够大，则使用直接裁剪
                    # 只有当输入分辨率小于目标分辨率时才缩放
                    if iw >= cw and ih >= ch:
                        use_resize = False
                except ValueError:
                    pass
            
            if use_resize:
                # 使用 crop_dimension_resize (缩放后裁剪)
                # 注意: json中默认为 decrease, 这里直接使用 json 配置
                tmpls = filter_config.get("crop_dimension_resize", 
                        ["scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"])
            else:
                # 使用 crop_dimension (直接裁剪)
                tmpls = filter_config.get("crop_dimension", ["crop={width}:{height}"])
                
            for tmpl in tmpls:
                filters.append(tmpl.format_map(format_data))
            
        if filters:
            vf_cmd = filter_config.get("base_cmd", ["-vf"])
            args.extend(vf_cmd)
            args.append(",".join(filters))
            
        return args

    def build_subtitle_args(self, subtitle_state: dict) -> list:
        # 字幕不使用ffmpeg进行编码，只需要后缀即可，因此返回空参数
        return []
