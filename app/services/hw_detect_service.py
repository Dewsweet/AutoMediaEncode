# coding: utf-8
import subprocess
import sys
from ..common.logger import logger

class HWDetectService:
    """
    底层硬件检测单例。跨平台支持 (Windows/macOS/Linux)。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HWDetectService, cls).__new__(cls)
            # 初始化为空，真正的检测延迟到第一次调用时（懒加载）
            cls._instance._vendors = None  
            cls._instance._raw_info = ""   # 保存显卡具体型号用于日志排错
            
            cls._instance._accel_rules = {
                "NVENC": "NVIDIA",
                "QSV": "INTEL",
                "AMF": "AMD",
                "VCE": "AMD",
                "VIDEOTOOLBOX": "APPLE" # Mac 原生加速
            }
        return cls._instance

    def _ensure_detected(self):
        """每次启动仅检测一次，后续调用直接返回缓存结果"""
        if self._vendors is not None:
            return
            
        logger.info("[HWDetect] 正在执行硬件环境检测...")
        output = ""
        try:
            if sys.platform == "win32":
                output = self._detect_windows()
            elif sys.platform == "darwin":
                output = self._detect_macos()
            elif sys.platform.startswith("linux"):
                output = self._detect_linux()
        except Exception as e:
            logger.error(f"[HWDetect] 硬件检测发生异常: {e}")
            
        self._raw_info = output.strip().replace('\n', ' | ')
        self._vendors = self._parse_vendors(output)
        logger.info(f"[HWDetect] 发现显卡设备: {self._raw_info if self._raw_info else '未知'}")

    def get_gpu_info(self) -> str:
        """获取检测到的显卡信息字符串，用于日志排错"""
        self._ensure_detected()
        return self._raw_info

    def get_supported_video_encoders(self, all_encoders: list) -> list:
        """
        根据检测到的硬件，过滤不支持的视频编码器 UI 选项。
        传入全量的下拉框列表，返回安全可用的下拉框列表。
        """
        self._ensure_detected() # 第一次调用时触发真实检测
        
        supported = []
        for enc in all_encoders:
            enc_upper = enc.upper()
            is_supported = True
            
            # 遍历所有的规则，看当前编码器名称是否命中了某个硬件加速后缀
            for suffix, required_vendor in self._accel_rules.items():
                if suffix in enc_upper:
                    # 命中了规则，检查电脑是否搭载了对应的显卡
                    if required_vendor == "APPLE":
                        # 特殊处理 Mac，只要是 darwin 系统就放行 VideoToolbox
                        is_supported = (sys.platform == "darwin")
                    else:
                        is_supported = (required_vendor in self._vendors)
                    break # 找到规则后跳出规则匹配

            if is_supported:
                supported.append(enc)
                
        return supported


    def _detect_windows(self) -> str:
        """Windows 下优先使用注册表查询，速度最快且无编码问题，兼容 Win11"""
        # 1. 首选方案：读取系统注册表 (最稳定)
        try:
            import winreg
            gpu_list = []
            # Windows 显示适配器的标准 GUID
            key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                for i in range(100): # 遍历可能的子项
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        if subkey_name.lower() == "properties": 
                            continue
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                desc, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                                if desc:
                                    gpu_list.append(desc)
                            except FileNotFoundError:
                                pass
                    except OSError:
                        break # 没有更多子项了
            if gpu_list:
                return "\n".join(gpu_list)
        except Exception as e:
            logger.debug(f"[HWDetect] 注册表读取显卡失败，尝试备用方案: {e}")

        # 2. 备用方案：PowerShell (强制指定 UTF-8 编码，防止中文系统乱码被 ignore 吞掉)
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000) # 更现代的隐藏黑框方法
        try:
            cmd = [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', creationflags=creationflags, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
        except Exception:
            pass
            
        # 3. 最终兜底方案：WMIC (在较新的 Win11 中可能已不存在)
        try:
            cmd_fallback = ["wmic", "path", "win32_VideoController", "get", "name"]
            res = subprocess.run(cmd_fallback, capture_output=True, text=True, errors='ignore', creationflags=creationflags, timeout=3)
            return res.stdout
        except Exception:
            return ""

    def _detect_macos(self) -> str:
        cmd = ["system_profiler", "SPDisplaysDataType"]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=3)
        return res.stdout

    def _detect_linux(self) -> str:
        cmd = ["lspci"]
        res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=3)
        gpu_lines = [line for line in res.stdout.splitlines() if "VGA" in line or "3D" in line or "Display" in line]
        return "\n".join(gpu_lines)

    def _parse_vendors(self, output: str) -> set:
        vendors = set()
        output = output.upper()
        if "NVIDIA" in output: vendors.add("NVIDIA")
        if "INTEL" in output: vendors.add("INTEL")
        if "AMD" in output or "RADEON" in output or "ADVANCED MICRO DEVICES" in output: vendors.add("AMD")
        if "APPLE" in output: vendors.add("APPLE")
        return vendors

# 提供全局单例
hw_detect_service = HWDetectService()