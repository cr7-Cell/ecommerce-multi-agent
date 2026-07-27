"""
MCP 适配器基类
==============
定义所有外部工具适配器的统一接口和数据模型。

核心设计模式：适配器模式 (Adapter Pattern)
- 目标接口 (Target): ToolAdapter 抽象基类
- 适配者 (Adaptee): 外部服务 (数据库、API、搜索引擎等)
- 适配器 (Adapter): DatabaseAdapter、ExternalAPIAdapter 等具体实现

调用流程：
  1. MCPServer.call_tool() 调用 tool.handler(**args)
  2. handler 内部创建 ToolRequest 并调用 adapter.execute(request)
  3. adapter 执行: 权限检查 → 超时控制 → 重试 → 调用外部服务
  4. 返回标准化的 ToolResponse
"""

import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ============================================================
# 数据模型
# ============================================================

class AdapterStatus(str, Enum):
    """适配器执行状态"""
    SUCCESS = "success"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    SERVICE_UNAVAILABLE = "service_unavailable"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ToolRequest:
    """
    工具调用请求（从 MCP Tool 传入适配器）

    这是 MCP 协议层和适配器层之间的标准数据契约。
    无论底层是数据库、HTTP API 还是搜索引擎，都使用这个统一格式。
    """
    tool_name: str                              # 工具名称（如 "query_order_details"）
    agent_name: str                             # 调用方 Agent（如 "order_management"）
    arguments: Dict[str, Any]                   # 工具参数（来自 MCP 调用）
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    caller_api_key: str = ""                    # 调用方 API Key（用于权限验证）
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ToolResponse:
    """
    工具调用响应（从适配器返回给 MCP Tool）

    标准化的响应格式，无论底层服务是什么，返回结构一致。
    """
    status: AdapterStatus                       # 执行状态
    data: Any = None                            # 返回数据（dict/list/str）
    error: Optional[str] = None                 # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据（耗时、重试次数等）
    request_id: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "request_id": self.request_id,
        }

    @classmethod
    def success(cls, data: Any, request_id: str = "", **metadata) -> "ToolResponse":
        return cls(status=AdapterStatus.SUCCESS, data=data, request_id=request_id, metadata=metadata)

    @classmethod
    def error(cls, status: AdapterStatus, error: str, request_id: str = "") -> "ToolResponse":
        return cls(status=status, error=error, request_id=request_id)


# ============================================================
# 适配器抽象基类
# ============================================================

class ToolAdapter(ABC):
    """
    工具适配器抽象基类

    所有外部工具适配器必须实现此接口。

    子类需要实现：
    - _validate(): 参数校验
    - _call_service(): 调用外部服务
    - _transform_response(): 响应格式转换

    基类自动处理：
    - 权限检查（通过 PermissionGuard）
    - 超时控制
    - 重试逻辑
    - 日志记录
    - 性能监控
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._permission_guard = None  # 延迟注入
        self._retry_config = None      # 延迟注入
        self._timeout_seconds = 30     # 默认超时

    def set_permission_guard(self, guard):
        """注入权限守卫"""
        self._permission_guard = guard

    def set_retry_config(self, config):
        """注入重试配置"""
        self._retry_config = config

    def set_timeout(self, seconds: int):
        """设置超时时间"""
        self._timeout_seconds = seconds

    # ---- 公共入口 ----

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """
        执行工具调用的完整流程（模板方法）

        1. 权限检查
        2. 参数校验
        3. 调用外部服务（含超时+重试）
        4. 响应格式转换
        5. 日志记录
        """
        start_time = time.time()

        # Step 1: 权限检查
        if self._permission_guard:
            allowed, reason = await self._permission_guard.check(request)
            if not allowed:
                logger.warning(f"[Adapter:{self.name}] 权限拒绝: {reason}")
                return ToolResponse.error(
                    AdapterStatus.PERMISSION_DENIED,
                    f"权限不足: {reason}",
                    request.request_id,
                )

        # Step 2: 参数校验
        try:
            self._validate(request.arguments)
        except ValueError as e:
            return ToolResponse.error(
                AdapterStatus.VALIDATION_ERROR,
                str(e),
                request.request_id,
            )

        # Step 3: 调用外部服务（含重试）
        elapsed = 0.0
        last_error = None
        max_retries = self._retry_config.max_retries if self._retry_config else 0

        for attempt in range(max_retries + 1):
            try:
                raw_result = await self._call_with_timeout(request)
                elapsed = (time.time() - start_time) * 1000

                # Step 4: 响应格式转换
                response = self._transform_response(raw_result, request)
                response.request_id = request.request_id
                response.metadata.update({
                    "adapter": self.name,
                    "elapsed_ms": round(elapsed, 2),
                    "attempts": attempt + 1,
                    "tool_name": request.tool_name,
                })

                logger.info(
                    f"[Adapter:{self.name}] {request.tool_name} "
                    f"成功 (耗时: {elapsed:.0f}ms, 尝试: {attempt + 1})"
                )
                return response

            except TimeoutError:
                last_error = "请求超时"
                if attempt < max_retries:
                    wait = self._retry_config.backoff(attempt)
                    logger.warning(f"[Adapter:{self.name}] 超时，{wait:.1f}s 后重试 (尝试 {attempt + 1})")
                    await self._async_sleep(wait)

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    wait = self._retry_config.backoff(attempt)
                    logger.warning(f"[Adapter:{self.name}] 错误: {e}，{wait:.1f}s 后重试")
                    await self._async_sleep(wait)

        # 所有重试都失败
        elapsed = (time.time() - start_time) * 1000
        logger.error(f"[Adapter:{self.name}] {request.tool_name} 失败: {last_error}")

        return ToolResponse(
            status=AdapterStatus.SERVICE_UNAVAILABLE,
            error=f"调用失败（已重试 {max_retries} 次）: {last_error}",
            metadata={"elapsed_ms": round(elapsed, 2), "attempts": max_retries + 1},
            request_id=request.request_id,
        )

    # ---- 子类必须实现的方法 ----

    @abstractmethod
    def _validate(self, arguments: Dict[str, Any]) -> None:
        """
        参数校验
        校验失败抛出 ValueError
        """
        pass

    @abstractmethod
    async def _call_service(self, request: ToolRequest) -> Any:
        """
        调用外部服务（核心逻辑）
        子类在这里实现具体的数据库查询、HTTP 请求等
        """
        pass

    @abstractmethod
    def _transform_response(self, raw_result: Any, request: ToolRequest) -> ToolResponse:
        """
        将外部服务的原始响应转换为标准 ToolResponse
        """
        pass

    # ---- 内部方法 ----

    async def _call_with_timeout(self, request: ToolRequest) -> Any:
        """带超时控制的服务调用"""
        import asyncio
        try:
            return await asyncio.wait_for(
                self._call_service(request),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"调用 {self.name} 超时 ({self._timeout_seconds}s)")

    async def _async_sleep(self, seconds: float):
        """异步等待"""
        import asyncio
        await asyncio.sleep(seconds)