# coding: utf-8
from PySide6.QtCore import QObject, Signal

class SignalBus(QObject):
    """
    全局信号总线 (Singleton)
    用于跨页面、跨线程传递任务状态和进度更新
    """
    _instance = None

    # 当用户点击"开始任务"时发出，携带整个任务数据的 payload 字典
    # payload 结构规范: {"task_id": str, "type": str, "files": list, "states": dict}
    taskAdded = Signal(dict)
    
    # 任务进度更新信号：task_id, current_idx, total_files, filename, percent, time_left
    taskProgressUpdated = Signal(str, int, int, str, float, str)
    
    # 任务完成信号：task_id
    taskCompleted = Signal(str)
    
    # 任务异常/错误信号：task_id, error_message
    taskError = Signal(str, str)
    
    # 任务取消/中止信号：task_id
    taskCancelled = Signal(str)

    # 任务请求停止信号：task_id (由UI发出给Manager)
    taskStopRequested = Signal(str)

    # 全局任务执行开始信号：task_id (由 TaskManager 或 AME 工作流发射)
    # 所有界面监听此信号, 将自家的"开始任务"按钮切换为不可用, 实现跨界面任务互斥
    taskExecutionStarted = Signal(str)

    # 全局任务执行结束信号：task_id (完成/出错/取消三种结局均触发)
    # 所有界面监听此信号, 恢复自家"开始任务"按钮的可用状态
    taskExecutionEnded = Signal(str)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SignalBus, cls).__new__(cls, *args, **kwargs)
        return cls._instance

# 全局单例实例
signalBus = SignalBus()
