# coding: utf-8
import json
import shlex

from .native_cli_parser import NativeCliParser
from ..path_service import PathService

class SafeFormatDict(dict):
    """一个安全的字典，在格式化字符串时如果遇到找不到的键，就原样保留 {key} 而不报错"""
    def __missing__(self, key):
        return "{" + key + "}"

class FFmpegBuilder:
    def __init__(self):
        config_path = PathService.get_common_dir() / 'Json' / 'recode_ffmpeg_config.json'
        
        preset_path = PathService.get_config_dir() / 'custom_preset.json'
        if not preset_path.exists():
            preset_path = PathService.get_common_dir() / 'Json' / 'custom_preset.json'
            
        with open(config_path, 'r', encoding='utf-8-sig') as f:
            self.config = json.load(f)
            
        try:
            with open(preset_path, 'r', encoding='utf-8-sig') as f:
                self.custom_preset_config = json.load(f)
        except Exception:
            self.custom_preset_config = {}

    def _get_preset_key(self, encoder: str):
        if "x264" in encoder: return "x264"
        elif "x265" in encoder: return "x265"
        elif "AV1" in encoder: return "SVTAV1"
        return ""

    def build_video_kwargs(self, video_state: dict) -> list:
        """
        基于 UI 状态构造 ffmpeg-python 接受的 **kwargs 列表。
        如果是 1-pass, 返回 [kwargs]。
        如果是 2-pass, 返回 [pass1_kwargs, pass2_kwargs]。
        """
        encoder = video_state.get('encoder_format', 'Copy')
        
        if encoder not in self.config.get("Video", {}):
            return [{"vcodec": "copy"}]
            
        video_config = self.config["Video"][encoder]
        base_kwargs = video_config.get("base_kwargs", {}).copy()
        
        # --- 1. 手动自定义参数 (最高优先级，如果有则不再读取码率和选项) ---
        custom_options_str = video_state.get('custom_options', '').strip()
        custom_options_dict = {}
        if custom_options_str:
            tokens = shlex.split(custom_options_str)
            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t.startswith('-'):
                    k = t.lstrip('-')
                    # 检查下一个 token 是不是选项的值
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                        custom_options_dict[k] = tokens[i + 1]
                        i += 1
                    else:
                        # 单独的横线开关，在 ffmpeg-python 中传 None 参数即可输出无值 flag
                        custom_options_dict[k] = None 
                i += 1
            # 一旦识别文本框内有内容，直接应用这些高级命令并短路返回，不包含下方的 UI 配置和码率拉条
            return [{**base_kwargs, **custom_options_dict}]

        # --- 2. 使用预设逻辑 (覆盖其他设置) ---
        use_preset = video_state.get('using_preset', False)
        preset_name = video_state.get('using_preset_name', '')
        
        if use_preset and preset_name:
            preset_key = self._get_preset_key(encoder)
            if preset_key and preset_key in self.custom_preset_config:
                cli_str = self.custom_preset_config[preset_key].get(preset_name, "")
                if cli_str:
                    if preset_key == "x264":
                        parsed_params = NativeCliParser.parse_x264(cli_str)
                        if parsed_params: base_kwargs["x264-params"] = parsed_params
                    elif preset_key == "x265":
                        parsed_params = NativeCliParser.parse_x265(cli_str)
                        if parsed_params: base_kwargs["x265-params"] = parsed_params
                    elif preset_key == "SVTAV1":
                        parsed_params = NativeCliParser.parse_svtav1(cli_str)
                        if parsed_params: base_kwargs["svtav1-params"] = parsed_params
                    
            # 开启自定义预设后，不应用通用 UI 设置（即原厂策略：用预设就跳过常规拉条控制）
            return [base_kwargs]

        # --- 3. 码率与选项模板映射 ---
        rc_mode = video_state.get('rc_mode', '')
        # 如果是 NVEnc, 它的 rc_mode 名称叫 "恒定质量 (CQ)"
        # 我们做一个简单的容错以适应名称波动
        if 'CRF' in rc_mode or 'CQP' in rc_mode or 'ICQ' in rc_mode or 'CQ' in rc_mode:
            real_rc_keys = [k for k in video_config.get("rate_control", {}).keys() if 'CRF' in k or 'CQP' in k or 'ICQ' in k or 'CQ' in k]
            if real_rc_keys:
                rc_mode = real_rc_keys[0]

        rc_config = video_config.get("rate_control", {})
        
        format_data = SafeFormatDict({
            "quality_val": video_state.get("quality_val", 20),
            "bitrate": video_state.get("bitrate", 1000),
            "preset_name": video_state.get("preset_name", ""),
            "preset_val": video_state.get("preset_val", ""),
            "profile_name": video_state.get("profile_name", ""),
            "level_val": video_state.get("level_val", ""),
            "tuning_name": video_state.get("tuning_name", "")
        })

        is_2pass = video_state.get('is_2pass', False)
        
        options_kwargs = {}
        for key, map_pattern in video_config.get("options", {}).items(): 
            ui_val = None
            if encoder in ["AVC (NVEnc)", "HEVC (NVEnc)"] and key == "presets":
                ui_val = video_state.get("preset_val")
            elif key == "presets": ui_val = video_state.get("preset_name")
            elif key == "profiles": ui_val = video_state.get("profile_name")
            elif key == "levels": ui_val = video_state.get("level_val")
            elif key == "tune": ui_val = video_state.get("tuning_name")
            
            if ui_val is not None and str(ui_val).lower() not in ["none", "auto", ""]:
                for k, v in map_pattern.items(): 
                    options_kwargs[k] = str(v).format_map(format_data)

        # --- 4. 2-pass / 1-pass 流转 ---
        if is_2pass:
            if "2pass_1" in rc_config and "2pass_2" in rc_config:
                pass1_kwargs = {**base_kwargs, **options_kwargs}
                pass2_kwargs = {**base_kwargs, **options_kwargs}
                if rc_mode in rc_config:
                    for k, v in rc_config[rc_mode].items():
                        pass1_kwargs[k] = str(v).format_map(format_data)
                        pass2_kwargs[k] = str(v).format_map(format_data)

                for k, v in rc_config["2pass_1"].items():
                    pass1_kwargs[k] = str(v).format_map(format_data)
                for k, v in rc_config["2pass_2"].items():
                    pass2_kwargs[k] = str(v).format_map(format_data)
                    
                return [pass1_kwargs, pass2_kwargs]
            elif "2pass" in rc_config:
                # 例如 NVEnc 的 -multipass 2
                kw = {**base_kwargs, **options_kwargs}
                if rc_mode in rc_config:
                    for k, v in rc_config[rc_mode].items():
                        kw[k] = str(v).format_map(format_data)
                for k, v in rc_config["2pass"].items():
                    kw[k] = str(v).format_map(format_data)
                return [kw]

        # 1-pass
        kw = {**base_kwargs, **options_kwargs}
        if rc_mode in rc_config:
            for k, v in rc_config[rc_mode].items():
                kw[k] = str(v).format_map(format_data)
                
        return [kw]

    def build_audio_kwargs(self, audio_state: dict) -> tuple:
        """
        基于 UI 状态构造 ffmpeg-python 接受的音频 **kwargs 字典和专用容器格式。
        返回: (kwargs_dict, container_str)
        """
        encoder = audio_state.get('encoder_format', 'Copy')
        
        if encoder == 'Copy' or encoder not in self.config.get("Audio", {}):
            # 获取 Copy 对应的字典配置，如果没有就默认空
            copy_cfg = self.config.get("Audio", {}).get("Copy", {})
            return {"acodec": "copy"}, copy_cfg.get("container", "")
            
        audio_config = self.config["Audio"][encoder]
        base_kwargs = audio_config.get("base_kwargs", {}).copy()
        container = audio_config.get("container", "")
        
        # --- 1. 参数与常规选项映射 ---
        rc_mode = audio_state.get('rc_mode', '')
        rc_config = audio_config.get("rate_control", {})
        
        format_data = SafeFormatDict({
            "bitrate": audio_state.get("bitrate", 128),
            "quality_val": audio_state.get("quality_val", 2),
            "sample_rate": audio_state.get("sample_rate", "44100"),
            "channels": audio_state.get("channels", "2")
        })
        
        kw = {**base_kwargs}
        if rc_mode in rc_config:
            for k, v in rc_config[rc_mode].items():
                # 兼容 json 中的 "-b:a" 这类带横杠的写法，ffmpeg-python kwargs不需要横杠
                clean_k = k.lstrip('-')
                kw[clean_k] = str(v).format_map(format_data)
                
        for key, map_pattern in audio_config.get("options", {}).items():
            ui_val = audio_state.get(key)
            if ui_val and str(ui_val).lower() not in ["none", "auto", "original", "原轨", "自动"]:
                for k, v in map_pattern.items():
                    clean_k = k.lstrip('-')
                    kw[clean_k] = str(v).format_map(format_data)
                    
        return kw, container

    def build_image_kwargs(self, image_state: dict) -> tuple:
        """
        基于 UI 状态构造 ffmpeg-python 接受的图片 **kwargs 字典和专用容器格式。
        """
        encoder = image_state.get('encoder_format', 'Copy')
        
        if encoder == 'Copy' or encoder not in self.config.get("Image", {}):
            copy_cfg = self.config.get("Image", {}).get("Copy", {})
            return {"vcodec": "copy"}, copy_cfg.get("container", "")
            
        img_config = self.config["Image"][encoder]
        base_kwargs = img_config.get("base_kwargs", {}).copy()
        container = img_config.get("container", "")
        
        format_data = SafeFormatDict({
            "quality_val": image_state.get("quality_val", 80),
            "width": image_state.get("width", 0),
            "height": image_state.get("height", 0)
        })
        
        kw = {**base_kwargs}
        
        # --- 1. 画质与无损模式映射 ---
        is_lossless = image_state.get("is_lossless", False)
        if is_lossless and "lossless" in img_config:
            for k, v in img_config["lossless"].items():
                kw[k.lstrip('-')] = str(v).format_map(format_data)
        elif "quality" in img_config:
            for k, v in img_config["quality"].items():
                kw[k.lstrip('-')] = str(v).format_map(format_data)
                
        # --- 2. 图片尺寸与基础效果滤镜映射 (Image_filters) ---
        enable_base_process = image_state.get("enbale_base_process", False)
        if enable_base_process:
            vf_list = []
            filters_cfg = self.config.get("Image_filters", {})
            
            tgt_width = image_state.get("crop_w")
            tgt_height = image_state.get("crop_h")
            orig_width = image_state.get("original_w")
            orig_height = image_state.get("original_h")
            
            # (1) 裁切与缩放控制
            if tgt_width and tgt_height:
                try:
                    t_w = int(tgt_width)
                    t_h = int(tgt_height)
                    o_w = int(orig_width) if orig_width else 0
                    o_h = int(orig_height) if orig_height else 0
                    
                    if o_w and o_h and (o_w < t_w or o_h < t_h):
                        # 分辨率不足需要缩放填充
                        cmd_list = filters_cfg.get("crop_dimension_resize", [])
                    else:
                        # 分辨率足够则直接裁切
                        cmd_list = filters_cfg.get("crop_dimension_resize", [])
                        
                    if cmd_list:
                        # 这里要注意 format_data 里的键名得能匹配上 json 里的 {width} 和 {height}
                        # 因此我们临时往 format_data 塞入这两个直观的键
                        format_data["width"] = t_w
                        format_data["height"] = t_h
                        vf_list.append(str(cmd_list[0]).format_map(format_data))
                except ValueError:
                    pass
                    
            # (2) 旋转控制
            rotate_val = image_state.get("rotate", "")
            if rotate_val and rotate_val not in ["无", "None", "", "none"]:
                if rotate_val in filters_cfg.get("rotate", {}):
                    vf_list.append(filters_cfg["rotate"][rotate_val])
                    
            # (3) 翻转控制
            flip_val = image_state.get("flip", "")
            if flip_val and flip_val not in ["无", "None", "", "none"]:
                if flip_val in filters_cfg.get("flip", {}):
                    vf_list.append(filters_cfg["flip"][flip_val])
                    
            if vf_list:
                kw["vf"] = ",".join(vf_list)
                
        return kw, container

    def build_subtitle_kwargs(self, subtitle_state: dict) -> tuple:
        """
        基于 UI 状态构造 ffmpeg-python 接受的字幕 **kwargs 字典和专用容器格式。
        """
        encoder = str(subtitle_state.get('encoder_format', '')).lower()
        container = self.config.get("Subtitle", {}).get(encoder, {}).get("container", "")
        return {}, container