"""
MCP 外部工具适配器层
====================
将 MCP 工具调用桥接到真实的外部服务（数据库、API、向量检索等）。

架构：
  MCP Tool (tools.py)
       │
       ▼
  Adapter (适配器 - 统一接口)
       │
       ├── DatabaseAdapter  → PostgreSQL / SQLite
       ├── ExternalAPIAdapter → HTTP 外部 API
       ├── VectorSearchAdapter → ChromaDB / pgvector
       └── ... (可扩展)
       │
       ▼
  外部服务 (真实数据源)

调用链路：
  User Query → Supervisor → Expert Agent → MCPServer.call_tool()
    → tool.handler(**args) → adapter.execute(request)
      → 权限检查 → 超时控制 → 重试 → 调用外部服务 → 返回结果
"""

from core.mcp.adapters.base import (
    ToolRequest,
    ToolResponse,
    ToolAdapter,
    AdapterStatus,
)
from core.mcp.adapters.security import PermissionGuard, RateLimiter
from core.mcp.adapters.retry import RetryConfig, retry_with_backoff
from core.mcp.adapters.database import DatabaseAdapter
from core.mcp.adapters.external_api import ExternalAPIAdapter

__all__ = [
    "ToolRequest",
    "ToolResponse",
    "ToolAdapter",
    "AdapterStatus",
    "PermissionGuard",
    "RateLimiter",
    "RetryConfig",
    "retry_with_backoff",
    "DatabaseAdapter",
    "ExternalAPIAdapter",
]