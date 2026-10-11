"""非节点任务的输出保护：预检全部目标，成功后才发布文件。"""
import os
import tempfile
from pathlib import Path, PureWindowsPath

from PySide6.QtCore import QCoreApplication
from app.common.logger import logger


def safe_filename(name: str) -> str:
    """媒体元数据只能指定文件名，不能指定路径或 Windows 特殊文件。"""
    name = str(name)
    if (not name or name in {".", ".."} or name.endswith((".", " "))
            or any(c in name for c in '<>:"/\\|?*')
            or any(ord(c) < 32 for c in name)
            or PureWindowsPath(name).is_reserved()):
        raise ValueError(QCoreApplication.translate("OutputService", "不安全的输出文件名: {name}").format(name=name))
    return name


class OutputTransaction:
    """Windows rename 不覆盖已有文件；所有工具仅能写入私有暂存目录。"""
    def __init__(self, inputs):
        self._inputs = {self._key(Path(p)) for p in inputs}
        self._targets = {}
        self._directories = {}

    @staticmethod
    def _key(path):
        return str(path.resolve()).casefold()

    def plan(self, target):
        target = Path(target)
        safe_filename(target.name)
        key = self._key(target)
        if key in self._inputs:
            raise ValueError(QCoreApplication.translate("OutputService", "输出路径与输入文件相同: {path}").format(path=target))
        if key in self._targets:
            raise ValueError(QCoreApplication.translate("OutputService", "多个输出文件使用了相同路径: {path}").format(path=target))
        if target.exists() or target.is_symlink():
            raise FileExistsError(QCoreApplication.translate("OutputService", "输出文件已存在，请更改输出名称或目录: {path}").format(path=target))
        self._targets[key] = target.resolve()

    def stage(self, target):
        target = self._targets[self._key(Path(target))]
        parent = target.parent
        if parent not in self._directories:
            parent.mkdir(parents=True, exist_ok=True)
            self._directories[parent] = tempfile.TemporaryDirectory(prefix=".ame-", dir=parent)
        return Path(self._directories[parent].name) / target.name

    def commit(self):
        # 在移动任何文件前检查全部产物，避免漏文件也报告任务成功。
        for target in self._targets.values():
            if not self.stage(target).is_file():
                raise FileNotFoundError(QCoreApplication.translate("OutputService", "任务未生成预期输出文件: {path}").format(path=target))
            if target.exists() or target.is_symlink():
                raise FileExistsError(QCoreApplication.translate("OutputService", "输出文件已存在，请更改输出名称或目录: {path}").format(path=target))
        for target in self._targets.values():
            # 本项目只支持 Windows；os.rename 在目标已存在时抛错，保护竞态中新建的文件。
            os.rename(self.stage(target), target)

    def cleanup(self):
        for directory in self._directories.values():
            try:
                directory.cleanup()
            except OSError:
                logger.exception(f"清理任务暂存目录失败: {directory.name}")
        self._directories.clear()
