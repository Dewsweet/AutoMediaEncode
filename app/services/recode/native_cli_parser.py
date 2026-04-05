# coding: utf-8
import shlex

class NativeCliParser:
    """
    负责将原生编码器 (x264, x265, SVT-AV1) 的 CLI 参数字符串
    转换为 FFmpeg 接受的 -<encoder>-params 键值对格式 (key=val:key=val)
    """

    # --- 黑名单配置区 ---
    # 填入 FFmpeg 不接受、或者会与 FFmpeg 基础命令冲突的原生参数名。
    # 比如我们已知有些参数在 libx264wrapper 中并不直接暴露，可以填在这里过滤掉。
    X264_IGNORE_LIST = {
        # 'example-param'
    }

    X265_IGNORE_LIST = {
        # 'example-param'
    }

    SVTAV1_IGNORE_LIST = {
        # 'example-param'
    }

    @classmethod
    def _parse_generic(cls, cli_str: str, ignore_list: set) -> str:
        if not cli_str.strip():
            return ""

        # 使用 shlex 安全分割，防止引号里面的空格被打断
        # 兼容例如 --aq-mode "1" 这样的写法
        tokens = shlex.split(cli_str)
        
        params = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # 我们只处理以 -- 开头的标准化参数
            if token.startswith("--"):
                raw_key = token[2:]  # 去掉 '--'
                
                # 1. 处理 --no-xxx 格式，转变为 xxx=0
                if raw_key.startswith("no-"):
                    key = raw_key[3:]
                    val = "0"
                else:
                    key = raw_key
                    # 看下一个 token 是否是值 (不能以 -- 开头，且不越界)
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                        val = tokens[i + 1]
                        i += 1  # 消耗掉 value
                    else:
                        val = "1" # 单独的开关，例如 --weightb 转为 weightb=1
                
                # 过滤不需要的参数
                if key not in ignore_list and raw_key not in ignore_list:
                    params.append(f"{key}={val}")
            
            i += 1
            
        return ":".join(params)

    @classmethod
    def parse_x264(cls, cli_str: str) -> str:
        return cls._parse_generic(cli_str, cls.X264_IGNORE_LIST)

    @classmethod
    def parse_x265(cls, cli_str: str) -> str:
        return cls._parse_generic(cli_str, cls.X265_IGNORE_LIST)

    @classmethod
    def parse_svtav1(cls, cli_str: str) -> str:
        return cls._parse_generic(cli_str, cls.SVTAV1_IGNORE_LIST)
