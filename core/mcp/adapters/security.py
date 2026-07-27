"""
MCP 工具权限控制与安全验证
===========================
为 MCP 工具调用提供 API Key 验证和频率限制。

权限模型：
  1. API Key 验证：每个 Agent 调用工具时需要携带有效的 API Key
  2. 频率限制：每个工具在每个时间窗口内限制调用次数
  3. 工具白名单：每个 Agent 只能调用其被授权的工具
"""

import logging
import time
from collections import defaultdict
from typing import Any, Dict, Optional, Set, Tuple

from core.mcp.adapters.base import ToolRequest

logger = logging.getLogger(__name__)


class PermissionGuard:
    """
    权限守卫 — 检查工具调用是否被授权

    验证层级：
    1. API Key 是否存在且有效
    2. 调用方 Agent 是否有权限使用该工具
    3. 是否超过频率限制
    """

    def __init__(self):
        # Agent → 允许的工具白名单
        self._tool_allowlist: Dict[str, Set[str]] = {}
        # 有效的 API Key 集合
        self._valid_api_keys: Set[str] = set()
        # 是否启用 API Key 验证（开发环境可关闭）
        self._require_api_key: bool = True

    def configure(
        self,
        api_keys: list = None,
        tool_allowlist: Dict[str, list] = None,
        require_api_key: bool = True,
    ):
        """
        配置权限规则

        参数:
            api_keys: 有效的 API Key 列表
            tool_allowlist: {agent_name: [tool_name, ...]}
            require_api_key: 是否要求 API Key
        """
        if api_keys:
            self._valid_api_keys.update(api_keys)
        if tool_allowlist:
            for agent, tools in tool_allowlist.items():
                self._tool_allowlist[agent] = set(tools)
        self._require_api_key = require_api_key
        logger.info(
            f"[PermissionGuard] 已配置: {len(self._valid_api_keys)} 个 API Key, "
            f"{len(self._tool_allowlist)} 个 Agent 白名单"
        )

    async def check(self, request: ToolRequest) -> Tuple[bool, str]:
        """
        检查工具调用权限

        返回: (是否允许, 拒绝原因)
        """
        # 1. API Key 验证
        if self._require_api_key:
            if not request.caller_api_key:
                return False, "缺少 API Key"
            if request.caller_api_key not in self._valid_api_keys:
                return False, f"无效的 API Key: {request.caller_api_key[:8]}..."

        # 2. 工具白名单检查
        if self._tool_allowlist:
            agent_tools = self._tool_allowlist.get(request.agent_name, set())
            if agent_tools and request.tool_name not in agent_tools:
                return False, (
                    f"Agent '{request.agent_name}' 无权调用工具 '{request.tool_name}'"
                )

        return True, ""


class RateLimiter:
    """
    频率限制器 — 滑动窗口算法

    防止某个 Agent 或工具被过度调用。
    """

    def __init__(self, window_seconds: int = 60, max_calls: int = 100):
        """
        参数:
            window_seconds: 时间窗口（秒）
            max_calls: 窗口内最大调用次数
        """
        self.window_seconds = window_seconds
        self.max_calls = max_calls
        # {key: [timestamp1, timestamp2, ...]}
        self._call_history: Dict[str, list] = defaultdict(list)

    async def check(self, request: ToolRequest) -> Tuple[bool, str]:
        """
        检查是否超过频率限制

        返回: (是否允许, 拒绝原因)
        """
        key = f"{request.agent_name}:{request.tool_name}"
        now = time.time()
        window_start = now - self.window_seconds

        # 清理过期记录
        self._call_history[key] = [
            t for t in self._call_history[key] if t > window_start
        ]

        if len(self._call_history[key]) >= self.max_calls:
            remaining = self._call_history[key][0] - window_start
            return False, (
                f"频率限制: {self.window_seconds}s 内最多 {self.max_calls} 次调用，"
                f"请在 {remaining:.0f}s 后重试"
            )

        # 记录本次调用
        self._call_history[key].append(now)
        return True, ""

    def get_usage(self, agent_name: str, tool_name: str = None) -> Dict[str, Any]:
        """获取当前使用统计"""
        now = time.time()
        window_start = now - self.window_seconds
        result = {}

        for key, timestamps in self._call_history.items():
            if tool_name and not key.endswith(f":{tool_name}"):
                continue
            if agent_name and not key.startswith(f"{agent_name}:"):
                continue
            active = [t for t in timestamps if t > window_start]
            result[key] = {
                "current_calls": len(active),
                "max_calls": self.max_calls,
                "window_seconds": self.window_seconds,
                "remaining": max(0, self.max_calls - len(active)),
            }

        return result