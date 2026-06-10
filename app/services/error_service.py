# coding: utf-8
"""AME 错误服务 — 将 CLI 工具的错误输出翻译为用户友好提示"""
import re


class ErrorService:

    @classmethod
    def ffmpeg_error(cls, err_msg: str):
        """从 FFmpeg 的错误输出中提取核心错误信息, 并提供针对常见错误的提示"""
        lines = [line.strip() for line in err_msg.splitlines() if line.strip()]

        # 过滤 FFmpeg 级联崩溃产生的通用错误，暴露出最前面的真实原因
        generic_errors = [
            "Error while opening encoder",
            "Generic error in an external library",
            "Task finished with error code",
            "Terminating thread with return code",
            "Could not open encoder before EOF",
            "Nothing was written into output file",
            "Error sending frames to consumers",
            "Invalid argument",
            "Conversion failed!",
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

        hint = cls._match_hint(short_err)
        return hint if hint else short_err

    @classmethod
    def cli_error(cls, tool: str, stderr: str):
        """x264/x265/qaac/mkvmerge/vspipe 通用 CLI 错误提取
        返回: 中文错误提示 + 关键原文片段
        """
        if not stderr:
            return f"{tool} 执行失败，无错误输出。请检查节点设置或查看日志"

        lines = [l.strip() for l in stderr.splitlines() if l.strip()]
        if not lines:
            return f"{tool} 执行失败，请检查节点设置或查看日志"

        # 取最后 3 行作为关键错误
        tail = "\n".join(lines[-3:])
        hint = cls._match_hint(tail)

        if hint:
            return hint
        else:
            # 未匹配到已知模式，截取最后 150 字符
            snippet = tail[-150:] if len(tail) > 150 else tail
            return f"{snippet}\n\n详情请查看 logs/ame_run.log"

    @classmethod
    def _match_hint(cls, text: str):
        """根据错误文本匹配已知错误模式，返回中文提示"""
        t = text.lower()

        if "10 bit encode not supported" in t:
            return "所选视频编码器不支持 10 bit, 请更换编码器或降低位深"
        if "could not write header (incorrect codec parameters ?)" in t:
            return "编码参数与容器不兼容，请更换编码器或容器格式"
        if "no capable devices found" in t:
            return "未找到可用的硬件加速设备"
        if "no such file or directory" in t:
            return "输入文件或预设路径不存在"
        if "unrecognized option" in t or "unknown option" in t:
            return "CLI 命令中有未知的参数选项，请检查自定义参数"
        if "unknown encoder" in t or "invalid encoder" in t:
            return "当前版本不支持该编码器，请更换编码器"
        if "could not open" in t or "cannot open" in t:
            return "输入文件不存在或路径错误"
        if "permission denied" in t:
            return "文件访问权限不足"
        if "not supported" in t:
            return "输入格式不受支持，请检查输入文件"
        if "broken pipe" in t or "error writing" in t:
            return "管道连接中断 (vspipe)，上游进程异常退出"
        if "invalid data found when processing input" in t:
            return "输入文件已损坏或格式不正确"
        if "out of memory" in t:
            return "系统内存不足，请关闭其他程序后重试"
        if "error while decoding" in t:
            return "解码输入文件时出错，文件可能已损坏"
        if "error while encoding" in t:
            return "编码过程出错，请检查编码器参数"
        if "conversion failed" in t:
            return "转换失败，请检查节点设置或查看日志"
        if "returncode=1" in t or "return code 1" in t:
            return "执行返回错误码 1，请检查节点设置或查看日志"
        return None

    @classmethod
    def format_node_error(cls, node_name: str, detail: str):
        """格式化节点错误信息，供 InfoBar 显示"""
        msg = f"节点『{node_name}』执行失败"
        if detail:
            detail_short = detail[:200] + "…" if len(detail) > 200 else detail
            msg += f"\n{detail_short}"
        else:
            msg += "，请检查节点设置或查看日志"
        return msg
