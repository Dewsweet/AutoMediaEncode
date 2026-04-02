# coding: utf-8
import subprocess
import logging

class HWDetectService:
    """
    底层硬件检测单例。
    在程序启动时静默运行WMI命令，极速检测当前计算机搭载的显卡厂商。
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HWDetectService, cls).__new__(cls)
            cls._instance._vendors = cls._instance._detect_gpus()
        return cls._instance

    def _detect_gpus(self):
        """
        利用 WMI 命令极速查询显卡厂商
        """
        vendors = set()
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # wmic 会返回类似 "NVIDIA GeForce RTX 3060" 或 "Intel(R) UHD Graphics" 等字符串
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, errors='ignore', startupinfo=startupinfo, timeout=3
            )
            output = result.stdout.upper()
            
            if "NVIDIA" in output:
                vendors.add("NVIDIA")
            if "INTEL" in output:
                vendors.add("INTEL")
            # 兼容 AMD 或 Radeon 的叫法
            if "AMD" in output or "RADEON" in output:
                vendors.add("AMD")
                
        except Exception as e:
            logging.error(f"Hardware detection failed: {e}")
            
        return vendors

    def get_supported_video_encoders(self, all_encoders: list) -> list:
        """
        根据检测到的硬件，过滤不支持的视频编码器 UI 选项。
        传入全量的下拉框列表，返回安全可用的下拉框列表。
        
        例如传入: ["Copy", "AVC (x264)", "AVC (NVEnc)", "AVC (QSV)", "AVC (VCE)"]
        如果没检测到 NVIDIA 显卡，"AVC (NVEnc)" 就会被剔除。
        """
        supported = []
        for enc in all_encoders:
            # 判断硬件加速特征词
            if "NVEnc" in enc:
                if "NVIDIA" in self._vendors:
                    supported.append(enc)
            elif "QSV" in enc:
                if "INTEL" in self._vendors:
                    supported.append(enc)
            elif "VCE" in enc or "AMF" in enc:
                if "AMD" in self._vendors:
                    supported.append(enc)
            else:
                # 没有任何上述硬件标记的，皆视为纯 CPU 或者是 Copy 一定支持
                supported.append(enc)
                
        return supported

# 提供一个便捷的实例供全局调用
hw_detect_service = HWDetectService()
