"""中止只发出 kill；等待与关闭管道由拥有进程的后台线程完成。"""
import subprocess


def kill_process(process):
    if process is None:
        return
    # FfmpegProgress 与原生 Popen 使用同一个终止方式，不跨线程调用 quit/communicate。
    child = process if isinstance(process, subprocess.Popen) else getattr(process, "process", None)
    if child is not None:
        try:
            if child.poll() is None:
                child.kill()
        except OSError:
            pass
