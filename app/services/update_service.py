# coding:utf-8
"""软件更新检查服务：通过 GitHub Releases API 查询远程仓库最新版本"""
import json
import re
import ssl
import urllib.error
import urllib.request
from typing import Optional

from PySide6.QtCore import QThread, Signal
from loguru import logger

GITHUB_REPO_URL = "https://github.com/Dewsweet/AutoMediaEncode"
GITHUB_API_URL = "https://api.github.com/repos/Dewsweet/AutoMediaEncode/releases"


class UpdateCheckWorker(QThread):
    """后台检查更新的 QThread Worker

    checkFinished(dict) 携带的字典结构:
        {
            "tag_name": str,        # 例如 "v0.9.1 - Beta"
            "html_url": str,        # Release 页面地址
            "published_at": str,    # ISO 8601 发布时间
            "body": str,            # 更新日志 (Markdown 纯文本)
        }
    """
    checkFinished = Signal(dict)
    checkFailed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._cancelled = False

    def cancel(self):
        """标记取消，worker 结束后信号将被忽略"""
        self._cancelled = True

    def run(self):
        try:
            release = self._fetch_latest_release()
            if self._cancelled:
                return
            if release is None:
                self.checkFailed.emit("仓库中暂无可用版本")
                return
            self.checkFinished.emit({
                "tag_name": release.get("tag_name", ""),
                "html_url": release.get("html_url", GITHUB_REPO_URL + "/releases"),
                "published_at": release.get("published_at", ""),
                "body": release.get("body", "") or "",
            })
        except urllib.error.HTTPError as e:
            logger.error(f"检查更新失败: HTTP {e.code}")
            self.checkFailed.emit(f"服务器返回错误 (HTTP {e.code})")
        except urllib.error.URLError as e:
            reason = getattr(e, "reason", e)
            logger.error(f"检查更新失败: 无法连接 GitHub ({reason})")
            self.checkFailed.emit("无法连接 GitHub，请检查网络连接或代理设置")
        except json.JSONDecodeError as e:
            logger.error(f"检查更新失败: 响应解析失败 ({e})")
            self.checkFailed.emit("响应数据解析失败")
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            self.checkFailed.emit(f"未知错误: {str(e)}")

    @staticmethod
    def _fetch_latest_release() -> Optional[dict]:
        """请求 releases 列表 API，返回第一个非 draft 的 release

        注意: 仓库所有 release 均为 prerelease, /releases/latest 端点会 404,
        因此必须使用列表端点。
        """
        req = urllib.request.Request(
            GITHUB_API_URL + "?per_page=5",
            headers={
                # GitHub API 要求携带 User-Agent
                "User-Agent": "AutoMediaEncode-UpdateChecker",
                "Accept": "application/vnd.github+json",
            },
            method="GET",
        )
        # 仅访问官方 API，保持默认校验；指定超时防止线程长时间挂起
        with urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not isinstance(data, list):
            raise json.JSONDecodeError("响应不是列表", str(data)[:100], 0)

        for release in data:
            if not release.get("draft", False):
                return release
        return None


class UpdateService:
    """更新检查服务 (单例)：管理 worker 生命周期并提供版本比较"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._worker: Optional[UpdateCheckWorker] = None

    def check_for_updates(self, on_finished, on_failed, parent=None) -> bool:
        """启动一次更新检查

        Args:
            on_finished: 检查成功回调, 接收一个 dict 参数
            on_failed: 检查失败回调, 接收一个 str 参数
            parent: worker 的父对象

        Returns:
            bool: 是否成功启动检查 (已有检查在进行中时返回 False)
        """
        if self._worker is not None and self._worker.isRunning():
            logger.warning("更新检查已在进行中，忽略本次请求")
            return False

        self._worker = UpdateCheckWorker(parent)
        self._worker.checkFinished.connect(on_finished)
        self._worker.checkFailed.connect(on_failed)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.finished.connect(self._cleanup_worker)
        self._worker.start()
        return True

    def _cleanup_worker(self):
        self._worker = None

    @property
    def is_checking(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    @staticmethod
    def parse_version(version: str) -> tuple:
        """从版本字符串中提取数字版本段

        "v0.9.1 - Beta" / "0.9.1 - Beta" / "0.9.1" -> (0, 9, 1)
        解析失败返回 ()
        """
        match = re.search(r"\d+(?:\.\d+)*", version)
        if not match:
            return ()
        return tuple(int(x) for x in match.group(0).split("."))

    @staticmethod
    def compare_versions(local: str, remote: str) -> int:
        """比较本地与远程版本号

        Returns:
            1  远程更新 (需要提示更新)
            0  版本相同
            -1 本地更新 (远程为旧版本)
        """
        local_tuple = UpdateService.parse_version(local)
        remote_tuple = UpdateService.parse_version(remote)
        if not local_tuple or not remote_tuple:
            # 任一版本无法解析时保守处理：认为本地已是最新，避免误报
            logger.warning(f"版本号解析失败: local={local!r}, remote={remote!r}")
            return 0

        length = max(len(local_tuple), len(remote_tuple))
        local_pad = local_tuple + (0,) * (length - len(local_tuple))
        remote_pad = remote_tuple + (0,) * (length - len(remote_tuple))

        if remote_pad > local_pad:
            return 1
        if remote_pad < local_pad:
            return -1
        return 0


update_service = UpdateService()
