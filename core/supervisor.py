"""
Supervisor Agent（主控 Agent）
=============================
基于 ReAct (Reasoning + Acting) 模式的 Supervisor：
- Thought: 分析用户请求，推理需要哪个 Expert
- Action: 路由到对应 Expert Agent
- Observation: 收集 Expert 执行结果
- Final Answer: 整合结果，生成最终答案

支持：
1. 单 Agent 路由：简单任务直接分配给一个 Expert
2. 多 Agent 编排：复杂任务按顺序调用多个 Expert
3. 并行调用：独立子任务并行执行
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from config.settings import (
    AgentRole, SUPERVISOR_SYSTEM_PROMPT, system_config
)
from core.state import (
    MainGraphState, RoutingDecision, TaskRecord, TaskStatus,
    map_main_to_expert, map_expert_to_main,
    create_initial_expert_state
)
from core.mcp.protocol import MCPRouter, MCPServer, MCPClient
from core.mcp.tools import get_tools_for_agent

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent - 主控智能体

    核心职责：
    1. 意图识别与任务分解
    2. 路由决策（单 Agent / 多 Agent 编排）
    3. 结果整合与最终答案生成
    4. 异常处理与降级策略

    ReAct 思考流程：
    ┌──────────────────────────────────────────────┐
    │  Thought: 用户想做什么？需要哪些 Agent？       │
    │     ↓                                        │
    │  Action: 调用 route_to_expert() 路由任务      │
    │     ↓                                        │
    │  Observation: 收集 Expert 返回结果            │
    │     ↓                                        │
    │  Thought: 结果是否满足需求？还需要更多信息？    │
    │     ↓                                        │
    │  Final Answer: 整合所有结果，生成最终回复      │
    └──────────────────────────────────────────────┘
    """

    # 任务关键词 → Agent 映射表（用于快速路由）
    KEYWORD_ROUTING: Dict[str, str] = {
        # 选品/市场
        "选品": AgentRole.MARKET_RESEARCH,
        "市场调研": AgentRole.MARKET_RESEARCH,
        "竞品": AgentRole.MARKET_RESEARCH,
        "市场趋势": AgentRole.MARKET_RESEARCH,
        "选品分析": AgentRole.MARKET_RESEARCH,

        # 广告
        "广告": AgentRole.ADVERTISING,
        "投放": AgentRole.ADVERTISING,
        "推广": AgentRole.ADVERTISING,
        "ROI": AgentRole.ADVERTISING,
        "营销效果": AgentRole.ADVERTISING,

        # 客服
        "客服": AgentRole.CUSTOMER_SERVICE,
        "售后": AgentRole.CUSTOMER_SERVICE,
        "退款": AgentRole.CUSTOMER_SERVICE,
        "投诉": AgentRole.CUSTOMER_SERVICE,
        "咨询": AgentRole.CUSTOMER_SERVICE,
        "FAQ": AgentRole.CUSTOMER_SERVICE,

        # 供应链
        "供应链": AgentRole.SUPPLY_CHAIN,
        "补货": AgentRole.SUPPLY_CHAIN,
        "预测": AgentRole.SUPPLY_CHAIN,
        "供应商": AgentRole.SUPPLY_CHAIN,
        "采购": AgentRole.SUPPLY_CHAIN,

        # 订单
        "订单": AgentRole.ORDER_MANAGEMENT,
        "下单": AgentRole.ORDER_MANAGEMENT,
        "取消订单": AgentRole.ORDER_MANAGEMENT,
        "查订单": AgentRole.ORDER_MANAGEMENT,

        # 推荐
        "推荐": AgentRole.RECOMMENDATION,
        "个性化": AgentRole.RECOMMENDATION,
        "猜你喜欢": AgentRole.RECOMMENDATION,

        # 库存
        "库存": AgentRole.INVENTORY,
        "入库": AgentRole.INVENTORY,
        "出库": AgentRole.INVENTORY,
        "盘点": AgentRole.INVENTORY,

        # 支付
        "支付": AgentRole.PAYMENT,
        "付款": AgentRole.PAYMENT,
        "结算": AgentRole.PAYMENT,
        "对账": AgentRole.PAYMENT,

        # 物流
        "物流": AgentRole.LOGISTICS,
        "快递": AgentRole.LOGISTICS,
        "配送": AgentRole.LOGISTICS,
        "追踪": AgentRole.LOGISTICS,
        "发货": AgentRole.LOGISTICS,

        # 营销
        "促销": AgentRole.MARKETING,
        "优惠券": AgentRole.MARKETING,
        "折扣": AgentRole.MARKETING,
        "活动": AgentRole.MARKETING,

        # 用户行为
        "用户分析": AgentRole.USER_BEHAVIOR,
        "用户行为": AgentRole.USER_BEHAVIOR,
        "用户画像": AgentRole.USER_BEHAVIOR,
        "用户分群": AgentRole.USER_BEHAVIOR,
    }

    # 多 Agent 协作模式定义
    # 当任务涉及多个领域时，定义 Agent 的执行顺序
    MULTI_AGENT_PATTERNS: Dict[str, List[str]] = {
        # 选品 → 广告投放 → 库存准备
        "新品上市": [
            AgentRole.MARKET_RESEARCH,
            AgentRole.ADVERTISING,
            AgentRole.INVENTORY,
        ],
        # 用户下单 → 支付 → 物流
        "下单流程": [
            AgentRole.ORDER_MANAGEMENT,
            AgentRole.PAYMENT,
            AgentRole.LOGISTICS,
        ],
        # 营销活动 → 推荐 → 用户分析
        "营销推荐": [
            AgentRole.MARKETING,
            AgentRole.RECOMMENDATION,
            AgentRole.USER_BEHAVIOR,
        ],
        # 售后处理 → 退款 → 客服
        "售后处理": [
            AgentRole.CUSTOMER_SERVICE,
            AgentRole.PAYMENT,
            AgentRole.LOGISTICS,
        ],
        # 供应链优化 → 库存 → 预测
        "供应链优化": [
            AgentRole.SUPPLY_CHAIN,
            AgentRole.INVENTORY,
        ],
        # 用户分析 → 推荐 → 营销
        "用户增长": [
            AgentRole.USER_BEHAVIOR,
            AgentRole.RECOMMENDATION,
            AgentRole.MARKETING,
        ],
        # 广告分析 → 用户行为 → 推荐优化
        "广告优化": [
            AgentRole.ADVERTISING,
            AgentRole.USER_BEHAVIOR,
            AgentRole.RECOMMENDATION,
        ],
    }

    def __init__(self, mcp_router: MCPRouter, llm=None):
        self.mcp_router = mcp_router
        self.llm = llm  # LangChain LLM 实例
        self._routing_history: List[RoutingDecision] = []

    # ================================================================
    # ReAct 核心方法
    # ================================================================
    async def think(self, state: MainGraphState) -> RoutingDecision:
        """
        Thought 阶段：分析用户请求，制定路由决策

        策略优先级：
        1. LLM 智能路由（有 LLM 时始终优先）
        2. 多 Agent 模式匹配
        3. 关键词快速匹配
        4. 默认降级路由
        """
        user_query = state.get("user_query", "")
        task_history = state.get("task_history", [])
        expert_outputs = state.get("expert_outputs", {})

        # 1. 优先使用 LLM 智能路由
        if self.llm:
            decision = await self._llm_route(state)
            self._routing_history.append(decision)
            return decision

        # 2. 多 Agent 模式匹配
        pattern_match = self._pattern_route(user_query)
        if pattern_match and not task_history:
            decision = RoutingDecision(
                next_agent=pattern_match[0],
                reasoning=f"模式匹配路由: {' → '.join(pattern_match)}",
                task_description=user_query,
                requires_multi_agent=True,
                agent_sequence=pattern_match,
            )
            self._routing_history.append(decision)
            return decision

        # 3. 关键词快速匹配
        keyword_match = self._keyword_route(user_query)
        if keyword_match and not task_history:
            decision = RoutingDecision(
                next_agent=keyword_match,
                reasoning=f"关键词匹配路由到 {keyword_match}",
                task_description=user_query,
            )
            self._routing_history.append(decision)
            return decision

        # 4. 如果已有任务历史且 Expert 已产出结果，路由到 FINISH
        if task_history and expert_outputs:
            decision = RoutingDecision(
                next_agent="FINISH",
                reasoning="Expert 已完成任务，路由到聚合节点",
                task_description=user_query,
            )
            self._routing_history.append(decision)
            return decision

        # 5. 降级：默认路由
        decision = RoutingDecision(
            next_agent=keyword_match or AgentRole.CUSTOMER_SERVICE,
            reasoning="降级路由（LLM 不可用，无关键词匹配）",
            task_description=user_query,
        )

        self._routing_history.append(decision)
        return decision

    async def act(self, state: MainGraphState, decision: RoutingDecision) -> Dict[str, Any]:
        """
        Action 阶段：执行路由决策，调用 Expert Agent
        """
        expert_name = decision.next_agent

        if expert_name == "FINISH":
            return {"status": "finished", "result": state.get("final_answer", "")}

        if decision.requires_multi_agent:
            return await self._execute_multi_agent(state, decision.agent_sequence)
        else:
            return await self._execute_single_agent(state, expert_name, decision.task_description)

    def observe(self, state: MainGraphState, action_result: Dict[str, Any]) -> str:
        """
        Observation 阶段：分析 Expert 执行结果，判断是否需要继续
        """
        if action_result.get("status") == "finished":
            return "FINISH"

        # 检查是否所有 Expert 都已完成
        if action_result.get("all_completed", False):
            return "FINISH"

        # 还有未完成的 Agent
        next_agent = action_result.get("next_agent", "")
        return next_agent or "FINISH"

    async def final_answer(self, state: MainGraphState) -> str:
        """
        Final Answer 阶段：整合所有 Expert 输出，通过 LLM 生成自然语言最终答案
        """
        expert_outputs = state.get("expert_outputs", {})
        user_query = state.get("user_query", "")

        if not expert_outputs:
            # 没有 Expert 参与，直接用 LLM 做对话式回复
            if self.llm:
                try:
                    return await self._llm_direct_chat(user_query)
                except Exception as e:
                    logger.error(f"LLM 直接对话失败: {e}")
            return json.dumps({
                "answer": f"抱歉，未能处理您的请求：「{user_query}」。请尝试更具体地描述您的需求。",
                "agent_used": [],
                "status": "no_result"
            }, ensure_ascii=False)

        # 如果有 LLM，用它合成自然语言回复
        if self.llm:
            try:
                return await self._llm_final_answer(state)
            except Exception as e:
                logger.error(f"LLM 最终答案生成失败: {e}")

        # 降级：手动拼接结果
        parts = []
        agents_used = []
        for agent_name, output in expert_outputs.items():
            agents_used.append(agent_name)
            agent_display = self._get_agent_display_name(agent_name)
            if isinstance(output, dict):
                # 优先使用 summary 字段
                summary = output.get("summary", "")
                if not summary:
                    # 尝试从订单/物流等字段生成自然语言描述
                    summary = self._format_expert_summary(agent_name, output)
                if not summary:
                    summary = str(output)
                parts.append(f"【{agent_display}】{summary}")
            else:
                parts.append(f"【{agent_display}】{output}")

        return json.dumps({
            "answer": "\n\n".join(parts),
            "agent_used": agents_used,
            "status": "success"
        }, ensure_ascii=False)

    def _format_expert_summary(self, agent_name: str, output: dict) -> str:
        """根据 Agent 类型和输出数据生成自然语言摘要"""
        if agent_name == "order_management":
            order_status = output.get("order_status", "")
            order_details = output.get("order_details", {})
            if isinstance(order_details, dict):
                order_id = order_details.get("order_id", "")
                shipping = order_details.get("shipping_info", {})
                if isinstance(shipping, dict):
                    carrier = shipping.get("carrier", "")
                    tracking = shipping.get("tracking_number", "")
                    delivery = shipping.get("estimated_delivery", "")
                    location = shipping.get("current_location", "")
                    return (
                        f"订单 {order_id} 状态：{order_status}。"
                        f"物流承运商：{carrier}，运单号：{tracking}，"
                        f"当前位置：{location}，预计送达：{delivery}。"
                    )
            return f"订单状态：{order_status}"
        elif agent_name == "logistics":
            tracking = output.get("tracking_number", "")
            status = output.get("shipment_status", "")
            delivery = output.get("estimated_delivery", "")
            return f"物流单号 {tracking}，状态：{status}，预计送达：{delivery}"
        return ""

    async def _llm_final_answer(self, state: MainGraphState) -> str:
        """使用 LLM 合成最终答案"""
        expert_outputs = state.get("expert_outputs", {})
        user_query = state.get("user_query", "")

        outputs_text = json.dumps(expert_outputs, ensure_ascii=False, default=str)
        agents_used = list(expert_outputs.keys())

        prompt = f"""你是跨境电商客服助手。请根据以下各专家 Agent 的输出，对用户问题生成一个自然、友好的综合回复。

用户问题: {user_query}

参与处理的 Agent: {', '.join(agents_used)}

各 Agent 输出:
{outputs_text}

请以 JSON 格式回复:
{{
    "answer": "<自然语言综合回复>",
    "agent_used": {json.dumps(agents_used)},
    "status": "success"
}}
"""
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json_match.group()
            else:
                return json.dumps({
                    "answer": content.strip(),
                    "agent_used": agents_used,
                    "status": "success"
                }, ensure_ascii=False)
        except Exception:
            return json.dumps({
                "answer": f"已由 {', '.join(agents_used)} 专家处理完成。",
                "agent_used": agents_used,
                "status": "success"
            }, ensure_ascii=False)

    async def _llm_direct_chat(self, user_query: str) -> str:
        """无 Expert 参与时，直接用 LLM 进行对话式回复"""
        prompt = f"""你是跨境电商多智能体系统的智能助手，可以帮助用户处理选品分析、广告投放、订单管理、物流追踪、客服咨询等跨境电商业务。

请用友好、自然的中文回复用户。如果用户只是打招呼或闲聊，请友好回应并介绍你能提供的服务。

用户: {user_query}

请以 JSON 格式回复:
{{
    "answer": "<自然语言回复>",
    "agent_used": [],
    "status": "chat"
}}"""
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json_match.group()
            else:
                return json.dumps({
                    "answer": content.strip(),
                    "agent_used": [],
                    "status": "chat"
                }, ensure_ascii=False)
        except Exception as e:
            logger.error(f"_llm_direct_chat 失败: {e}")
            raise

    # ================================================================
    # 路由决策方法
    # ================================================================
    def _keyword_route(self, query: str) -> Optional[str]:
        """关键词匹配路由"""
        for keyword, agent in self.KEYWORD_ROUTING.items():
            if keyword in query:
                return agent
        return None

    def _pattern_route(self, query: str) -> Optional[List[str]]:
        """多 Agent 模式匹配"""
        for pattern_name, agents in self.MULTI_AGENT_PATTERNS.items():
            if pattern_name in query:
                return agents
        return None

    async def _llm_route(self, state: MainGraphState) -> RoutingDecision:
        """使用 LLM 进行智能路由决策"""
        from config.settings import SUPERVISOR_SYSTEM_PROMPT

        user_query = state.get("user_query", "")
        expert_outputs = state.get("expert_outputs", {})
        task_history = state.get("task_history", [])

        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]

        # 添加上下文：已完成的 Expert 及其输出摘要
        if expert_outputs:
            completed = []
            for agent_name, output in expert_outputs.items():
                if isinstance(output, dict):
                    status = output.get("order_status") or output.get("shipment_status") or "已完成"
                    summary = output.get("summary", f"状态: {status}")
                else:
                    summary = str(output)
                completed.append(f"- {agent_name}: {summary}")

            messages.append({
                "role": "system",
                "content": (
                    f"已调用的 Agent 及其结果:\n" + "\n".join(completed) +
                    "\n\n如果所有必要信息已获取，请返回 FINISH。"
                    "如果还有未处理的关键信息，请指定下一个 Agent。"
                ),
            })
        elif task_history:
            context = "\n".join([
                f"- {t.get('agent', '')}: {t.get('output_summary', '')}"
                for t in task_history
            ])
            messages.append({
                "role": "system",
                "content": f"已完成的任务:\n{context}\n请判断是否需要继续调用其他 Agent。"
            })

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content if hasattr(response, 'content') else str(response)

            # 解析 JSON 响应
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                decision_data = json.loads(json_match.group())
                next_agent = decision_data.get("next_agent", "FINISH")
                # 如果 LLM 返回已调用过的 Agent，强制 FINISH（防止循环）
                if next_agent != "FINISH" and next_agent in expert_outputs:
                    logger.info(f"[Supervisor] LLM 重复路由到 {next_agent}，已存在输出，强制 FINISH")
                    next_agent = "FINISH"
                return RoutingDecision(
                    next_agent=next_agent,
                    reasoning=decision_data.get("reasoning", ""),
                    task_description=decision_data.get("task_description", ""),
                    requires_multi_agent=decision_data.get("requires_multi_agent", False),
                    agent_sequence=decision_data.get("agent_sequence", []),
                )
        except Exception as e:
            logger.error(f"LLM 路由决策失败: {e}")

        return RoutingDecision(
            next_agent=AgentRole.CUSTOMER_SERVICE,
            reasoning="LLM 路由失败，降级到客服",
            task_description=user_query,
        )

    # ================================================================
    # Agent 执行方法
    # ================================================================
    async def _execute_single_agent(self, state: MainGraphState,
                                     expert_name: str,
                                     task_description: str) -> Dict[str, Any]:
        """执行单个 Expert Agent"""
        logger.info(f"[Supervisor] 路由到 Expert: {expert_name}")

        # 通过 MCP Router 调用 Agent 的工具
        # 实际实现中，这里会调用 Agent 的 run() 方法
        tools = get_tools_for_agent(expert_name)

        # 使用 MCP 协议调用 Agent 的核心工具
        primary_tool = self._get_primary_tool(expert_name)
        if primary_tool:
            result = await self.mcp_router.route_tool_call(
                agent_name=expert_name,
                tool_name=primary_tool,
                arguments={"query": task_description, "context": state.get("user_context", {})}
            )
        else:
            result = {"success": True, "result": f"{expert_name} 处理完成"}

        return {
            "status": "completed",
            "expert_name": expert_name,
            "result": result,
            "all_completed": True,
        }

    async def _execute_multi_agent(self, state: MainGraphState,
                                    agent_sequence: List[str]) -> Dict[str, Any]:
        """
        多 Agent 顺序执行

        执行模式：
        - 顺序执行：Agent 按序列依次执行，后一个 Agent 可以访问前一个的结果
        - 并行执行：独立的 Agent 可并行执行（未来优化）
        """
        all_results = {}

        for i, agent_name in enumerate(agent_sequence):
            logger.info(f"[Supervisor] 多Agent执行 [{i+1}/{len(agent_sequence)}]: {agent_name}")

            # 为当前 Agent 构建上下文（包含前序 Agent 的结果）
            context = state.get("user_context", {})
            if all_results:
                context["previous_agent_results"] = all_results

            result = await self._execute_single_agent(state, agent_name,
                                                       state.get("current_task", ""))
            all_results[agent_name] = result

        return {
            "status": "completed",
            "all_results": all_results,
            "all_completed": True,
            "agent_sequence": agent_sequence,
        }

    def _get_primary_tool(self, agent_name: str) -> Optional[str]:
        """获取 Agent 的主要工具"""
        primary_tools = {
            AgentRole.MARKET_RESEARCH: "generate_selection_report",
            AgentRole.ADVERTISING: "generate_ad_plan",
            AgentRole.CUSTOMER_SERVICE: "generate_response",
            AgentRole.SUPPLY_CHAIN: "forecast_demand",
            AgentRole.ORDER_MANAGEMENT: "query_order_details",
            AgentRole.RECOMMENDATION: "generate_personalized_feed",
            AgentRole.INVENTORY: "check_stock",
            AgentRole.PAYMENT: "process_payment",
            AgentRole.LOGISTICS: "track_shipment",
            AgentRole.MARKETING: "create_campaign",
            AgentRole.USER_BEHAVIOR: "segment_users",
        }
        return primary_tools.get(agent_name)

    # ================================================================
    # 辅助方法
    # ================================================================
    def _get_agent_display_name(self, agent_name: str) -> str:
        """获取 Agent 中文显示名称"""
        names = {
            AgentRole.MARKET_RESEARCH: "选品分析",
            AgentRole.ADVERTISING: "广告投放",
            AgentRole.CUSTOMER_SERVICE: "客服",
            AgentRole.SUPPLY_CHAIN: "供应链",
            AgentRole.ORDER_MANAGEMENT: "订单管理",
            AgentRole.RECOMMENDATION: "个性化推荐",
            AgentRole.INVENTORY: "库存管理",
            AgentRole.PAYMENT: "支付",
            AgentRole.LOGISTICS: "物流追踪",
            AgentRole.MARKETING: "营销活动",
            AgentRole.USER_BEHAVIOR: "用户行为分析",
        }
        return names.get(agent_name, agent_name)

    def get_routing_history(self) -> List[RoutingDecision]:
        return self._routing_history