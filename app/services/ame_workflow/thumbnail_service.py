"""封面解码与内存缓存：后台仅处理 QImage，GUI 线程负责 QPixmap。"""
import struct
from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import (QObject, QRunnable, QThreadPool, Signal, Slot,
                           QSize, Qt, QBuffer, QByteArray, QIODevice, QSaveFile,
                           QCoreApplication)
from PySide6.QtGui import QImageReader

COVER_SIZE = QSize(368, 216)
CARD_SIZE = QSize(184, 108)
SOURCE_KEY = 'AMECoverSource'


def cover_source(path):
    """只读取 PNG 头部的来源标记，绝不在 GUI 线程解码旧大图。

    没有标记的旧封面保守保留，避免无法区分旧截图与自定义图片时覆盖用户图。
    """
    try:
        with Path(path).open('rb') as stream:
            if stream.read(8) != b'\x89PNG\r\n\x1a\n':
                return None
            for _ in range(64):
                header = stream.read(8)
                if len(header) != 8:
                    break
                length, kind = struct.unpack('>I4s', header)
                if kind in (b'IDAT', b'IEND'):
                    break
                if kind == b'tEXt' and length <= 1024:
                    text = stream.read(length)
                    if text.startswith(SOURCE_KEY.encode() + b'\0'):
                        return text.split(b'\0', 1)[1].decode('ascii', errors='replace')
                else:
                    stream.seek(length, 1)
                stream.seek(4, 1)  # CRC
    except OSError:
        pass
    return None


def read_cover(path, size=COVER_SIZE):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 128 * 1024 * 1024:
        raise ValueError(QCoreApplication.translate('AMEThumbnail', '封面文件无效或超过 128 MB'))
    reader = QImageReader(str(path))
    try:
        reader.setAutoTransform(True)
        original = reader.size()
        if (original.width() <= 0 or original.height() <= 0
                or original.width() * original.height() > 40_000_000
                or max(original.width(), original.height()) > 20000):
            raise ValueError(QCoreApplication.translate('AMEThumbnail', '图片无效或尺寸超过限制（4000 万像素 / 单边 20000）'))
        # JPEG 等格式可直接缩放解码；PNG 完整解码仍受像素上限保护。
        if max(original.width(), original.height()) > 1024:
            scaled = original.scaled(QSize(1024, 1024), Qt.KeepAspectRatio)
            reader.setScaledSize(QSize(max(1, scaled.width()), max(1, scaled.height())))
        image = reader.read()
        if image.isNull():
            raise ValueError(QCoreApplication.translate('AMEThumbnail', '无法读取封面图片: {error}').format(error=reader.errorString()))
    finally:
        reader.setFileName('')  # 异常堆栈持引用时也释放 Windows 文件句柄。
    # 先裁剪再放大，极端长宽比不会产生巨型中间图像。
    width = min(image.width(), max(1, round(image.height() * size.width() / size.height())))
    height = min(image.height(), max(1, round(image.width() * size.height() / size.width())))
    return image.copy((image.width()-width)//2, (image.height()-height)//2, width, height).scaled(
        size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def encode_cover(image, source):
    image.setText(SOURCE_KEY, source)
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.WriteOnly) or not image.save(buffer, 'PNG'):
        raise OSError(QCoreApplication.translate('AMEThumbnail', '封面图片编码失败'))
    buffer.close()
    return data


def write_cover(path, data):
    # 禁止直接写入回退；打开、编码和提交失败都必须保留原文件。
    target = QSaveFile(str(path))
    target.setDirectWriteFallback(False)
    if not target.open(QIODevice.WriteOnly):
        raise OSError(target.errorString())
    if target.write(data) != len(data):
        error = target.errorString()
        target.cancelWriting()
        raise OSError(error)
    if not target.commit():
        raise OSError(target.errorString())


class _ImageSignals(QObject):
    finished = Signal(object, object, str, bool)


class _ImageTask(QRunnable):
    def __init__(self, key, path, prepare):
        super().__init__()
        self.key, self.path, self.prepare = key, path, prepare
        self.signals = _ImageSignals()

    def run(self):
        try:
            image = read_cover(self.path, COVER_SIZE if self.prepare else CARD_SIZE)
            result = encode_cover(image, 'manual') if self.prepare else image
            error = ''
        except Exception as exception:
            result, error = None, str(exception)
        self.signals.finished.emit(self.key, result, error, self.prepare)


class ThumbnailService(QObject):
    ready = Signal(object, object, str)
    prepared = Signal(object, object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(2)
        self._jobs = {}
        self._cache = OrderedDict()
        self._closed = False

    def request(self, path):
        if self._closed:
            return None
        try:
            path = Path(path)
            stat = path.stat()
            key = (str(path.resolve()).casefold(), stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
        except OSError:
            return None
        if key not in self._cache and key not in self._jobs:
            self._start(key, path, False)
        return key

    def cached(self, key):
        value = self._cache.get(key)
        if value is not None:
            self._cache.move_to_end(key)
        return value

    def prepare(self, token, path):
        if not self._closed:
            self._start(token, path, True)

    def _start(self, key, path, prepare):
        job = _ImageTask(key, path, prepare)
        job.signals.finished.connect(self._finished)
        self._jobs[key] = job
        self._pool.start(job)

    @Slot(object, object, str, bool)
    def _finished(self, key, result, error, prepare):
        self._jobs.pop(key, None)
        if self._closed:
            return
        if prepare:
            self.prepared.emit(key, result, error)
        else:
            self._cache[key] = (result, error)
            self._cache.move_to_end(key)
            while len(self._cache) > 64:
                self._cache.popitem(last=False)
            self.ready.emit(key, result, error)

    def shutdown(self):
        self._closed = True
        self._pool.clear()
        self._pool.waitForDone()
        self._jobs.clear()
        self._cache.clear()


_service = None


def thumbnail_service():
    global _service
    if _service is None:
        app = QCoreApplication.instance()
        _service = ThumbnailService(app)
        app.aboutToQuit.connect(_service.shutdown)
    return _service
