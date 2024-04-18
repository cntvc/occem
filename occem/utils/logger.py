import os
import sys

from loguru import logger

from occem.constants import LOG_PATH

__all__ = ["logger"]

"""
日志格式化文档: https://loguru.readthedocs.io/en/stable/api/logger.html#record
"""

log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | {level} | {name}:{line} | {function} | message: {message}"  # noqa

logger.remove()

logger.add(
    sink=sys.stdout,
    level="INFO",
    format=log_format,
)

logger.add(
    sink=os.path.join(LOG_PATH, "log_{time:YYYY_MM}.log"),
    format=log_format,
    level="DEBUG",
    rotation="5MB",
    compression="tar.gz",
)
