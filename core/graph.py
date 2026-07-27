"""
LangGraph 主图构建 - Supervisor-Expert 协作编排
================================================
基于 LangGraph 的 StateGraph 实现 Supervisor-Expert 多智能体协作

图结构:
                    ┌─────────────┐
                    │  __start__  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Supervisor │  ← 主控节点：ReAct 路由决策
                    │    Node     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐ ┌─────▼─────┐ ┌───▼────────┐
     │ Market     │ │Advertising│ │ Customer   │  ...
     │ Research   │ │  Expert   │ │ Service    │
     │ Subgraph   │ │ Subgraph  │ │ Subgraph   │
     └────────┬───┘ └─────┬─────┘ └───┬────────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │  Aggregate  │  ← 结果聚合节点
                    │    Node     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  __end__    │
                    └─────────────┘

状态映射:
  MainGraphState ──map_main_to_expert()──► ExpertSubgraphState
  ExpertSubgraphState ──map_expert_to_main()──► MainGraphState
"""

import logging
import asyncio
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime

from config.settings import AgentRole, system_config
from core.state import (
    MainGraphState, TaskStatus,
    map_main_to_expert, map_expert_to_main,
    create_initial_main_state, create_initial_expert_state
)
from core.supervisor import SupervisorAgent
from core.experts.base import ExpertAgent
from core.experts.market_research import MarketResearchAgent
from core.experts.advertising import AdvertisingAgent
from core.experts.customer_service import CustomerServiceAgent
from core.experts.supply_chain import SupplyChainAgent
from core.experts.order_management import OrderManagementAgent
from core.experts.recommendation import RecommendationAgent
from core.experts.inventory import InventoryAgent
from core.experts.payment import PaymentAgent
from core.experts.logistics import LogisticsAgent
from core.experts.marketing import MarketingAgent
from core.experts.user_behavior import UserBehaviorAgent
from core.mcp.protocol import MCPRouter, MCPServer, MCPClient, create_mcp_server
from core.mcp.tools import AGENT_TOOLS_REGISTRY, get_tools_for_agent

logger = logging.getLogger(__name__)


# ============================================================
# Agent 工厂
# ============================================================
class AgentFactory:
    """Agent 工厂 - 创建和管理所有 Expert Agent 实例"""

    _agent_classes = {
        AgentRole.MARKET_RESEARCH: MarketResearchAgent,
        AgentRole.ADVERTISING: AdvertisingAgent,
        AgentRole.CUSTOMER_SERVICE: CustomerServiceAgent,
        AgentRole.SUPPLY_CHAIN: SupplyChainAgent,
        AgentRole.ORDER_MANAGEMENT: OrderManagementAgent,
        AgentRole.RECOMMENDATION: RecommendationAgent,
        AgentRole.INVENTORY: InventoryAgent,
        AgentRole.PAYMENT: PaymentAgent,
        AgentRole.LOGISTICS: LogisticsAgent,
        AgentRole.MARKETING: MarketingAgent,
        AgentRole.USER_BEHAVIOR: UserBehaviorAgent,
    }

    @classmethod
    def create_all_agents(cls) -> Dict[str, ExpertAgent]:
        """创建所有 Expert Agent 实例"""
        agents = {}
        for role, agent_class in cls._agent_classes.items():
            agents[role.value] = agent_class()
            logger.info(f"[AgentFactory] 创建 Agent: {role.value}")
        return agents

    @classmethod
    def create_agent(cls, role: AgentRole) -> ExpertAgent:
        """创建单个 Expert Agent"""
        agent_class = cls._agent_classes.get(role)
        if not agent_class:
            raise ValueError(f"未知的 Agent 角色: {role}")
        return agent_class()


# ============================================================
# MCP 初始化
# ============================================================
def init_mcp_router(agents: Dict[str, ExpertAgent]) -> MCPRouter:
    """初始化 MCP Router，注册所有 Agent 的 MCP Server"""
    router = MCPRouter()

    for agent_name, agent in agents.items():
        if agent.mcp_server:
            router.register_agent(agent.mcp_server)
            logger.info(f"[MCP Init] 注册 Agent MCP Server: {agent_name}")

    return router


# ============================================================
# LangGraph 节点函数
# ============================================================
# 注意：以下代码为 LangGraph 标准模式的实现框架
# 在实际部署时需要安装 langgraph 并调整导入

class MultiAgentGraph:
    """
    多智能体协作图 - 封装所有 LangGraph 节点和边

    使用方式：
        graph = MultiAgentGraph()
        result = await graph.run("帮我分析美国市场的蓝牙耳机选品")
    """

    def __init__(self):
        # 初始化 LLM
        try:
            self.llm = system_config.get_llm_instance()
            logger.info(f"[Graph] LLM 初始化完成: {system_config.llm.provider}/{system_config.llm.model_name}")
        except Exception as e:
            logger.warning(f"[Graph] LLM 初始化失败: {e}，使用降级模式")
            self.llm = None

        # 设置 MCP 工具的 LLM
        from core.mcp.tools import set_llm
        if self.llm:
            set_llm(self.llm)

        # 初始化 Agent
        self.agents = AgentFactory.create_all_agents()
        self.mcp_router = init_mcp_router(self.agents)
        self.supervisor = SupervisorAgent(mcp_router=self.mcp_router, llm=self.llm)

        # 适配器注册中心（延迟初始化）
        self._adapter_initialized = False

    async def _ensure_adapters(self):
        """确保适配器注册中心已初始化（懒加载，只执行一次）"""
        if self._adapter_initialized:
            return
        try:
            from core.mcp.adapters.registry import get_adapter_registry
            from core.mcp.tools import set_adapter_registry
            registry = await get_adapter_registry()
            set_adapter_registry(registry)
            self._adapter_initialized = True
            logger.info("[Graph] 适配器注册中心已初始化")
        except Exception as e:
            logger.warning(f"[Graph] 适配器注册中心初始化失败: {e}，使用 mock 降级")
            self._adapter_initialized = True  # 不再重试

    # ---- 节点函数 ----

    async def supervisor_node(self, state: MainGraphState) -> Dict[str, Any]:
        """
        Supervisor 节点 - ReAct 路由决策

        输入: MainGraphState
        输出: 状态更新（routing_decision, next_agent）
        """
        logger.info(f"[Graph] Supervisor 节点: iteration={state.get('iteration_count', 0)}")

        # 检查最大迭代次数
        if state.get("iteration_count", 0) >= system_config.max_agent_iterations:
            logger.warning("[Graph] 达到最大迭代次数，强制结束")
            return {
                "next_agent": "FINISH",
                "final_answer": "任务执行达到最大迭代次数限制，已返回当前收集到的结果。",
                "iteration_count": state["iteration_count"] + 1,
            }

        # Thought: Supervisor 分析并决策
        decision = await self.supervisor.think(state)

        return {
            "routing_decision": {
                "next_agent": decision.next_agent,
                "reasoning": decision.reasoning,
                "task_description": decision.task_description,
                "requires_multi_agent": decision.requires_multi_agent,
                "agent_sequence": decision.agent_sequence,
            },
            "next_agent": decision.next_agent,
            "current_task": decision.task_description,
            "iteration_count": state["iteration_count"] + 1,
        }

    async def expert_node(self, state: MainGraphState) -> Dict[str, Any]:
        """
        Expert 节点 - 执行 Expert Agent 子图

        1. 从 MainGraphState 映射到 ExpertSubgraphState
        2. 执行 Expert Agent 的 ReAct 循环
        3. 将结果映射回 MainGraphState
        """
        expert_name = state.get("next_agent", "")
        if not expert_name or expert_name == "FINISH":
            return {}

        logger.info(f"[Graph] Expert 节点: {expert_name}")

        agent = self.agents.get(expert_name)
        if not agent:
            logger.error(f"[Graph] 未知 Agent: {expert_name}")
            return {
                "expert_outputs": {expert_name: {"error": f"未知 Agent: {expert_name}"}},
                "next_agent": "FINISH",
            }

        # Step 1: MainGraphState → ExpertSubgraphState
        expert_state = create_initial_expert_state(expert_name, state)

        # Step 2: 执行 Expert Agent
        try:
            result_state = await agent.run(expert_state)
        except Exception as e:
            logger.error(f"[Graph] Expert 执行失败: {expert_name} - {e}")
            return {
                "expert_outputs": {expert_name: {"error": str(e)}},
                "next_agent": "FINISH",
            }

        # Step 3: ExpertSubgraphState → MainGraphState
        updates = map_expert_to_main(result_state, expert_name, state)

        # 累积 expert_outputs（merge 而非覆盖）
        existing_outputs = dict(state.get("expert_outputs", {}))
        new_outputs = updates.get("expert_outputs", {})
        existing_outputs.update(new_outputs)
        updates["expert_outputs"] = existing_outputs

        # 添加路由信息
        updates["next_agent"] = "supervisor"  # 返回 Supervisor 继续决策

        return updates

    async def aggregate_node(self, state: MainGraphState) -> Dict[str, Any]:
        """
        聚合节点 - 整合所有 Expert 输出，生成最终答案
        """
        logger.info("[Graph] 聚合节点: 生成最终答案")

        final_answer = await self.supervisor.final_answer(state)

        return {
            "final_answer": final_answer,
            "next_agent": "FINISH",
        }

    # ---- 路由函数 ----

    def route_after_supervisor(self, state: MainGraphState) -> str:
        """Supervisor 节点后的路由"""
        next_agent = state.get("next_agent", "FINISH")

        if next_agent == "FINISH":
            return "aggregate"
        elif next_agent in self.agents:
            return "expert"
        else:
            logger.warning(f"[Graph] 未知路由目标: {next_agent}")
            return "aggregate"

    def route_after_expert(self, state: MainGraphState) -> str:
        """Expert 节点后的路由"""
        next_agent = state.get("next_agent", "FINISH")

        if next_agent == "FINISH":
            return "aggregate"
        elif next_agent == "supervisor":
            return "supervisor"
        else:
            return "aggregate"

    # ---- 图构建 ----

    def build_graph(self):
        """
        构建 LangGraph StateGraph

        使用 langgraph 库时取消注释以下代码：

        from langgraph.graph import StateGraph, END

        workflow = StateGraph(MainGraphState)

        # 添加节点
        workflow.add_node("supervisor", self.supervisor_node)
        workflow.add_node("expert", self.expert_node)
        workflow.add_node("aggregate", self.aggregate_node)

        # 设置入口
        workflow.set_entry_point("supervisor")

        # 添加边
        workflow.add_conditional_edges(
            "supervisor",
            self.route_after_supervisor,
            {
                "expert": "expert",
                "aggregate": "aggregate",
            }
        )

        workflow.add_conditional_edges(
            "expert",
            self.route_after_expert,
            {
                "supervisor": "supervisor",
                "aggregate": "aggregate",
            }
        )

        workflow.add_edge("aggregate", END)

        return workflow.compile()
        """
        logger.info("[Graph] 图结构已定义（需要 langgraph 库来编译）")
        return None

    # ---- 运行入口 ----

    async def run(self, user_query: str, user_context: dict = None) -> Dict[str, Any]:
        """
        运行多智能体协作图

        参数:
            user_query: 用户查询
            user_context: 用户上下文信息

        返回:
            包含 final_answer 和 expert_outputs 的字典
        """
        logger.info(f"[Graph] 开始执行: {user_query}")

        # 确保适配器已初始化（懒加载）
        await self._ensure_adapters()

        # 初始化状态
        state = create_initial_main_state(user_query, user_context)

        max_iterations = system_config.max_agent_iterations

        for i in range(max_iterations):
            # Supervisor 决策
            state.update(await self.supervisor_node(state))

            next_agent = state.get("next_agent", "FINISH")
            if next_agent == "FINISH":
                break

            # Expert 执行
            state.update(await self.expert_node(state))

            next_agent = state.get("next_agent", "FINISH")
            if next_agent == "FINISH":
                break

        # 聚合最终答案
        state.update(await self.aggregate_node(state))

        logger.info(f"[Graph] 执行完成，迭代 {state.get('iteration_count', 0)} 次")

        return {
            "final_answer": state.get("final_answer", ""),
            "expert_outputs": state.get("expert_outputs", {}),
            "task_history": state.get("task_history", []),
            "session_id": state.get("session_id", ""),
            "iteration_count": state.get("iteration_count", 0),
        }


# ============================================================
# LangGraph 图构建（兼容 langgraph 库）
# ============================================================
def build_langgraph():
    """
    使用 langgraph 库构建可编译的 StateGraph

    使用方式:
        from langgraph.graph import StateGraph, END
        graph = build_langgraph()
        compiled = graph.compile()
        result = compiled.invoke({"user_query": "..."})
    """
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        logger.warning("langgraph 未安装，使用回退模式")
        return None

    graph_instance = MultiAgentGraph()

    workflow = StateGraph(MainGraphState)

    # 添加节点
    workflow.add_node("supervisor", graph_instance.supervisor_node)
    workflow.add_node("expert", graph_instance.expert_node)
    workflow.add_node("aggregate", graph_instance.aggregate_node)

    # 设置入口
    workflow.set_entry_point("supervisor")

    # 条件边
    workflow.add_conditional_edges(
        "supervisor",
        graph_instance.route_after_supervisor,
        {"expert": "expert", "aggregate": "aggregate"}
    )
    workflow.add_conditional_edges(
        "expert",
        graph_instance.route_after_expert,
        {"supervisor": "supervisor", "aggregate": "aggregate"}
    )

    # 结束边
    workflow.add_edge("aggregate", END)

    return workflow.compile()