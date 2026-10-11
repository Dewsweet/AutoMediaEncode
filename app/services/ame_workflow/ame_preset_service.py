"""AME 工作流预设管理服务 — 单例"""
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from ..path_service import PathService
from ..setting.json_sync import sync_template_dir, record_deleted_template
from ..output_service import safe_filename
from .workflow_serializer import load_workflow, read_workflow, save_workflow, write_workflow
from .thumbnail_service import cover_source, read_cover, encode_cover, write_cover
from PySide6.QtCore import QCoreApplication, Qt
from app.common.logger import logger


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
        self._cover_revisions = {}
        self.last_thumbnail_error = ''
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

    def validate_name(self, name: str) -> str:
        if not isinstance(name, str) or not name or name != name.strip():
            raise ValueError(QCoreApplication.translate('AMEPresetService', '请输入有效的工作流名称'))
        safe_filename(name)
        safe_filename(f'{name}.json')
        if len(f'{name}.json'.encode('utf-16-le')) // 2 > 255:
            raise ValueError(QCoreApplication.translate('AMEPresetService', '工作流名称过长'))
        return name

    def _path(self, name: str, suffix='.json') -> Path:
        name = self.validate_name(name)
        root = self._user_dir.resolve()
        path = root / f'{name}{suffix}'
        if path.is_symlink() or path.resolve().parent != root:
            raise ValueError(QCoreApplication.translate('AMEPresetService', '工作流路径超出预设目录'))
        return path

    def exists(self, name: str) -> bool:
        return self._path(name).exists() or self._path(name, '.png').exists()

    def save(self, name: str, graph, *, overwrite=True) -> Path:
        """保存工作流到用户预设目录，返回 JSON 文件路径"""
        json_path = self._path(name)
        if not overwrite and self.exists(name):
            raise FileExistsError(QCoreApplication.translate('AMEPresetService', '同名工作流已存在，请使用其他名称'))
        save_workflow(graph, json_path, overwrite=overwrite)
        return json_path

    def save_with_thumbnail(self, name: str, graph, *, overwrite=True) -> Path:
        """保存并自动截图。手动封面不为空时跳过自动截图"""
        json_path = self.save(name, graph, overwrite=overwrite)
        self.last_thumbnail_error = ''
        thumb = self._path(name, '.png')
        if not thumb.exists() or cover_source(thumb) == 'automatic':
            try:
                self._make_thumbnail(graph, name)
            except Exception as error:
                self.last_thumbnail_error = str(error)
                logger.warning(f'[AME] 工作流已保存，封面生成失败: {error}')
        return json_path

    def load(self, name: str, graph) -> bool:
        json_path = self._path(name)
        if not json_path.exists():
            return False
        load_workflow(graph, json_path)
        return True

    def delete(self, name: str):
        self._cover_revisions[name] = self.thumbnail_revision(name) + 1
        for ext in ('.json', '.png'):
            p = self._path(name, ext)
            if p.exists():
                p.unlink()
        # 若删除的是出厂模板同名工作流, 记录删除标记, 防止下次启动补缺同步时复活
        if (self._template_dir / f"{name}.json").exists():
            record_deleted_template(self._deleted_marker, name)

    def rename(self, old: str, new: str):
        sources = [self._path(old, ext) for ext in ('.json', '.png')]
        targets = [self._path(new, ext) for ext in ('.json', '.png')]
        if old == new:
            return
        if not sources[0].is_file():
            raise FileNotFoundError(sources[0])
        same_name = old.casefold() == new.casefold()
        if not same_name and any(path.exists() for path in targets):
            raise FileExistsError(QCoreApplication.translate('AMEPresetService', '同名工作流已存在，请使用其他名称'))
        moved = []
        try:
            for src, dst in zip(sources, targets):
                if src.exists():
                    src.rename(dst)
                    moved.append((src, dst))
        except Exception:
            for src, dst in reversed(moved):
                dst.rename(src)
            raise
        for name in (old, new):
            self._cover_revisions[name] = self.thumbnail_revision(name) + 1
        # 若重命名的原名对应出厂模板, 记录原名删除标记:
        # 否则下次启动补缺同步会因用户目录缺少原同名文件而把模板以原名复活,
        # 且重命名后的工作流再被删除时, 原名模板同样会复活
        if (self._template_dir / f"{old}.json").exists():
            record_deleted_template(self._deleted_marker, old)

    def import_file(self, path: str) -> str | None:
        src = Path(path)
        data = read_workflow(src)
        name = self.validate_name(src.stem)
        base = name
        counter = 1
        while self.exists(name):
            name = f"{base}_{counter}"
            counter += 1
        dst = self._path(name)
        write_workflow(data, dst, overwrite=False)
        return name

    def export(self, name: str, path: str):
        src = self._path(name)
        write_workflow(read_workflow(src), Path(path))

    def set_thumbnail(self, name: str, img_path: str):
        """同步服务入口；加载页使用后台 prepare 后提交小尺寸 PNG。"""
        self.set_thumbnail_data(name, encode_cover(read_cover(img_path), 'manual'))

    def thumbnail_revision(self, name):
        return self._cover_revisions.get(name, 0)

    def set_thumbnail_data(self, name, data):
        if not self._path(name).is_file():
            raise FileNotFoundError(QCoreApplication.translate('AMEPresetService', '工作流已被删除'))
        write_cover(self._path(name, '.png'), data)

    def _make_thumbnail(self, graph, name: str):
        """只能从手动保存入口调用；GUI 截图后原子写入带来源标记的 PNG。"""
        pixmap = graph.widget.grab()
        if pixmap.isNull():
            raise ValueError(QCoreApplication.translate('AMEPresetService', '无法截取工作流画布'))
        image = pixmap.scaled(320, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation).toImage()
        write_cover(self._path(name, '.png'), encode_cover(image, 'automatic'))


preset_service = AMEPresetService()
