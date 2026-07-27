"""
MCP (Model Context Protocol) 协议实现
=====================================
为每个 Expert Agent 提供标准化的工具注册、调用和通信能力

MCP 协议核心概念：
- Server: 每个 Agent 作为一个 MCP Server，暴露工具能力
- Client: Supervisor 作为 MCP Client，调用各 Agent 的工具
- Tool: 每个 Agent 暴露的具体能力（函数）
- Resource: 共享数据资源（数据库、知识库等）
- Prompt: 预定义的提示词模板

通信流程：
  Supervisor (MCP Client)
       │
       │  1. discover_tools(agent_name)
       ▼
  MCP Router ──────────────────────────────────┐
       │                                        │
       │  2. call_tool(agent, tool, args)       │
       ▼                                        │
  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
  │ MCP      │  │ MCP      │  │ MCP      │     │
  │ Server A │  │ Server B │  │ Server C │ ... │
  │ (Expert  │  │ (Expert  │  │ (Expert  │     │
  │  Agent)  │  │  Agent)  │  │  Agent)  │     │
  └──────────┘  └──────────┘  └──────────┘     │
       │            │            │              │
       ▼            ▼            ▼              │
  ┌──────────────────────────────────────────┐  │
  │          Shared Resources                │  │
  │  (Database, Knowledge Base, APIs...)     │◄─┘
  └──────────────────────────────────────────┘
"""

import json
import logging
import inspect
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================
# MCP 协议核心数据模型
# ============================================================
class MCPToolCategory(str, Enum):
    SEARCH = "search"       # 搜索类
    ANALYSIS = "analysis"   # 分析类
    ACTION = "action"       # 执行类
    QUERY = "query"         # 查询类
    GENERATION = "generation"  # 生成类


@dataclass
class MCPTool:
    """MCP 工具定义"""
    name: str
    description: str
    category: MCPToolCategory
    parameters: Dict[str, Any]  # JSON Schema 格式的参数定义
    handler: Callable  # 工具执行函数
    agent_name: str = ""
    timeout_seconds: int = 30
    requires_auth: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": self.parameters,
            "agent_name": self.agent_name,
            "timeout_seconds": self.timeout_seconds,
            "requires_auth": self.requires_auth,
            "tags": self.tags,
        }

    def to_json_schema(self) -> dict:
        """生成 JSON Schema 格式的工具描述"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class MCPResource:
    """MCP 资源定义（共享数据）"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    data: Any = None


@dataclass
class MCPPrompt:
    """MCP 提示词模板"""
    name: str
    description: str
    template: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MCPServerInfo:
    """MCP Server 信息"""
    name: str
    version: str
    description: str
    tools: List[MCPTool] = field(default_factory=list)
    resources: List[MCPResource] = field(default_factory=list)
    prompts: List[MCPPrompt] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=lambda: {
        "tools": {},
        "resources": {},
        "prompts": {},
        "logging": {},
    })


# ============================================================
# MCP Server 实现
# ============================================================
class MCPServer:
    """
    MCP Server - 每个 Expert Agent 对应一个 MCP Server
    负责注册工具、处理工具调用请求、返回执行结果
    """

    def __init__(self, server_info: MCPServerInfo):
        self.info = server_info
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, MCPPrompt] = {}
        self._call_history: List[dict] = []

    # ---- 工具注册 ----
    def register_tool(self, tool: MCPTool) -> None:
        """注册一个 MCP 工具"""
        tool.agent_name = self.info.name
        self._tools[tool.name] = tool
        self.info.tools.append(tool)
        logger.info(f"[MCP Server:{self.info.name}] 注册工具: {tool.name}")

    def register_tools(self, tools: List[MCPTool]) -> None:
        """批量注册工具"""
        for tool in tools:
            self.register_tool(tool)

    # ---- 资源注册 ----
    def register_resource(self, resource: MCPResource) -> None:
        self._resources[resource.uri] = resource
        self.info.resources.append(resource)

    # ---- 提示词注册 ----
    def register_prompt(self, prompt: MCPPrompt) -> None:
        self._prompts[prompt.name] = prompt
        self.info.prompts.append(prompt)

    # ---- 工具调用 ----
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用指定工具（兼容同步和异步 handler）
        返回格式: {"success": bool, "result": Any, "error": Optional[str]}
        """
        start_time = datetime.now()

        if tool_name not in self._tools:
            return {
                "success": False,
                "error": f"工具 '{tool_name}' 未注册在 Server '{self.info.name}' 中",
                "result": None
            }

        tool = self._tools[tool_name]
        try:
            # 兼容同步和异步 handler
            handler_result = tool.handler(**arguments)
            if inspect.iscoroutine(handler_result):
                result = await handler_result
            else:
                result = handler_result

            duration = (datetime.now() - start_time).total_seconds() * 1000
            self._log_call(tool_name, arguments, result, duration, success=True)

            return {
                "success": True,
                "result": result,
                "error": None,
                "duration_ms": duration,
                "tool_name": tool_name,
                "agent_name": self.info.name,
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self._log_call(tool_name, arguments, str(e), duration, success=False)
            logger.error(f"[MCP Server:{self.info.name}] 工具调用失败: {tool_name} - {e}")

            return {
                "success": False,
                "error": str(e),
                "result": None,
                "duration_ms": duration,
                "tool_name": tool_name,
                "agent_name": self.info.name,
            }

    def _log_call(self, tool_name: str, args: dict, result: Any,
                  duration_ms: float, success: bool):
        """记录工具调用历史"""
        self._call_history.append({
            "tool_name": tool_name,
            "arguments": args,
            "result_summary": str(result)[:200] if success else result,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        })

    # ---- 工具发现 ----
    def list_tools(self) -> List[dict]:
        """列出所有工具"""
        return [t.to_dict() for t in self._tools.values()]

    def get_tool_schema(self, tool_name: str) -> Optional[dict]:
        """获取工具 Schema"""
        tool = self._tools.get(tool_name)
        return tool.to_json_schema() if tool else None

    # ---- 资源访问 ----
    def read_resource(self, uri: str) -> Optional[Any]:
        """读取资源"""
        resource = self._resources.get(uri)
        return resource.data if resource else None

    # ---- 提示词获取 ----
    def get_prompt(self, name: str, arguments: dict = None) -> Optional[str]:
        """获取并填充提示词模板"""
        prompt = self._prompts.get(name)
        if not prompt:
            return None
        template = prompt.template
        if arguments:
            for key, value in arguments.items():
                template = template.replace(f"{{{key}}}", str(value))
        return template


# ============================================================
# MCP Client 实现
# ============================================================
class MCPClient:
    """
    MCP Client - Supervisor 使用 MCP Client 调用各 Expert Agent 的工具
    负责工具发现、工具调用、结果聚合
    """

    def __init__(self):
        self._servers: Dict[str, MCPServer] = {}
        self._tool_registry: Dict[str, List[str]] = {}  # agent_name -> [tool_names]

    def register_server(self, server: MCPServer) -> None:
        """注册一个 MCP Server（即注册一个 Expert Agent）"""
        self._servers[server.info.name] = server
        self._tool_registry[server.info.name] = list(server._tools.keys())
        logger.info(f"[MCP Client] 注册 Server: {server.info.name} "
                    f"(工具数: {len(server._tools)})")

    def register_servers(self, servers: List[MCPServer]) -> None:
        """批量注册 Server"""
        for server in servers:
            self.register_server(server)

    # ---- 工具发现 ----
    def discover_tools(self, agent_name: str = None) -> List[dict]:
        """
        发现工具
        - 指定 agent_name: 返回该 Agent 的工具列表
        - 不指定: 返回所有 Agent 的工具列表
        """
        if agent_name:
            server = self._servers.get(agent_name)
            return server.list_tools() if server else []
        else:
            all_tools = []
            for server in self._servers.values():
                all_tools.extend(server.list_tools())
            return all_tools

    def get_all_tools_schema(self) -> List[dict]:
        """获取所有工具的 JSON Schema（用于 LLM function calling）"""
        schemas = []
        for server in self._servers.values():
            for tool_name in server._tools:
                schema = server.get_tool_schema(tool_name)
                if schema:
                    schemas.append(schema)
        return schemas

    # ---- 工具调用 ----
    async def call_tool(self, agent_name: str, tool_name: str,
                        arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用指定 Agent 的工具
        """
        server = self._servers.get(agent_name)
        if not server:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' 未注册",
                "result": None
            }
        return await server.call_tool(tool_name, arguments)

    # ---- 批量调用（多 Agent 协作） ----
    async def call_tools_parallel(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        并行调用多个 Agent 的工具
        calls: [{"agent_name": ..., "tool_name": ..., "arguments": {...}}, ...]
        """
        import asyncio
        tasks = [
            self.call_tool(c["agent_name"], c["tool_name"], c.get("arguments", {}))
            for c in calls
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            {"success": False, "error": str(r), "result": None}
            if isinstance(r, Exception) else r
            for r in results
        ]

    # ---- 获取 Server 信息 ----
    def get_server_info(self, agent_name: str) -> Optional[MCPServerInfo]:
        server = self._servers.get(agent_name)
        return server.info if server else None

    def list_agents(self) -> List[str]:
        return list(self._servers.keys())


# ============================================================
# MCP Router - 统一路由层
# ============================================================
class MCPRouter:
    """
    MCP 路由器 - 统一管理所有 Agent 的 MCP 通信
    提供：
    1. 工具发现路由
    2. 工具调用路由
    3. 负载均衡
    4. 调用链追踪
    """

    def __init__(self):
        self.client = MCPClient()
        self._call_trace: List[dict] = []

    def register_agent(self, server: MCPServer) -> None:
        self.client.register_server(server)

    async def route_tool_call(self, agent_name: str, tool_name: str,
                              arguments: Dict[str, Any]) -> Dict[str, Any]:
        """路由工具调用并记录追踪"""
        result = await self.client.call_tool(agent_name, tool_name, arguments)
        self._call_trace.append({
            "agent_name": agent_name,
            "tool_name": tool_name,
            "arguments": arguments,
            "success": result.get("success", False),
            "timestamp": datetime.now().isoformat(),
        })
        return result

    def get_trace(self) -> List[dict]:
        return self._call_trace

    def get_trace_summary(self) -> str:
        """生成调用链摘要"""
        lines = ["MCP 调用链追踪:"]
        for i, trace in enumerate(self._call_trace, 1):
            status = "[OK]" if trace["success"] else "[FAIL]"
            lines.append(
                f"  {i}. [{status}] {trace['agent_name']}.{trace['tool_name']}"
            )
        return "\n".join(lines)


# ============================================================
# 工具定义工厂
# ============================================================
def create_mcp_tool(
    name: str,
    description: str,
    category: MCPToolCategory,
    parameters: Dict[str, Any],
    handler: Callable,
    **kwargs
) -> MCPTool:
    """创建 MCP 工具的标准工厂函数"""
    return MCPTool(
        name=name,
        description=description,
        category=category,
        parameters=parameters,
        handler=handler,
        **kwargs
    )


def create_mcp_server(
    name: str,
    version: str = "1.0.0",
    description: str = "",
    tools: List[MCPTool] = None,
) -> MCPServer:
    """创建 MCP Server 的标准工厂函数"""
    server_info = MCPServerInfo(
        name=name,
        version=version,
        description=description,
    )
    server = MCPServer(server_info)
    if tools:
        server.register_tools(tools)
    return server