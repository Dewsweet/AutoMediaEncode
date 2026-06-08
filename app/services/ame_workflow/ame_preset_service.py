"""AME 工作流预设管理服务 — 单例"""
import json, shutil, os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


@dataclass
class WorkflowInfo:
    name: str
    json_path: Path
    modified: datetime
    node_count: int = 0
    thumbnail: Path | None = None


class AMEPresetService:
    def __init__(self):
        self._template_dir = Path(__file__).parent.parent.parent / 'common' / 'json' / 'ame_preset'
        self._user_dir = Path(__file__).parent.parent.parent / 'config' / 'ame_preset'
        self._init_dirs()

    def _init_dirs(self):
        self._user_dir.mkdir(parents=True, exist_ok=True)
        if self._template_dir.exists() and not any(self._user_dir.glob('*.json')):
            for f in self._template_dir.glob('*.json'):
                shutil.copy2(f, self._user_dir / f.name)

    def list_workflows(self) -> list:
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
        json_path = self._user_dir / f"{name}.json"
        graph.save_session(str(json_path))
        self._save_thumbnail(graph, name)
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

    def rename(self, old: str, new: str):
        for ext in ('.json', '.png'):
            src = self._user_dir / f"{old}{ext}"
            dst = self._user_dir / f"{new}{ext}"
            if src.exists():
                src.rename(dst)

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

    def _save_thumbnail(self, graph, name: str):
        try:
            pixmap = graph.widget.grab()
            scaled = pixmap.scaled(320, 200,
                __import__('PySide6.QtCore', fromlist=['Qt']).Qt.KeepAspectRatio,
                __import__('PySide6.QtCore', fromlist=['Qt']).Qt.SmoothTransformation)
            scaled.save(str(self._user_dir / f"{name}.png"))
        except Exception:
            pass


preset_service = AMEPresetService()
