"""
Expert Agent 基类
=================
所有 Expert Agent 继承此基类，实现统一的接口规范。

每个 Expert Agent 遵循 ReAct 模式：
- Thought（思考）: 分析任务，确定需要调用哪些工具
- Action（行动）: 调用 MCP 工具执行具体操作
- Observation（观察）: 分析工具返回结果
- Final Answer（最终答案）: 生成领域专业回复

Expert Agent 与 MCP 的关系：
- 每个 Expert 是一个 MCP Server
- 每个 Expert 的工具通过 MCP 协议暴露
- Supervisor 通过 MCP Client 调用 Expert 的工具
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from config.settings import AgentRole
from core.state import (
    MainGraphState, TaskStatus, TaskRecord,
    map_main_to_expert, map_expert_to_main,
    create_initial_expert_state
)
from core.mcp.protocol import MCPServer, MCPServerInfo, MCPTool, MCPToolCategory, create_mcp_server
from core.mcp.tools import get_tools_for_agent

logger = logging.getLogger(__name__)


class ExpertAgent(ABC):
    """
    Expert Agent 基类

    所有 Expert Agent 的通用接口：
    - run(): 执行主任务（ReAct 循环）
    - think(): 分析任务
    - act(): 执行工具调用
    - observe(): 分析结果
    - final_answer(): 生成最终答案
    """

    def __init__(self, role: AgentRole, description: str = ""):
        self.role = role
        self.description = description
        self.mcp_server: Optional[MCPServer] = None
        self._task_history: List[TaskRecord] = []
        self._init_mcp_server()

    def _init_mcp_server(self):
        """初始化 MCP Server，注册工具"""
        server_info = MCPServerInfo(
            name=self.role.value,
            version="1.0.0",
            description=self.description,
        )
        self.mcp_server = MCPServer(server_info)

        # 注册工具
        tools = get_tools_for_agent(self.role.value)
        self.mcp_server.register_tools(tools)

        # 注册特定于该 Expert 的提示词
        self._register_prompts()

    def _register_prompts(self):
        """子类可重写，注册特定提示词"""
        pass

    # ================================================================
    # ReAct 核心方法
    # ================================================================
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expert Agent 执行入口

        参数:
            state: Expert 子图状态（从 MainGraphState 映射而来）

        返回:
            Expert 执行结果（将映射回 MainGraphState）
        """
        self._task_history = []
        max_iterations = 5

        for iteration in range(max_iterations):
            logger.info(f"[{self.role.value}] ReAct 迭代 {iteration + 1}/{max_iterations}")

            # Thought: 分析当前状态，决定下一步
            thought = await self.think(state)

            if thought.get("action") == "FINISH":
                break

            # Action: 执行工具调用
            action_result = await self.act(state, thought)

            # Observation: 分析结果，更新状态（可能同时修改 thought 推进到下一步）
            state = await self.observe(state, thought, action_result)

            # 检查 observe 是否将 thought 设置为 FINISH（多步计划模式）
            if thought.get("action") == "FINISH":
                break

        # Final Answer: 生成最终答案
        final_result = await self.final_answer(state)

        # 合并状态
        state.update(final_result)
        return state

    @abstractmethod
    async def think(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thought 阶段：分析当前状态，推理下一步行动

        返回: {"action": "tool_name" | "FINISH", "reasoning": "...", "tool_args": {...}}
        """
        pass

    @abstractmethod
    async def act(self, state: Dict[str, Any],
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        """
        Action 阶段：执行具体操作

        返回: {"success": bool, "result": Any, "error": Optional[str]}
        """
        pass

    @abstractmethod
    async def observe(self, state: Dict[str, Any],
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Observation 阶段：分析行动结果，更新状态

        返回: 更新后的状态
        """
        pass

    @abstractmethod
    async def final_answer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Final Answer 阶段：生成最终答案

        返回: 包含最终答案的状态更新
        """
        pass

    # ================================================================
    # 工具调用辅助方法
    # ================================================================
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """通过 MCP Server 调用工具"""
        if not self.mcp_server:
            raise RuntimeError(f"MCP Server 未初始化: {self.role.value}")
        return await self.mcp_server.call_tool(tool_name, arguments)

    def get_available_tools(self) -> List[dict]:
        """获取可用工具列表"""
        return self.mcp_server.list_tools() if self.mcp_server else []

    # ================================================================
    # 通用方法
    # ================================================================
    def _record_task(self, task_id: str, description: str, status: TaskStatus,
                     input_data: dict = None, output_data: dict = None):
        """记录任务执行"""
        self._task_history.append(TaskRecord(
            task_id=task_id,
            agent=self.role.value,
            description=description,
            status=status,
            input_data=input_data or {},
            output_data=output_data or {},
            started_at=datetime.now().isoformat(),
        ))

    def get_task_history(self) -> List[TaskRecord]:
        return self._task_history