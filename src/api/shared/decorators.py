import asyncio
import functools
import inspect
import time
from typing import Any, Callable, TypeVar

from logger import logger

F = TypeVar("F", bound=Callable[..., Any])


def logged(func: F) -> F:
    """Decorator to log function entry, exit, and execution time."""

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        logger.info(f"Entering {func_name}")
        
        try:
            result = await func(*args, **kwargs)
            duration = (time.perf_counter() - start_time) * 1000
            logger.info(f"Exiting {func_name}", extra={"duration_ms": int(duration)})
            return result
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error in {func_name}", extra={"error": str(e), "duration_ms": int(duration)})
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        logger.info(f"Entering {func_name}")
        
        try:
            result = func(*args, **kwargs)
            duration = (time.perf_counter() - start_time) * 1000
            logger.info(f"Exiting {func_name}", extra={"duration_ms": int(duration)})
            return result
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(f"Error in {func_name}", extra={"error": str(e), "duration_ms": int(duration)})
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper  # type: ignore
    return sync_wrapper  # type: ignore
