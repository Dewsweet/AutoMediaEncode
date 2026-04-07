# coding: utf-8
import logging
import datetime
from pathlib import Path
from ..services.path_service import PathService

def get_app_logger(name="AME"):
    """
    获取全局应用日志实例。
    日志将保存在 logs 目录下，按日期滚动，同时在控制台输出。
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    log_dir = PathService.get_log_dir()
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    log_file = log_dir / f"ame_run_{date_str}.log"
    
    # 写文件使用 INFO及以上级别 (包含 DEBUG 时细节太多可以适当开启)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # 控制台输出 INFO 及以上级别
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
    fh.setFormatter(formatter)
    # ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    # logger.addHandler(ch)
    
    return logger

# 提供一个单例的 logger 直接 import
logger = get_app_logger()
