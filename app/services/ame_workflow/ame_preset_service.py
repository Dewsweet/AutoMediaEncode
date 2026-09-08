"""AME 工作流预设管理服务 — 单例"""
import json, shutil, os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from ..path_service import PathService
from ..setting.json_sync import sync_template_dir, record_deleted_template


@dataclass
class WorkflowInfo:
    name: str
    json_path: Path
    modified: datetime
    node_count: int = 0
    thumbnail: Path | None = None


class AMEPresetService:
    def __init__(self):
        self._template_dir = PathService.get_json_dir() / "ame_preset"
        self._user_dir = PathService.get_config_dir() / "ame_preset"
        # 删除标记放在用户预设目录之外, 避免被 list_workflows 的 *.json 遍历误认为工作流
        self._deleted_marker = PathService.get_config_dir() / "ame_preset_deleted.json"
        self._manual_thumbs = set()  # 手动设置过封面的工作流名，不再自动截图
        self._init_dirs()

    def _init_dirs(self):
        """确保用户预设目录存在, 并按文件名补缺同步出厂模板:
        - 用户目录缺失的出厂工作流自动补充 (软件更新新增模板可送达)
        - 用户已删除的出厂工作流记录在删除标记中, 不会复活
        """
        sync_template_dir(self._template_dir, self._user_dir, self._deleted_marker)

    def list_workflows(self) -> list:
        """列出所有用户预设的工作流，按修改时间倒序"""
        result = []
        for f in sorted(self._user_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True):
            info = WorkflowInfo(
                name=f.stem,
                json_path=f,
                modified=datetime.fromtimestamp(f.stat().st_mtime),
            )
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                info.node_count = len(data.get('nodes', {}))
            except Exception:
                pass
            thumb = self._user_dir / f"{f.stem}.png"
            if thumb.exists():
                info.thumbnail = thumb
            result.append(info)
        return result

    def save(self, name: str, graph) -> Path:
        """保存工作流到用户预设目录，返回 JSON 文件路径"""
        json_path = self._user_dir / f"{name}.json"
        graph.save_session(str(json_path))
        return json_path

    def save_with_thumbnail(self, name: str, graph) -> Path:
        """保存并自动截图。手动封面不为空时跳过自动截图"""
        json_path = self.save(name, graph)
        if name not in self._manual_thumbs:
            self._make_thumbnail(graph, name)
        return json_path

    def load(self, name: str, graph) -> bool:
        json_path = self._user_dir / f"{name}.json"
        if not json_path.exists():
            return False
        graph.clear_session()
        graph.load_session(str(json_path))
        return True

    def delete(self, name: str):
        for ext in ('.json', '.png'):
            p = self._user_dir / f"{name}{ext}"
            if p.exists():
                p.unlink()
        # 若删除的是出厂模板同名工作流, 记录删除标记, 防止下次启动补缺同步时复活
        if (self._template_dir / f"{name}.json").exists():
            record_deleted_template(self._deleted_marker, name)

    def rename(self, old: str, new: str):
        for ext in ('.json', '.png'):
            src = self._user_dir / f"{old}{ext}"
            dst = self._user_dir / f"{new}{ext}"
            if src.exists():
                src.rename(dst)
        # 若重命名的原名对应出厂模板, 记录原名删除标记:
        # 否则下次启动补缺同步会因用户目录缺少原同名文件而把模板以原名复活,
        # 且重命名后的工作流再被删除时, 原名模板同样会复活
        if (self._template_dir / f"{old}.json").exists():
            record_deleted_template(self._deleted_marker, old)

    def import_file(self, path: str) -> str | None:
        src = Path(path)
        if not src.exists():
            return None
        name = src.stem
        base = name
        counter = 1
        while (self._user_dir / f"{name}.json").exists():
            name = f"{base}_{counter}"
            counter += 1
        dst = self._user_dir / f"{name}.json"
        shutil.copy2(src, dst)
        return name

    def export(self, name: str, path: str):
        src = self._user_dir / f"{name}.json"
        if src.exists():
            shutil.copy2(src, Path(path))

    def set_thumbnail(self, name: str, img_path: str):
        dst = self._user_dir / f"{name}.png"
        shutil.copy2(img_path, dst)
        self._manual_thumbs.add(name)  # 标记手动封面，不再自动截图

    def _make_thumbnail(self, graph, name: str):
        """尝试从 graph 截图并保存为预设缩略图，失败则静默忽略"""
        try:
            pixmap = graph.widget.grab()
            scaled = pixmap.scaled(320, 200,
                __import__('PySide6.QtCore', fromlist=['Qt']).Qt.KeepAspectRatio,
                __import__('PySide6.QtCore', fromlist=['Qt']).Qt.SmoothTransformation)
            scaled.save(str(self._user_dir / f"{name}.png"))
        except Exception:
            pass


preset_service = AMEPresetService()
