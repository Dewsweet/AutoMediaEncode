# coding: utf-8
class ErrorService:
    @classmethod
    def ffmpeg_error(cls, err_msg: str):
        """从FFmpeg的错误输出中提取核心错误信息, 并提供针对常见错误的提示"""
        lines = [line.strip() for line in err_msg.splitlines() if line.strip()] # 过滤掉空行和纯空白行
        
        # 过滤FFmpeg级联崩溃产生的"通用"废话错误，这样就能暴露出最前面的真实原因
        generic_errors = [
            "Error while opening encoder",
            "Generic error in an external library",
            "Task finished with error code",
            "Terminating thread with return code",
            "Could not open encoder before EOF",
            "Nothing was written into output file",
            "Error sending frames to consumers",
            "Invalid argument",
            "Conversion failed!"
        ]
        
        core_errors = []
        for line in lines:
            # 过滤掉统计信息行
            if "Qavg:" in line or "frame=" in line or "fps=" in line:
                continue
            
            # 排查是否属于级联崩溃废话
            if not any(g_err in line for g_err in generic_errors):
                # FFmpeg典型的日志格式 [模块名 @ 地址] 实际信息
                if line.startswith("[") and ("@" in line) and ("]" in line):
                    clean_msg = line.split("]", 1)[-1].strip()
                    if clean_msg:
                        core_errors.append(clean_msg)
        
        # 提取真正的核心报错（通常取最后过滤剩下的1~2条）
        if core_errors:
            short_err = "\n".join(core_errors[-2:])
        else:
            # 兜底查找
            fallback = [l for l in lines if any(k in l.lower() for k in ["error", "failed", "unrecognized", "invalid"])]
            if fallback:
                short_err = "\n".join(fallback[-2:])
            else:
                short_err = lines[-1] if lines else "发生未知错误"
        
        hint = ""
        if "10 bit encode not supported" in short_err:
            hint = "所选视频编码器不支持 10 bit, 请检查! "
        elif "Could not write header (incorrect codec parameters ?)" in short_err:
            hint = "参数配置错误, 更换编码器 或者 容器再次尝试! "
        elif "No capable devices found" in short_err:
            hint = "未找到可用的硬件加速设备! "
        elif "No such file or directory" in short_err:
            hint = "系统找不到输入文件或预设路径! "
        elif "Unrecognized option" in short_err:
            hint = "自定义FFmpeg命令中有未知的参数选项, 请检查拼写。"
        elif "Unknown encoder" in short_err or "Invalid encoder" in short_err:
            hint = "当前 FFmpeg 版本不支持该编码器。"

        if hint:
            return hint
        else:
            return short_err