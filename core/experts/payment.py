"""
支付处理 Agent - 支付、退款、对账
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import PaymentState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class PaymentAgent(ExpertAgent):
    """支付处理 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.PAYMENT,
            description="支付处理专家：负责支付处理、退款、交易查询和财务对账"
        )

    async def think(self, state: PaymentState) -> Dict[str, Any]:
        task = state.get("task_description", "")

        if "退款" in task or "refund" in task:
            return {
                "action": "refund_payment",
                "reasoning": "处理退款",
                "tool_args": {
                    "transaction_id": state.get("transaction_id", ""),
                    "amount": state.get("amount", 0),
                    "reason": task,
                },
            }
        elif "查询" in task or "历史" in task:
            return {
                "action": "query_payment_history",
                "reasoning": "查询支付历史",
                "tool_args": {
                    "user_id": state.get("user_context", {}).get("user_id", ""),
                },
            }
        else:
            return {
                "action": "process_payment",
                "reasoning": "处理支付",
                "tool_args": {
                    "order_id": state.get("task_description", ""),
                    "amount": state.get("amount", 0),
                    "payment_method": state.get("payment_method", "credit_card"),
                    "currency": state.get("currency", "USD"),
                },
            }

    async def act(self, state: PaymentState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: PaymentState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> PaymentState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            state["transaction_id"] = result.get("transaction_id", state.get("transaction_id", ""))
            state["payment_status"] = result.get("status", "success")

        return state

    async def final_answer(self, state: PaymentState) -> Dict[str, Any]:
        return {
            "transaction_id": state.get("transaction_id", ""),
            "payment_status": state.get("payment_status", "pending"),
            "refund_info": state.get("refund_info", {}),
            "payment_history": state.get("payment_history", []),
            "reconciliation": state.get("reconciliation", {}),
            "summary": f"支付处理完成，状态: {state.get('payment_status', 'N/A')}",
        }