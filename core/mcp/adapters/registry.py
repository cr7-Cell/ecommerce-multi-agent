"""
MCP 适配器注册中心
==================
管理所有外部工具适配器，提供统一的工具调用路由。

这是理解"工具如何调用"的核心文件：
  1. 初始化所有适配器（数据库、外部 API）
  2. 建立工具名 → 适配器的映射表
  3. 为每个 MCP 工具生成 handler 函数
  4. 注入权限控制和重试机制

调用链路（完整版）：
  User: "查询订单 ORD-001"
    → Supervisor.think() → RoutingDecision(next_agent="order_management")
    → ExpertNode → OrderManagementAgent.run()
      → think() → act() → self.call_tool("query_order_details", {"order_id": "ORD-001"})
        → MCPServer.call_tool("query_order_details", {"order_id": "ORD-001"})
          → tool.handler(order_id="ORD-001")           ← 入口
            → adapter_registry.get_handler("query_order_details")(...)
              → ToolRequest(tool_name="query_order_details", ...)
                → DatabaseAdapter.execute(request)       ← 适配器
                  → PermissionGuard.check(request)       ← 权限检查
                  → _validate(arguments)                 ← 参数校验
                  → _call_with_timeout(request)          ← 超时控制
                    → RetryConfig.backoff()              ← 重试
                    → _call_service(request)             ← 真实查询
                      → SELECT * FROM orders WHERE ...   ← SQL
                  → _transform_response(raw_result)      ← 格式转换
                → ToolResponse(status=SUCCESS, data={...})  ← 返回
          → MCPServer 返回 {"success": True, "result": {...}}
        → observe() 解析结果
      → final_answer() 生成答案
    → Supervisor.final_answer() → LLM 合成最终回复
  → 用户看到自然语言回答
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from core.mcp.adapters.base import (
    ToolAdapter, ToolRequest, ToolResponse, AdapterStatus,
)
from core.mcp.adapters.database import DatabaseAdapter
from core.mcp.adapters.external_api import ExternalAPIAdapter
from core.mcp.adapters.security import PermissionGuard, RateLimiter
from core.mcp.adapters.retry import RetryConfig

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    适配器注册中心

    管理工具名 → 适配器的映射，为每个工具生成 handler 函数。

    使用方式：
        registry = AdapterRegistry()
        await registry.initialize()

        # 获取工具 handler（传给 MCPTool 的 handler 参数）
        handler = registry.get_handler("query_order_details", "order_management")

        # 在 MCP 工具定义中使用
        tool = create_mcp_tool(
            name="query_order_details",
            handler=handler,  # ← 替换原来的 lambda mock
            ...
        )
    """

    def __init__(self):
        # 适配器实例
        self._adapters: Dict[str, ToolAdapter] = {}

        # 工具名 → (适配器名, 适配器实例) 映射
        self._tool_mapping: Dict[str, tuple] = {}

        # 权限控制
        self.permission_guard = PermissionGuard()
        self.rate_limiter = RateLimiter(window_seconds=60, max_calls=100)

        # 默认重试配置
        self.default_retry = RetryConfig(max_retries=2, base_delay_seconds=0.5)

        self._initialized = False

    async def initialize(self, database_url: str = None):
        """
        初始化所有适配器

        参数:
            database_url: 数据库连接字符串（可选，默认 SQLite）
        """
        # 1. 初始化数据库适配器
        db_adapter = DatabaseAdapter()
        await db_adapter.initialize(database_url)
        self._adapters["database"] = db_adapter

        # 2. 初始化外部 API 适配器（开发环境使用模拟器）
        api_adapter = ExternalAPIAdapter()
        self._adapters["external_api"] = api_adapter

        # 3. 为所有适配器注入权限和重试配置
        for adapter in self._adapters.values():
            adapter.set_permission_guard(self.permission_guard)
            adapter.set_retry_config(self.default_retry)

        # 4. 配置权限规则（开发环境：关闭 API Key 验证）
        self.permission_guard.configure(
            require_api_key=False,  # 开发环境不需要 API Key
            tool_allowlist={
                "order_management": ["query_order_details", "lookup_order_status", "create_order", "cancel_order"],
                "logistics": ["track_shipment", "estimate_delivery"],
                "customer_service": ["lookup_order_status", "search_knowledge_base"],
                "recommendation": ["get_user_profile"],
                "inventory": ["check_stock"],
                "payment": ["query_payment_history", "get_exchange_rate"],
            },
        )

        # 5. 建立工具名 → 适配器映射
        self._tool_mapping = {
            # 数据库查询类
            "query_order_details": ("database", db_adapter),
            "lookup_order_status": ("database", db_adapter),
            "create_order": ("database", db_adapter),
            "cancel_order": ("database", db_adapter),
            "get_user_profile": ("database", db_adapter),
            "check_stock": ("database", db_adapter),
            "query_payment_history": ("database", db_adapter),
            # 外部 API 类
            "track_shipment": ("external_api", api_adapter),
            "estimate_delivery": ("external_api", api_adapter),
            "get_exchange_rate": ("external_api", api_adapter),
        }

        self._initialized = True
        logger.info(
            f"[AdapterRegistry] 初始化完成: "
            f"{len(self._adapters)} 个适配器, "
            f"{len(self._tool_mapping)} 个工具映射"
        )

    def get_handler(self, tool_name: str, agent_name: str = "") -> Callable:
        """
        获取工具的 handler 函数

        返回一个 async callable，可以直接传给 MCPTool 的 handler 参数。

        参数:
            tool_name: 工具名称（如 "query_order_details"）
            agent_name: 调用方 Agent 名称（如 "order_management"）

        返回:
            async callable(**kwargs) → dict
        """
        if tool_name not in self._tool_mapping:
            # 工具未注册到适配器 → 返回降级 handler
            logger.warning(f"[AdapterRegistry] 工具 '{tool_name}' 未注册适配器，使用降级模式")
            return self._fallback_handler(tool_name, agent_name)

        adapter_name, adapter = self._tool_mapping[tool_name]

        async def handler(**kwargs):
            """异步 handler — 通过适配器执行工具调用"""
            # 注入工具名（用于适配器内部路由）
            kwargs["_tool_name"] = tool_name

            request = ToolRequest(
                tool_name=tool_name,
                agent_name=agent_name,
                arguments=kwargs,
            )

            try:
                response = await adapter.execute(request)
                if response.status == AdapterStatus.SUCCESS:
                    # 直接返回数据，MCPServer.call_tool() 会包装为 {"success": True, "result": ...}
                    return response.data
                else:
                    raise RuntimeError(response.error or "适配器执行失败")
            except Exception as e:
                logger.error(f"[AdapterRegistry] {tool_name} 执行异常: {e}")
                raise

        return handler

    def _fallback_handler(self, tool_name: str, agent_name: str) -> Callable:
        """降级 handler — 当工具未注册适配器时使用"""

        async def handler(**kwargs):
            from core.mcp.tools import _fallback_mock
            return _fallback_mock(tool_name, kwargs)

        return handler

    def get_all_adapter_tools(self) -> Dict[str, list]:
        """获取所有已注册适配器的工具列表"""
        result = {}
        for tool_name, (adapter_name, _) in self._tool_mapping.items():
            if adapter_name not in result:
                result[adapter_name] = []
            result[adapter_name].append(tool_name)
        return result

    async def close(self):
        """关闭所有适配器"""
        for adapter in self._adapters.values():
            if hasattr(adapter, 'close'):
                await adapter.close()
        logger.info("[AdapterRegistry] 所有适配器已关闭")


# ============================================================
# 全局单例
# ============================================================

_registry: Optional[AdapterRegistry] = None


async def get_adapter_registry(database_url: str = None) -> AdapterRegistry:
    """获取适配器注册中心单例"""
    global _registry
    if _registry is None:
        _registry = AdapterRegistry()
        await _registry.initialize(database_url)
    return _registry


def reset_registry():
    """重置注册中心（用于测试）"""
    global _registry
    _registry = None