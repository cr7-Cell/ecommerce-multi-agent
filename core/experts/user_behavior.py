"""
用户行为分析 Agent - 行为追踪与用户分群
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import UserBehaviorState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class UserBehaviorAgent(ExpertAgent):
    """用户行为分析 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.USER_BEHAVIOR,
            description="用户行为分析专家：负责行为追踪、模式分析、用户分群和流失预测"
        )

    async def think(self, state: UserBehaviorState) -> Dict[str, Any]:
        task = state.get("task_description", "")

        if "分群" in task or "segment" in task:
            return {
                "action": "segment_users",
                "reasoning": "用户分群分析",
                "tool_args": {
                    "segmentation_type": "rfm",
                    "segment_count": 5,
                },
            }
        elif "模式" in task or "pattern" in task:
            return {
                "action": "analyze_behavior_pattern",
                "reasoning": "分析行为模式",
                "tool_args": {
                    "user_id": state.get("user_id", ""),
                    "analysis_period": "30d",
                },
            }
        else:
            return {
                "action": "segment_users",
                "reasoning": "默认执行用户分群",
                "tool_args": {
                    "segmentation_type": "behavioral",
                    "segment_count": 5,
                },
            }

    async def act(self, state: UserBehaviorState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        return await self.call_tool(thought["action"], thought["tool_args"])

    async def observe(self, state: UserBehaviorState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> UserBehaviorState:
        if action_result.get("success"):
            result = action_result.get("result", {})
            state["segment_analysis"] = result
            state["user_segment"] = result.get("segments", [{}])[0].get("name", "") if result.get("segments") else ""
            state["behavior_patterns"] = result.get("patterns", {})

        return state

    async def final_answer(self, state: UserBehaviorState) -> Dict[str, Any]:
        return {
            "behavior_patterns": state.get("behavior_patterns", {}),
            "user_segment": state.get("user_segment", ""),
            "churn_risk": state.get("churn_risk", 0.0),
            "conversion_probability": state.get("conversion_probability", 0.0),
            "segment_analysis": state.get("segment_analysis", {}),
            "summary": f"用户分群: {state.get('user_segment', 'N/A')}",
        }