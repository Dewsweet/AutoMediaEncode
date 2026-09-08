# coding:utf-8
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from ..path_service import PathService
from .json_sync import sync_preset_json, atomic_write_json

class PresetService:
    def __init__(self):
        # 确定根目录下的 config 文件夹作为用户数据的持久化存储地
        self._config_dir = PathService.get_config_dir()
        self._config_dir.mkdir(parents=True, exist_ok=True) 
        
        self.preset_file_path = self._config_dir / "custom_preset.json" 
        self._ensure_preset_file_exists()

    def _ensure_preset_file_exists(self):
        """
        初始化检查：将出厂模板同步到用户的 config 目录。
        - 用户文件缺失: 复制模板
        - 用户文件损坏: 备份为 .bak 后从模板重建
        - 均有效: 深合并模板新增键, 用户已有值永远优先
        防止覆盖安装/软件更新丢失或污染用户数据。
        """
        template_path = PathService.get_json_dir() / "custom_preset.json"
        sync_preset_json(template_path, self.preset_file_path)

        # 极端情况: 模板不存在且用户文件也没有, 创建一个空的出厂结构
        if not self.preset_file_path.exists():
            default_data = {
                "_Notes" : "编码器参数预设置",
                "x264": {},
                "x265": {},
                "SVTAV1": {}
            }
            self.save_all_presets(default_data)

    def load_all_presets(self) -> Dict[str, Any]:
        """
        读取所有预设
        返回一个字典，结构大致如下：
        {
            "x264": {
                "preset1": "参数字符串",
                "preset2": "参数字符串",
                ...
            }
        }
        """
        try:
            with open(self.preset_file_path, "r", encoding="utf-8") as f:
                return json.load(f) 
        except Exception:
            # 读取失败(文件损坏/被删): 触发同步逻辑自愈, 备份损坏文件并从模板重建
            logger.warning("读取用户预设 JSON 失败, 触发自愈重建")
            self._ensure_preset_file_exists()
            try:
                with open(self.preset_file_path, "r", encoding="utf-8") as f:
                    return json.load(f) 
            except Exception:
                return {"x264": {}, "x265": {}, "SVTAV1": {}}

    def save_all_presets(self, data: Dict[str, Any]) -> bool:
        """保存所有预设回 JSON (原子写入, 避免中断产生半截文件)"""
        return atomic_write_json(self.preset_file_path, data)

    def get_presets_by_encoder(self, encoder_name: str) -> Dict[str, str]:
        """获取指定编码器 (如 'x264') 的所有预设"""
        data = self.load_all_presets()
        return data.get(encoder_name, {})

    def get_default_presets_by_encoder(self, encoder_name: str) -> Dict[str, str]:
        """获取指定编码器的出厂默认预设"""
        template_path = PathService.get_json_dir() / "custom_preset.json"
        
        if template_path.exists():
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    default_data = json.load(f)
                    return default_data.get(encoder_name, {})
            except Exception:
                return {}
        return {}

    def add_or_update_preset(self, encoder_name: str, preset_name: str, params: str):
        """添加或更新某个编码器的具体条目"""
        data = self.load_all_presets()
        if encoder_name not in data:
            data[encoder_name] = {}
        data[encoder_name][preset_name] = params
        self.save_all_presets(data)

    def delete_preset(self, encoder_name: str, preset_name: str):
        """删除某个预设"""
        data = self.load_all_presets()
        if encoder_name in data and preset_name in data[encoder_name]:
            del data[encoder_name][preset_name]
            self.save_all_presets(data)

# 单例模式，全局复用
preset_service = PresetService()