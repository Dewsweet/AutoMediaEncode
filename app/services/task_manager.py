# coding: utf-8
from PySide6.QtCore import QObject

from ..common.signal_bus import signalBus
from ..services.recode.recode_worker import RecodeWorker

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

        # 挂载信号总线监听
        signalBus.taskAdded.connect(self._on_task_added)
        signalBus.taskStopRequested.connect(self._on_task_stop_requested)

    def _on_task_added(self, payload: dict):
        task_id = payload.get("task_id")
        task_type = payload.get("type", "")

        # 根据任务类型，实例化对应的执行器 (Worker)
        if task_type == "Recode":
            worker = RecodeWorker(payload=payload, parent=self)
            
            # 当该任务在后台自然结束（即使因为错误或已完成），将其从管理器中移除清理
            worker.finished.connect(lambda t_id=task_id: self._cleanup_worker(t_id))
            
            self.workers[task_id] = worker
            # 这里暂时维持和之前一样的“收到就立即启动”策略，如果日后需要做串行或限制并发数量，就在这里用队列进行阻塞或分配
            worker.start()
        # elif task_type == "Demux": ...
        else:
            pass

    def _on_task_stop_requested(self, task_id: str):
        worker = self.workers.get(task_id)
        if worker:
            worker.stop()
            # 从UI点击中止后直接抛出 cancelled 信号给 UI更新
            signalBus.taskCancelled.emit(task_id)

    def _cleanup_worker(self, task_id: str):
        if task_id in self.workers:
            # 安全清理
            del self.workers[task_id]

# 创建单例即可生效，由于这里是挂载在 signalBus 上的
taskManager = TaskManager()
