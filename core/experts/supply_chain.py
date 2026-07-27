"""
供应链预测 Agent - 需求预测与补货优化
负责需求预测、库存周转分析、供应商评估、补货建议
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import SupplyChainState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class SupplyChainAgent(ExpertAgent):
    """供应链预测 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.SUPPLY_CHAIN,
            description="供应链专家：负责需求预测、库存优化、供应商评估和补货建议"
        )

    async def think(self, state: SupplyChainState) -> Dict[str, Any]:
        task = state.get("task_description", "")

        if "预测" in task or "forecast" in task:
            return {
                "action": "forecast_demand",
                "reasoning": "执行需求预测",
                "tool_args": {
                    "product_ids": [],
                    "forecast_period_days": state.get("forecast_period", 30),
                },
            }
        elif "补货" in task or "replenish" in task:
            return {
                "action": "recommend_replenishment",
                "reasoning": "生成补货建议",
                "tool_args": {
                    "warehouse_id": state.get("warehouse_id", ""),
                    "product_ids": [],
                },
            }
        elif "供应商" in task or "supplier" in task:
            return {
                "action": "evaluate_supplier",
                "reasoning": "评估供应商",
                "tool_args": {"supplier_id": ""},
            }
        else:
            return {
                "action": "forecast_demand",
                "reasoning": "默认执行需求预测",
                "tool_args": {
                    "product_ids": [],
                    "forecast_period_days": state.get("forecast_period", 30),
                },
            }

    async def act(self, state: SupplyChainState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: SupplyChainState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> SupplyChainState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            tool_name = thought["action"]

            if "forecast" in tool_name:
                state["demand_forecast"] = result
            elif "replenish" in tool_name:
                state["replenishment_suggestions"] = result.get("replenishment_plan", [])
            elif "evaluate" in tool_name:
                state["supplier_recommendations"] = [result]

        return state

    async def final_answer(self, state: SupplyChainState) -> Dict[str, Any]:
        return {
            "demand_forecast": state.get("demand_forecast", {}),
            "inventory_plan": state.get("inventory_plan", {}),
            "supplier_recommendations": state.get("supplier_recommendations", []),
            "replenishment_suggestions": state.get("replenishment_suggestions", []),
            "turnover_rate": state.get("turnover_rate", 0.0),
            "summary": "供应链分析完成",
        }