"""
营销活动 Agent - 促销活动管理与优惠券分发
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import MarketingState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class MarketingAgent(ExpertAgent):
    """营销活动 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.MARKETING,
            description="营销活动专家：负责促销活动创建、优惠券分发、用户分群和效果分析"
        )

    async def think(self, state: MarketingState) -> Dict[str, Any]:
        task = state.get("task_description", "")

        if "优惠券" in task or "coupon" in task:
            return {
                "action": "distribute_coupons",
                "reasoning": "分发优惠券",
                "tool_args": {
                    "coupon_template_id": state.get("campaign_name", ""),
                    "user_segments": state.get("target_audience", {}).get("segments", []),
                    "quantity": 1000,
                },
            }
        elif "分析" in task or "效果" in task or "ROI" in task:
            return {
                "action": "analyze_campaign_roi",
                "reasoning": "分析活动效果",
                "tool_args": {
                    "campaign_id": state.get("campaign_name", ""),
                    "metrics": ["revenue", "cost", "conversion_rate", "new_users"],
                },
            }
        else:
            return {
                "action": "create_campaign",
                "reasoning": "创建营销活动",
                "tool_args": {
                    "campaign_name": state.get("campaign_name", "新活动"),
                    "campaign_type": state.get("campaign_type", "seasonal_promo"),
                    "start_date": state.get("promotion_period", {}).get("start", ""),
                    "end_date": state.get("promotion_period", {}).get("end", ""),
                    "budget": state.get("budget", 5000.0),
                    "target_segments": state.get("target_audience", {}).get("segments", []),
                },
            }

    async def act(self, state: MarketingState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: MarketingState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> MarketingState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            state["campaign_name"] = result.get("campaign_id", state.get("campaign_name", ""))
            state["performance_metrics"] = result
            state["roi"] = result.get("roi", 0.0)

        return state

    async def final_answer(self, state: MarketingState) -> Dict[str, Any]:
        return {
            "campaign_name": state.get("campaign_name", ""),
            "campaign_type": state.get("campaign_type", ""),
            "discount_rules": state.get("discount_rules", {}),
            "coupon_templates": state.get("coupon_templates", []),
            "performance_metrics": state.get("performance_metrics", {}),
            "roi": state.get("roi", 0.0),
            "summary": f"营销活动: {state.get('campaign_name', 'N/A')}, ROI: {state.get('roi', 'N/A')}",
        }