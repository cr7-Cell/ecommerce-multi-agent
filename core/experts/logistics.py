"""
物流追踪 Agent - 配送管理与物流追踪
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import LogisticsState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class LogisticsAgent(ExpertAgent):
    """物流追踪 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.LOGISTICS,
            description="物流追踪专家：负责配送管理、快递选择、物流追踪和配送预估"
        )

    async def think(self, state: LogisticsState) -> Dict[str, Any]:
        # 如果已有物流状态，任务完成
        if state.get("shipment_status"):
            return {"action": "FINISH", "reasoning": "物流追踪已完成"}

        task = state.get("task_description", "")

        # 从 order_management 的输出中提取 tracking_number 和 carrier
        tracking_number = state.get("tracking_number", "")
        carrier = state.get("carrier", "")
        if not tracking_number:
            expert_outputs = state.get("expert_outputs", {})
            order_output = expert_outputs.get("order_management", {})
            if isinstance(order_output, dict):
                shipping_info = order_output.get("shipping_info", {})
                if isinstance(shipping_info, dict):
                    tracking_number = shipping_info.get("tracking_number", "")
                    if not carrier:
                        carrier = shipping_info.get("carrier", "")

        if any(w in task for w in ["选择", "快递", "carrier"]):
            return {
                "action": "select_carrier",
                "reasoning": "选择快递公司",
                "tool_args": {
                    "origin": state.get("origin_address", {}),
                    "destination": state.get("destination_address", {}),
                    "delivery_speed": "standard",
                },
            }
        elif any(w in task for w in ["预估", "时间", "estimate", "预计"]):
            return {
                "action": "estimate_delivery",
                "reasoning": "预估配送时间",
                "tool_args": {
                    "order_id": state.get("task_description", ""),
                    "destination": state.get("destination_address", {}),
                },
            }
        else:
            # 默认追踪物流 — 优先使用 tracking_number
            if tracking_number:
                return {
                    "action": "track_shipment",
                    "reasoning": "追踪物流状态",
                    "tool_args": {
                        "tracking_number": tracking_number,
                        "carrier": carrier,
                    },
                }
            else:
                # 没有 tracking_number，用预估配送代替
                return {
                    "action": "estimate_delivery",
                    "reasoning": "无运单号，预估配送时间",
                    "tool_args": {
                        "order_id": state.get("task_description", ""),
                        "destination": state.get("destination_address", {}),
                    },
                }

    async def act(self, state: LogisticsState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: LogisticsState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> LogisticsState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            logger.info(f"[Logistics] observe: result type={type(result).__name__}, action={thought.get('action')}")

            if isinstance(result, dict):
                # track_shipment 返回格式: {tracking_number, carrier, status, current_location, ...}
                if "status" in result:
                    state["shipment_status"] = result.get("status", "")
                    state["tracking_number"] = result.get("tracking_number", state.get("tracking_number", ""))
                    state["carrier"] = result.get("carrier", state.get("carrier", ""))
                    state["estimated_delivery"] = result.get("estimated_delivery", "")
                # estimate_delivery 返回格式: {from, to, estimates, recommended, ...}
                elif "recommended" in result:
                    state["shipment_status"] = "预估完成"
                    state["carrier"] = result.get("recommended", state.get("carrier", ""))
                    estimates = result.get("estimates", [])
                    if estimates:
                        state["estimated_delivery"] = f"{estimates[0].get('carrier', '')} {estimates[0].get('days', '')}天"
                # select_carrier 返回格式: {recommended_carrier, estimated_days, cost}
                elif "recommended_carrier" in result:
                    state["shipment_status"] = "已选择快递"
                    state["carrier"] = result.get("recommended_carrier", "")
                    state["estimated_delivery"] = f"{result.get('estimated_days', '?')}天"

                state["tracking_history"] = [result]
                logger.info(f"[Logistics] observe: shipment_status={state['shipment_status']}")

        return state

    async def final_answer(self, state: LogisticsState) -> Dict[str, Any]:
        return {
            "tracking_number": state.get("tracking_number", ""),
            "carrier": state.get("carrier", ""),
            "shipment_status": state.get("shipment_status", "unknown"),
            "estimated_delivery": state.get("estimated_delivery", ""),
            "tracking_history": state.get("tracking_history", []),
            "delivery_exception": state.get("delivery_exception", {}),
            "summary": f"物流状态: {state.get('shipment_status', 'N/A')}",
        }