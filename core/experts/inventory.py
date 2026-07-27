"""
库存管理 Agent - 库存查询、入库、出库、预警
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import InventoryState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class InventoryAgent(ExpertAgent):
    """库存管理 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.INVENTORY,
            description="库存管理专家：负责库存查询、入库出库记录、库存预警和盘点"
        )

    async def think(self, state: InventoryState) -> Dict[str, Any]:
        task = state.get("task_description", "")

        if "入库" in task or "inbound" in task:
            return {
                "action": "record_inbound",
                "reasoning": "记录商品入库",
                "tool_args": {
                    "product_id": state.get("product_id", ""),
                    "quantity": 100,
                    "warehouse_id": state.get("warehouse_id", ""),
                },
            }
        elif "预警" in task or "alert" in task:
            return {
                "action": "stock_alert",
                "reasoning": "检查库存预警",
                "tool_args": {
                    "warehouse_id": state.get("warehouse_id", ""),
                },
            }
        else:
            return {
                "action": "check_stock",
                "reasoning": "查询库存",
                "tool_args": {
                    "product_ids": [state.get("product_id", "")] if state.get("product_id") else [],
                    "warehouse_id": state.get("warehouse_id", ""),
                },
            }

    async def act(self, state: InventoryState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: InventoryState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> InventoryState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            tool_name = thought["action"]

            if "check" in tool_name:
                state["stock_level"] = result.get("quantity", 0)
            elif "inbound" in tool_name:
                state["inbound_records"] = [result]
            elif "alert" in tool_name:
                state["stock_alerts"] = result.get("alerts", [])

        return state

    async def final_answer(self, state: InventoryState) -> Dict[str, Any]:
        return {
            "stock_level": state.get("stock_level", 0),
            "safety_stock": state.get("safety_stock", 0),
            "stock_alerts": state.get("stock_alerts", []),
            "inbound_records": state.get("inbound_records", []),
            "outbound_records": state.get("outbound_records", []),
            "summary": f"库存查询完成，当前库存: {state.get('stock_level', 0)}",
        }