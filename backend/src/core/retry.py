"""HTTP/API 重试模块（参考 OmniBox 三重重试模式）"""
import time
import logging
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger("orcaai.retry")

T = TypeVar("T")


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry_log: bool = True,
):
    """指数退避重试装饰器

    Args:
        max_retries: 最大重试次数（不含首次）
        base_delay: 首次重试等待秒数
        backoff_factor: 退避倍数
        exceptions: 哪些异常触发重试
        on_retry_log: 是否记录重试日志
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay * (backoff_factor ** attempt)
                        if on_retry_log:
                            logger.warning(
                                "%s 失败 (第 %d/%d 次)，%0.1f 秒后重试: %s",
                                func.__qualname__, attempt + 1, max_retries, delay, e,
                            )
                        time.sleep(delay)
                    else:
                        logger.error("%s 重试 %d 次后仍失败: %s", func.__qualname__, max_retries, e)
            raise last_error  # type: ignore
        return wrapper
    return decorator
