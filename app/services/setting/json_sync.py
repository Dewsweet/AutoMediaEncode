# coding: utf-8
"""
JSON 预设同步工具 — 模板向用户配置"补缺"合并

设计原则:
- 用户数据至上: 合并只做加法, 模板新增键自动下发, 用户已有值永远优先, 永不删除用户键
- 损坏自愈: 用户 JSON 损坏时备份为 .bak 后从模板重建, 不再静默丢失
- 原子写入: 临时文件 + os.replace, 避免写入中断产生半截文件
"""
import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from ...common.logger import logger


def deep_merge_presets(template: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    逐键递归合并: 模板键补缺, 用户值优先, 永不删除用户键。
    返回合并结果, 不修改入参字典。
    """
    merged = dict(user)
    for key, t_value in template.items():
        if key not in merged:
            # 深拷贝模板值, 避免与模板共享可变对象
            merged[key] = json.loads(json.dumps(t_value))
        elif isinstance(t_value, dict) and isinstance(merged[key], dict):
            merged[key] = deep_merge_presets(t_value, merged[key])
        # 类型不一致或非 dict: 用户值优先, 保留不动
    return merged


def atomic_write_json(path: Path, data: Dict[str, Any]) -> bool:
    """原子写入 JSON: 先写 .tmp 再 os.replace, 失败时清理临时文件。"""
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, path)
        return True
    except Exception as e:
        logger.warning(f"原子写入 JSON 失败: {path} - {e}")
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
        return False


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    """读取 JSON, 解析失败或顶层不是 dict 时返回 None"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def sync_preset_json(template_path: Path, user_path: Path) -> bool:
    """
    同步单个预设 JSON (模板 → 用户):
    - 用户文件缺失: 直接复制模板
    - 用户文件损坏: 备份为 .bak 后从模板重建
    - 均有效: 深合并模板补缺, 内容无变化则跳过写回
    """
    template = _load_json(template_path) if template_path.exists() else None
    if template is None:
        # 没有可用模板时不动用户文件
        return user_path.exists() and _load_json(user_path) is not None

    user = None
    if user_path.exists():
        user = _load_json(user_path)
        if user is None:
            # 损坏自愈: 备份原文件保留抢救可能性, 再从模板重建
            bak_path = user_path.with_suffix(user_path.suffix + '.bak')
            try:
                shutil.copy2(user_path, bak_path)
                logger.warning(f"用户预设 JSON 损坏, 已备份到 {bak_path} 并从模板重建")
            except Exception as e:
                logger.warning(f"备份损坏的预设 JSON 失败: {e}")
            user = None

    if user is None:
        return atomic_write_json(user_path, template)

    merged = deep_merge_presets(template, user)
    if merged != user:
        return atomic_write_json(user_path, merged)
    return True


def sync_template_dir(template_dir: Path, user_dir: Path,
                      deleted_marker: Optional[Path] = None) -> None:
    """
    按文件名补缺同步模板目录 → 用户目录:
    - 仅复制用户目录中不存在的模板文件
    - deleted_marker 中记录的文件名视为用户已主动删除, 跳过不复活
    """
    if not template_dir.exists():
        return
    user_dir.mkdir(parents=True, exist_ok=True)

    deleted = _load_deleted_names(deleted_marker)

    for f in template_dir.glob('*.json'):
        # '_' 开头的文件视为服务内部文件, 不作为出厂预设同步
        if f.name.startswith('_') or f.stem in deleted or f.name in deleted:
            continue
        dst = user_dir / f.name
        if not dst.exists():
            try:
                shutil.copy2(f, dst)
                logger.info(f"同步出厂模板到用户配置: {f.name}")
            except Exception as e:
                logger.warning(f"复制出厂模板失败: {f.name} - {e}")


def record_deleted_template(deleted_marker: Path, name: str) -> None:
    """记录用户删除的出厂模板名, 防止下次启动补缺同步时复活"""
    deleted = _load_deleted_names(deleted_marker)
    if name not in deleted:
        deleted.append(name)
        atomic_write_json(deleted_marker, {"deleted": deleted})


def _load_deleted_names(deleted_marker: Optional[Path]) -> list:
    """读取删除标记文件, 兼容 {"deleted": [...]} 与 [...] 两种历史格式"""
    if deleted_marker is None or not deleted_marker.exists():
        return []
    data = _load_json(deleted_marker)
    if isinstance(data, dict):
        names = data.get('deleted', [])
    else:
        return []
    return [n for n in names if isinstance(n, str)]
