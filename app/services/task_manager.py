# coding: utf-8
from PySide6.QtCore import QObject

from ..common.signal_bus import signalBus
from ..services.recode.recode_worker import RecodeWorker
from ..services.demuxing.demux_worker import DemuxWorker
from .muxing.mux_worker import MuxWorker

class TaskManager(QObject):
    """
    全局任务调度与管理器 (Singleton)
    负责接管各种类型的后台处理，并在收到 UI 的请求时实例化、管理或终止 Worker。
    避免 UI 视图组件与底层多媒体处理逻辑的强耦合。
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TaskManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, parent=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        super().__init__(parent)
        self._initialized = True
        
        self.workers = {}  # 存放所有的后台 Worker {task_id: QThread}
        self._shutting_down = False

        # 挂载信号总线监听
        signalBus.taskAdded.connect(self._on_task_added)
        signalBus.taskStopRequested.connect(self._on_task_stop_requested)

    def _on_task_added(self, payload: dict):
        task_id = payload.get("task_id")
        task_type = payload.get("type", "")
        worker_class = {"Recode": RecodeWorker, "Demux": DemuxWorker, "Mux": MuxWorker}.get(task_type)
        if worker_class is None:
            return

        if self._shutting_down:
            return
        if self.workers:
            signalBus.taskError.emit(task_id, self.tr("已有任务正在运行或中止，请等待其结束"))
            return
        try:
            if not task_id or not payload.get("files"):
                raise ValueError(self.tr("任务缺少编号或输入文件"))
            worker = worker_class(payload=payload, parent=self)
        except Exception as exc:
            signalBus.taskError.emit(task_id or "", self.tr("无法启动任务: {error}").format(error=str(exc)))
            return
        worker.finished.connect(lambda t_id=task_id: self._cleanup_worker(t_id))
        self.workers[task_id] = worker
        signalBus.taskExecutionStarted.emit(task_id)
        worker.start()

    def _on_task_stop_requested(self, task_id: str):
        worker = self.workers.get(task_id)
        if worker:
            worker.stop()

    def _cleanup_worker(self, task_id: str):
        if task_id in self.workers:
            worker = self.workers.pop(task_id)
            if worker._is_cancelled and not worker._has_error:
                signalBus.taskCancelled.emit(task_id)
            worker.deleteLater()
            # worker.finished 在任务完成/出错/被取消三种结局下均会触发,
            # 在此处统一发射全局结束信号, 通知所有界面恢复开始按钮
            signalBus.taskExecutionEnded.emit(task_id)

    def shutdown(self):
        """先终止全部进程，再等待线程释放输出与管道。"""
        self._shutting_down = True
        for worker in list(self.workers.values()):
            worker.stop()
        for task_id, worker in list(self.workers.items()):
            worker.wait()
            self._cleanup_worker(task_id)

# 创建单例即可生效，由于这里是挂载在 signalBus 上的
taskManager = TaskManager()
