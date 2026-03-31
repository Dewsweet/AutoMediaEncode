# coding:utf-8
import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any

from .path_service import PathService

class PresetService:
    def __init__(self):
        # 确定根目录下的 config 文件夹作为用户数据的持久化存储地
        self._config_dir = Path("app/config") 
        self._config_dir.mkdir(parents=True, exist_ok=True) 
        
        self.preset_file_path = self._config_dir / "custom_preset.json" 
        self._ensure_preset_file_exists()

    def _ensure_preset_file_exists(self):
        """
        初始化检查：如果在用户的 config 目录下没有该字典，
        则从内部持有的 "出厂模板" 中复制一份过去，防止覆盖安装丢失用户数据。
        """
        if not self.preset_file_path.exists():
            # 获取代码目录里的初始模板
            template_path = PathService.get_common_dir() / "Json" / "custom_preset.json"
            if template_path.exists():
                shutil.copy2(template_path, self.preset_file_path)
            else:
                # 极端情况下如果连模板都没有，就创建一个空的（按原来字典结构）
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
            return {"x264": {}, "x265": {}, "SVTAV1": {}}

    def save_all_presets(self, data: Dict[str, Any]) -> bool:
        """保存所有预设回 JSON"""
        try:
            with open(self.preset_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Error saving preset: {e}")
            return False

    def get_presets_by_encoder(self, encoder_name: str) -> Dict[str, str]:
        """获取指定编码器 (如 'x264') 的所有预设"""
        data = self.load_all_presets()
        return data.get(encoder_name, {})

    def get_default_presets_by_encoder(self, encoder_name: str) -> Dict[str, str]:
        """获取指定编码器的出厂默认预设"""
        template_path = PathService.get_common_dir() / "Json" / "custom_preset.json"
        
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