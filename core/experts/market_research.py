"""
选品分析 Agent - 市场调研与商品选择
负责竞品分析、市场趋势、价格对比、选品推荐
"""

import logging
from typing import Any, Dict, List

from config.settings import AgentRole
from core.state import MarketResearchState
from core.experts.base import ExpertAgent

logger = logging.getLogger(__name__)


class MarketResearchAgent(ExpertAgent):
    """选品分析 Expert Agent"""

    def __init__(self):
        super().__init__(
            role=AgentRole.MARKET_RESEARCH,
            description="选品分析专家：负责竞品调研、市场趋势分析、价格对比和选品推荐"
        )

    async def think(self, state: MarketResearchState) -> Dict[str, Any]:
        # 如果报告已生成，任务完成
        if state.get("analysis_report") and state.get("selected_products") is not None:
            return {"action": "FINISH", "reasoning": "选品分析已完成"}

        task = state.get("task_description", "")
        search_keywords = state.get("search_keywords", [])
        target_market = state.get("target_market", "")

        # 如果没有搜索关键词，从任务描述中提取
        if not search_keywords:
            search_keywords = self._extract_keywords(task)

        # 确定执行计划
        plan = [
            {"tool": "search_competitor_products", "reason": "搜索竞品信息"},
            {"tool": "analyze_market_trends", "reason": "分析市场趋势"},
            {"tool": "fetch_product_rankings", "reason": "获取商品排名"},
            {"tool": "compare_price_ranges", "reason": "对比价格区间"},
            {"tool": "generate_selection_report", "reason": "生成选品报告"},
        ]

        # 返回第一步行动
        return {
            "action": "search_competitor_products",
            "reasoning": f"开始选品分析流程，关键词: {search_keywords}",
            "tool_args": {
                "keywords": search_keywords,
                "market": target_market or "US",
                "limit": 20
            },
            "plan": plan,
            "current_step": 0,
            "search_keywords": search_keywords,
        }

    async def act(self, state: MarketResearchState,
                  thought: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = thought["action"]
        tool_args = thought.get("tool_args", {})

        if tool_name == "FINISH":
            return {"success": True, "result": "finished"}

        return await self.call_tool(tool_name, tool_args)

    async def observe(self, state: MarketResearchState,
                      thought: Dict[str, Any],
                      action_result: Dict[str, Any]) -> MarketResearchState:
        current_step = thought.get("current_step", 0)
        plan = thought.get("plan", [])

        if not action_result.get("success"):
            logger.error(f"[MarketResearch] 工具调用失败 step={current_step}: {action_result.get('error')}")
            thought["action"] = "FINISH"
            return state

        result = action_result.get("result", {})

        # 根据当前步骤更新状态（mock 工具直接返回数据，不需要 .get("data")）
        step_handlers = {
            0: lambda: state.update({
                "competitor_data": result.get("products", result if isinstance(result, list) else []),
                "search_keywords": thought.get("search_keywords", [])
            }),
            1: lambda: state.update({
                "market_trends": result if isinstance(result, dict) else {}
            }),
            2: lambda: state.update({
                "price_analysis": result if isinstance(result, dict) else {}
            }),
            3: lambda: state.update({
                "selected_products": result.get("selected", result.get("products", []))
            }),
            4: lambda: state.update({
                "analysis_report": result.get("report", str(result))
            }),
        }

        handler = step_handlers.get(current_step, lambda: None)
        handler()

        # 更新 thought 到下一步
        if current_step + 1 < len(plan):
            next_step = plan[current_step + 1]
            thought["action"] = next_step["tool"]
            thought["tool_args"] = self._build_tool_args(
                next_step["tool"], state
            )
            thought["current_step"] = current_step + 1
        else:
            thought["action"] = "FINISH"

        return state

    async def final_answer(self, state: MarketResearchState) -> Dict[str, Any]:
        products = state.get("selected_products", [])
        report = state.get("analysis_report", "")
        trends = state.get("market_trends", {})

        return {
            "selected_products": products,
            "analysis_report": report or self._generate_report(state),
            "market_trends": trends,
            "price_analysis": state.get("price_analysis", {}),
            "competitor_data": state.get("competitor_data", []),
            "summary": f"选品分析完成，共分析 {len(products)} 个候选商品",
        }

    # ---- 辅助方法 ----
    def _extract_keywords(self, task: str) -> List[str]:
        """从任务描述中提取关键词"""
        import re
        # 先提取连续的中文词块和英文词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', task)
        # 过滤掉停用词和短词
        stopwords = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
                     '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有',
                     '看', '好', '自己', '这', '帮', '分析', '一下', '市场', 'the', 'a', 'an',
                     'is', 'are', 'was', 'were', 'for', 'in', 'of', 'me', 'my'}
        keywords = [w for w in words if w.lower() not in stopwords and len(w) > 1]
        # 如果关键词太长（整句），尝试按2-4字切分
        if keywords and len(keywords[0]) > 6:
            long_word = keywords[0]
            # 提取有意义的子串：蓝牙耳机、选品 等
            sub_keywords = []
            for i in range(0, len(long_word), 2):
                chunk = long_word[i:i+4]
                if len(chunk) >= 2:
                    sub_keywords.append(chunk)
            keywords = sub_keywords
        return keywords[:5]

    def _build_tool_args(self, tool_name: str, state: MarketResearchState) -> Dict[str, Any]:
        """根据工具名称构建参数"""
        args_map = {
            "search_competitor_products": {
                "keywords": state.get("search_keywords", []),
                "market": state.get("target_market", "US"),
            },
            "analyze_market_trends": {
                "category": state.get("search_keywords", [""])[0],
                "market": state.get("target_market", "US"),
            },
            "fetch_product_rankings": {
                "category": state.get("search_keywords", [""])[0],
                "market": state.get("target_market", "US"),
            },
            "compare_price_ranges": {
                "product_ids": [p.get("id") for p in state.get("competitor_data", [])],
                "markets": [state.get("target_market", "US"), "CN", "UK"],
            },
            "generate_selection_report": {
                "analysis_data": {
                    "competitor_data": state.get("competitor_data", []),
                    "market_trends": state.get("market_trends", {}),
                    "price_analysis": state.get("price_analysis", {}),
                }
            },
        }
        return args_map.get(tool_name, {})

    def _generate_report(self, state: MarketResearchState) -> str:
        """生成分析报告"""
        return (
            f"选品分析报告\n"
            f"市场趋势: {state.get('market_trends', {})}\n"
            f"价格分析: {state.get('price_analysis', {})}\n"
            f"推荐商品数: {len(state.get('selected_products', []))}"
        )