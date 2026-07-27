"""
客服 Agent - 智能客服与售后处理
负责FAQ回答、订单查询、退款处理、情感分析、知识库检索
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import CustomerServiceState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class CustomerServiceAgent(ExpertAgent):
    """客服 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.CUSTOMER_SERVICE,
            description="客服专家：负责客户咨询解答、售后处理、FAQ检索和情感分析"
        )

    async def think(self, state: CustomerServiceState) -> Dict[str, Any]:
        question = state.get("user_question", state.get("task_description", ""))

        # 意图识别
        if any(w in question for w in ["退款", "退货", "refund", "return"]):
            return {
                "action": "process_refund_request",
                "reasoning": "用户请求退款处理",
                "tool_args": {"order_id": "", "reason": question},
                "intent": "refund",
            }
        elif any(w in question for w in ["订单", "order", "查询", "状态"]):
            return {
                "action": "lookup_order_status",
                "reasoning": "用户查询订单状态",
                "tool_args": {"order_id": "", "user_id": ""},
                "intent": "order_query",
            }
        else:
            return {
                "action": "search_knowledge_base",
                "reasoning": "检索知识库获取答案",
                "tool_args": {"query": question, "top_k": 5},
                "intent": "faq",
            }

    async def act(self, state: CustomerServiceState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: CustomerServiceState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> CustomerServiceState:
        state["intent"] = thought.get("intent", "")

        if action_result.get("success"):
            result = action_result.get("result", {})

            if thought["action"] == "search_knowledge_base":
                state["knowledge_base_hits"] = result.get("results", [])
            elif thought["action"] == "lookup_order_status":
                state["order_info"] = result
            elif thought["action"] == "process_refund_request":
                state["refund_eligible"] = True

        return state

    async def final_answer(self, state: CustomerServiceState) -> Dict[str, Any]:
        # 生成最终客服回复
        intent = state.get("intent", "faq")
        kb_hits = state.get("knowledge_base_hits", [])
        order_info = state.get("order_info", {})

        if intent == "refund":
            response = "您的退款申请已收到，我们将尽快处理。退款金额将在3-5个工作日内退还到您的支付账户。"
        elif intent == "order_query":
            status = order_info.get("order_status", "处理中")
            response = f"您的订单当前状态为：{status}"
        elif kb_hits:
            response = kb_hits[0].get("content", "感谢您的咨询，请问有什么可以帮您？")
        else:
            response = "感谢您的咨询，我会尽快为您查找相关信息。"

        return {
            "generated_response": response,
            "sentiment": state.get("sentiment", "neutral"),
            "intent": intent,
            "refund_eligible": state.get("refund_eligible", False),
            "order_info": order_info,
            "escalated": state.get("escalated", False),
            "summary": response[:80],
        }