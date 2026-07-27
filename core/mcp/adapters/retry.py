"""
MCP 工具调用超时处理与重试机制
==============================
为所有外部工具调用提供统一的超时和重试策略。

重试策略：
  - 指数退避 (Exponential Backoff): 每次重试等待时间翻倍
  - 最大重试次数: 可配置
  - 可重试的错误类型: 超时、网络错误、服务不可用
  - 不可重试的错误: 参数错误、权限不足
"""

import logging
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """
    重试配置

    参数:
        max_retries: 最大重试次数（不含首次调用）
        base_delay_seconds: 基础延迟（秒）
        max_delay_seconds: 最大延迟上限（秒）
        jitter: 是否添加随机抖动（避免惊群效应）
        retryable_errors: 可重试的错误类型关键词
    """
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    jitter: bool = True
    retryable_errors: tuple = ("timeout", "connection", "service_unavailable", "503", "429")

    def backoff(self, attempt: int) -> float:
        """
        计算第 N 次重试的等待时间（指数退避）

        公式: min(base * 2^attempt, max_delay) + jitter

        示例:
          第 1 次重试: 1s → 2s
          第 2 次重试: 2s → 4s
          第 3 次重试: 4s → 8s
        """
        delay = min(self.base_delay_seconds * (2 ** attempt), self.max_delay_seconds)
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)
        return round(delay, 2)

    def is_retryable(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in self.retryable_errors)


# ============================================================
# 装饰器方式（备选方案）
# ============================================================

async def retry_with_backoff(
    func,
    config: RetryConfig = None,
    *args,
    **kwargs,
):
    """
    带指数退避的重试执行器

    用法:
        result = await retry_with_backoff(my_async_func, config, arg1, arg2)
    """
    if config is None:
        config = RetryConfig()

    last_error = None
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < config.max_retries and config.is_retryable(e):
                wait = config.backoff(attempt)
                logger.warning(
                    f"[Retry] 第 {attempt + 1} 次重试，等待 {wait}s，"
                    f"错误: {e}"
                )
                import asyncio
                await asyncio.sleep(wait)
            else:
                break

    raise last_error