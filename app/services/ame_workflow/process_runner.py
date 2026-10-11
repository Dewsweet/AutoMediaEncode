"""工作流进程的取消、超时和回收；等待与管道关闭只在所属后台线程执行。"""
import subprocess
import time
from contextlib import contextmanager
from threading import Event, Lock, local

import win32api
import win32job


class ProcessCancelled(Exception):
    pass


_thread_state = local()


class ProcessControl:
    def __init__(self):
        self.cancelled = Event()
        self.paused = Event()
        self._lock = Lock()
        self._processes = {}

    def cancel(self):
        self.cancelled.set()
        self.paused.clear()
        with self._lock:
            for process, job in self._processes.items():
                self._kill(process, job)

    @staticmethod
    def _kill(process, job):
        # Job Object 包含工具自行派生的子进程，避免仅停止管道的父进程。
        try:
            win32job.TerminateJobObject(job, 1)
        except win32api.error:
            if process.poll() is None:
                try:
                    process.kill()
                except OSError:
                    pass

    def checkpoint(self):
        while self.paused.is_set():
            if self.cancelled.wait(0.05):
                raise ProcessCancelled()
        if self.cancelled.is_set():
            raise ProcessCancelled()

    def start(self, cmd, **kwargs):
        self.checkpoint()
        with self._lock:
            if self.cancelled.is_set():
                raise ProcessCancelled()
            job = win32job.CreateJobObject(None, '')
            process = None
            try:
                limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
                limits['BasicLimitInformation']['LimitFlags'] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
                process = subprocess.Popen(cmd, **kwargs)
                win32job.AssignProcessToJobObject(job, process._handle)
                self._processes[process] = job
                return process
            except BaseException:
                if process is not None:
                    process.kill()
                    process.wait()
                    for stream in (process.stdin, process.stdout, process.stderr):
                        if stream is not None:
                            stream.close()
                win32api.CloseHandle(job)
                raise

    def stop(self, process):
        with self._lock:
            job = self._processes.get(process)
            if job is not None:
                self._kill(process, job)

    def release(self, process):
        self.stop(process)
        process.wait()
        if getattr(process, '_communication_started', False):
            # communicate(timeout=...) 的 Windows 读管道线程也必须完成回收。
            process.communicate()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()
        with self._lock:
            job = self._processes.pop(process, None)
            if job is not None:
                win32api.CloseHandle(job)

    def close(self):
        for process in list(self._processes):
            self.release(process)


@contextmanager
def process_scope(control):
    previous = getattr(_thread_state, 'control', None)
    _thread_state.control = control
    try:
        yield
    finally:
        _thread_state.control = previous


def current_control():
    return getattr(_thread_state, 'control', None)


def check_cancelled():
    control = current_control()
    if control is not None:
        control.checkpoint()


def _check_wait(control, cmd, deadline, timeout, cancelled):
    if control.cancelled.is_set() or (cancelled and cancelled()):
        raise ProcessCancelled()
    if deadline is not None and time.monotonic() >= deadline:
        raise subprocess.TimeoutExpired(cmd, timeout)


def run_process(cmd, *, capture_output=False, timeout=None, cancelled=None, **kwargs):
    """subprocess.run 的捕获输出用法；静默或关闭 stdout 后仍每 50ms 检查取消。"""
    control = current_control() or ProcessControl()
    if cancelled and cancelled():
        raise ProcessCancelled()
    if capture_output:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
    kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    process = control.start(cmd, **kwargs)
    deadline = time.monotonic() + timeout if timeout is not None else None
    try:
        while True:
            _check_wait(control, cmd, deadline, timeout, cancelled)
            try:
                stdout, stderr = process.communicate(timeout=0.05)
                _check_wait(control, cmd, deadline, timeout, cancelled)
                control.checkpoint()
                return subprocess.CompletedProcess(cmd, process.returncode, stdout, stderr)
            except subprocess.TimeoutExpired:
                if process.poll() is not None:
                    # 父进程已结束但后代仍持有输出句柄，停止后代以便收到 EOF。
                    control.stop(process)
    finally:
        control.release(process)


def run_pipe(cmd1, kw1, cmd2, kw2, *, timeout=14400, cancelled=None):
    """两端均受管理；第二端启动失败、取消和超时也会回收第一端。"""
    control = current_control() or ProcessControl()
    if cancelled and cancelled():
        raise ProcessCancelled()
    first_kwargs = dict(kw1 or {})
    first_kwargs['stdout'] = subprocess.PIPE
    # 生产端的错误输出不进入媒体数据流，也不会堵住无人读取的 PIPE。
    first_kwargs['stderr'] = subprocess.DEVNULL
    first_kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    second_kwargs = dict(kw2 or {})
    second_kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    second_kwargs.setdefault('errors', 'replace')
    second_kwargs.setdefault('creationflags', subprocess.CREATE_NO_WINDOW)
    p1 = p2 = None
    deadline = time.monotonic() + timeout if timeout is not None else None
    try:
        p1 = control.start(cmd1, **first_kwargs)
        p2 = control.start(cmd2, stdin=p1.stdout, **second_kwargs)
        p1.stdout.close()
        while True:
            _check_wait(control, cmd2, deadline, timeout, cancelled)
            try:
                stdout, _ = p2.communicate(timeout=0.05)
                _check_wait(control, cmd2, deadline, timeout, cancelled)
                control.checkpoint()
                if p2.returncode == 0:
                    # 消费端可能把生产端异常中断留下的部分帧编码成功。
                    # 两端均正常结束，才能把媒体文件发布给下游节点。
                    while True:
                        _check_wait(control, cmd1, deadline, timeout, cancelled)
                        try:
                            p1.wait(timeout=0.05)
                            break
                        except subprocess.TimeoutExpired:
                            continue
                    if p1.returncode != 0:
                        return p1.returncode, (stdout or '') + f'\nPipeline producer failed: returncode={p1.returncode}'
                return p2.returncode, stdout
            except subprocess.TimeoutExpired:
                if p2.poll() is not None:
                    control.stop(p2)
    finally:
        for process in (p2, p1):
            if process is not None:
                control.stop(process)
        for process in (p2, p1):
            if process is not None:
                control.release(process)
