"""
订单管理 Agent - 订单创建、查询、修改、取消
"""

import logging
import re
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import OrderManagementState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class OrderManagementAgent(ExpertAgent):
    """订单管理 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.ORDER_MANAGEMENT,
            description="订单管理专家：负责订单创建、查询、状态更新和取消处理"
        )

    def _extract_order_id(self, state: OrderManagementState) -> str:
        """从状态中提取订单 ID，优先从用户查询中解析"""
        # 1. 先从 order_id 字段获取
        order_id = state.get("order_id", "")
        if order_id:
            return order_id

        # 2. 从 task_description（用户查询）中解析订单号
        task_desc = state.get("task_description", "")
        # 匹配模式: ORD-xxxx 或 ORD-xxxxxxxx-xxxxx
        match = re.search(r'ORD-\d{4,}(?:-\d+)?', task_desc)
        if match:
            return match.group()

        # 3. 从 order_details 中获取
        details = state.get("order_details", {})
        if isinstance(details, dict) and details.get("order_id"):
            return details["order_id"]

        return ""

    async def think(self, state: OrderManagementState) -> Dict[str, Any]:
        # 如果订单详情已获取且状态已设置，任务完成
        if state.get("order_details") and state.get("order_status"):
            return {"action": "FINISH", "reasoning": "订单查询已完成"}

        action = state.get("order_action", "query")
        order_id = self._extract_order_id(state)

        # 根据查询内容自动判断操作类型
        task_desc = state.get("task_description", "")
        if "取消" in task_desc or "cancel" in task_desc.lower():
            action = "cancel"
        elif "创建" in task_desc or "下单" in task_desc or "create" in task_desc.lower():
            action = "create"
        elif "更新" in task_desc or "修改" in task_desc or "update" in task_desc.lower():
            action = "update"
        elif "查询" in task_desc or "查" in task_desc or "query" in task_desc.lower() or "状态" in task_desc or "配送" in task_desc:
            action = "query"

        action_map = {
            "create": ("create_order", "创建新订单", {
                "user_id": state.get("customer_info", {}).get("user_id", ""),
                "items": state.get("product_list", []),
                "shipping_address": state.get("shipping_info", {}),
                "payment_method": "credit_card",
            }),
            "query": ("query_order_details", "查询订单详情", {
                "order_id": order_id,
            }),
            "cancel": ("cancel_order", "取消订单", {
                "order_id": order_id,
                "reason": state.get("task_description", "用户请求取消"),
            }),
            "update": ("update_order_status", "更新订单状态", {
                "order_id": order_id,
                "new_status": state.get("order_status", "processing"),
            }),
        }

        action_info = action_map.get(action, action_map["query"])
        logger.info(f"[OrderManagement] think: action={action_info[0]}, order_id={order_id}")
        return {
            "action": action_info[0],
            "reasoning": action_info[1],
            "tool_args": action_info[2],
        }

    async def act(self, state: OrderManagementState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: OrderManagementState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> OrderManagementState:
        if not isinstance(action_result, dict):
            logger.error(f"[OrderManagement] observe: 非预期的 action_result 类型: {type(action_result)}")
            state["order_status"] = "error"
            return state

        if action_result.get("success"):
            result = action_result.get("result", {})
            if not isinstance(result, dict):
                logger.error(f"[OrderManagement] observe: 非预期的 result 类型: {type(result)}")
                state["order_status"] = "error"
                return state

            state["order_details"] = result
            state["order_status"] = result.get("status", state.get("order_status", ""))
            state["order_id"] = result.get("order_id", state.get("order_id", ""))
            state["payment_status"] = result.get("payment_status", state.get("payment_status", ""))
            state["shipping_info"] = result.get("shipping_info", state.get("shipping_info", {}))
        else:
            logger.error(f"[OrderManagement] observe: 工具调用失败 - {action_result.get('error')}")
            state["order_status"] = "error"

        return state

    async def final_answer(self, state: OrderManagementState) -> Dict[str, Any]:
        order_details = state.get("order_details", {})
        order_status = state.get("order_status", "")
        payment_status = state.get("payment_status", "")
        shipping_info = state.get("shipping_info", {})

        # 生成自然语言摘要
        summary_parts = []
        order_id = order_details.get("order_id", "") if isinstance(order_details, dict) else ""
        if order_id:
            summary_parts.append(f"订单 {order_id} 当前状态为「{order_status}」")
        else:
            summary_parts.append(f"订单状态: {order_status}")

        if payment_status:
            summary_parts.append(f"支付状态: {payment_status}")

        if isinstance(shipping_info, dict) and shipping_info:
            carrier = shipping_info.get("carrier", "")
            tracking = shipping_info.get("tracking_number", "")
            location = shipping_info.get("current_location", "")
            delivery = shipping_info.get("estimated_delivery", "")
            if carrier:
                summary_parts.append(f"物流承运商: {carrier}")
            if tracking:
                summary_parts.append(f"运单号: {tracking}")
            if location:
                summary_parts.append(f"当前位置: {location}")
            if delivery:
                summary_parts.append(f"预计送达: {delivery}")

        return {
            "order_details": order_details,
            "order_status": order_status,
            "payment_status": payment_status,
            "shipping_info": shipping_info,
            "order_history": state.get("order_history", []),
            "summary": "；".join(summary_parts) if summary_parts else f"订单操作完成，状态: {order_status}",
        }