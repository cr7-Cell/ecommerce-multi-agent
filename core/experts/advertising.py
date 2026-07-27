"""
广告投放 Agent - 广告策略与效果优化
负责广告计划生成、预算分配、效果分析、定向优化
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import AdvertisingState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class AdvertisingAgent(ExpertAgent):
    """广告投放 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.ADVERTISING,
            description="广告投放专家：负责广告策略制定、预算分配、效果分析和定向优化"
        )

    async def think(self, state: AdvertisingState) -> Dict[str, Any]:
        task = state.get("task_description", "")
        budget = state.get("budget", 0)

        if "分析" in task or "效果" in task:
            return {
                "action": "analyze_ad_performance",
                "reasoning": "分析广告效果",
                "tool_args": {"campaign_id": state.get("campaign_id", ""),
                             "metrics": ["ctr", "cpc", "roas", "conversions"]},
            }
        elif "优化" in task:
            return {
                "action": "optimize_ad_targeting",
                "reasoning": "优化广告定向",
                "tool_args": {"campaign_id": state.get("campaign_id", ""),
                             "optimization_goal": "conversions"},
            }
        else:
            return {
                "action": "generate_ad_plan",
                "reasoning": "生成广告投放计划",
                "tool_args": {
                    "products": state.get("target_products", []),
                    "total_budget": budget or 1000.0,
                    "platforms": state.get("platform", "google"),
                    "duration_days": 30,
                },
            }

    async def act(self, state: AdvertisingState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: AdvertisingState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> AdvertisingState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            tool_name = thought["action"]

            if "plan" in tool_name:
                state["ad_plans"] = [result]
            elif "performance" in tool_name:
                state["performance_metrics"] = result
            elif "optimize" in tool_name:
                state["roi_analysis"] = result
            elif "create" in tool_name:
                state["campaign_id"] = result.get("campaign_id", "")

        return state

    async def final_answer(self, state: AdvertisingState) -> Dict[str, Any]:
        return {
            "ad_plans": state.get("ad_plans", []),
            "campaign_id": state.get("campaign_id", ""),
            "performance_metrics": state.get("performance_metrics", {}),
            "roi_analysis": state.get("roi_analysis", {}),
            "budget": state.get("budget", 0),
            "summary": f"广告投放计划已生成，预算: {state.get('budget', 0)}",
        }