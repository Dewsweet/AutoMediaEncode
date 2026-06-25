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
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', startupinfo=startupinfo, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
        except Exception:
            pass
            
        cmd_fallback = ["wmic", "path", "win32_VideoController", "get", "name"]
        res = subprocess.run(cmd_fallback, capture_output=True, text=True, errors='ignore', startupinfo=startupinfo, timeout=3)
        return res.stdout

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