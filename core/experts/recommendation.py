"""
个性化推荐 Agent - 协同过滤与内容推荐
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import RecommendationState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class RecommendationAgent(ExpertAgent):
    """个性化推荐 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.RECOMMENDATION,
            description="推荐系统专家：负责用户画像分析、协同过滤、内容推荐和个性化排序"
        )

    async def think(self, state: RecommendationState) -> Dict[str, Any]:
        return {
            "action": "generate_personalized_feed",
            "reasoning": "生成个性化推荐信息流",
            "tool_args": {
                "user_id": state.get("user_profile", {}).get("user_id", ""),
                "page": "home",
                "limit": 20,
            },
        }

    async def act(self, state: RecommendationState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: RecommendationState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> RecommendationState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            state["recommended_products"] = result.get("recommendations", [])
            state["recommendation_reason"] = result.get("reason", [])
            state["ranking_scores"] = result.get("ranked_products", [])

        return state

    async def final_answer(self, state: RecommendationState) -> Dict[str, Any]:
        return {
            "recommended_products": state.get("recommended_products", []),
            "ranking_scores": state.get("ranking_scores", []),
            "recommendation_reason": state.get("recommendation_reason", []),
            "user_profile": state.get("user_profile", {}),
            "summary": f"为您推荐 {len(state.get('recommended_products', []))} 个商品",
        }