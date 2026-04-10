# coding: utf-8
import sys
import datetime
from pathlib import Path
from loguru import logger
from ..services.path_service import PathService

def _setup_logger():
    """
    配置并获取全局应用日志实例。
    使用 loguru 进行管理，支持控制台高亮和日志文件的自动轮转。
    """
    # 移除 loguru 默认的标准输出 (如果不移除可能会重复打印)
    logger.remove()
    
    # 控制台输出 (INFO 级别以上，彩色高亮)
    # logger.add(
    #     sys.stdout,
    #     level="INFO",
    #     format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    #     enqueue=True
    # )
    
    # 文件输出 (DEBUG 级别以上，按天/按大小轮转，保留 7 天)
    log_dir = PathService.get_log_dir()
    log_file = log_dir / "ame_run_{time:YYYY-MM-DD}.log"
    
    logger.add(
        str(log_file),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",      # 每个文件最大 10MB，超过就分割
        retention="7 days",    # 仅保留最近 7 天的日志记录
        encoding="utf-8",
        enqueue=True           # 开启异步写入，保证多线程安全
    )

# 模块加载时立刻按照设定初始化，其他文件直接 'from logger import logger' 即可
_setup_logger()
