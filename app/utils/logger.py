"""日志系统

配置结构化日志，支持：
- 多种日志级别
- JSON 和文本格式
- 上下文日志记录
- 文件和控制台输出
"""

import logging
import sys
from typing import Literal, Optional

import structlog


def setup_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    format: Literal["json", "text"] = "json",
    log_file: Optional[str] = None
):
    """
    配置日志系统
    
    Args:
        level: 日志级别
        format: 日志格式（json 或 text）
        log_file: 可选的日志文件路径
    """
    # 设置日志级别
    log_level = getattr(logging, level.upper())
    
    # 配置标准库 logging
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[]
    )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    logging.root.addHandler(console_handler)
    
    # 添加文件处理器（如果指定）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        logging.root.addHandler(file_handler)
    
    # 配置 structlog
    if format == "json":
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已配置 (级别: {level}, 格式: {format})")


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称（通常使用 __name__）
        
    Returns:
        日志记录器实例
    """
    return logging.getLogger(name)


class LogContext:
    """
    日志上下文管理器
    
    用于在特定代码块中添加上下文信息到日志。
    """
    
    def __init__(self, **kwargs):
        """
        初始化日志上下文
        
        Args:
            **kwargs: 上下文键值对
        """
        self.context = kwargs
        self.token = None
    
    def __enter__(self):
        """进入上下文"""
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if self.token:
            structlog.contextvars.unbind_contextvars(*self.context.keys())


def log_function_call(func):
    """
    装饰器：记录函数调用
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"调用函数: {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数返回: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"函数异常: {func.__name__}, 错误: {e}")
            raise
    
    return wrapper


def log_async_function_call(func):
    """
    装饰器：记录异步函数调用
    
    Args:
        func: 要装饰的异步函数
        
    Returns:
        装饰后的异步函数
    """
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"调用异步函数: {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"异步函数返回: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"异步函数异常: {func.__name__}, 错误: {e}")
            raise
    
    return wrapper
