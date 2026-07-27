"""
MCP 工具定义 - 为每个 Expert Agent 定义标准化的 MCP 工具
每个工具包含：名称、描述、参数 Schema、处理器函数
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from core.mcp.protocol import (
    MCPTool, MCPToolCategory, create_mcp_tool
)

logger = logging.getLogger(__name__)

# 模块级 LLM 实例（延迟初始化）
_llm = None

# 适配器注册中心（延迟初始化）
_adapter_registry = None


def set_llm(llm):
    """设置模块级 LLM 实例"""
    global _llm
    _llm = llm


def set_adapter_registry(registry):
    """设置适配器注册中心"""
    global _adapter_registry
    _adapter_registry = registry


def _get_adapter_handler(tool_name: str, agent_name: str = ""):
    """
    获取工具的 handler 函数（延迟求值）

    优先使用适配器注册中心，降级到 mock 数据。
    handler 在每次调用时检查 _adapter_registry 状态，而不是在模块导入时固定。
    这是理解"工具如何调用"的关键入口点。
    """
    async def handler(**kwargs):
        global _adapter_registry
        if _adapter_registry is not None:
            fn = _adapter_registry.get_handler(tool_name, agent_name)
            return await fn(**kwargs)
        return _fallback_mock(tool_name, kwargs)
    return handler


def _get_llm():
    """获取 LLM 实例，如果未设置则尝试自动初始化"""
    global _llm
    if _llm is None:
        try:
            from config.settings import system_config
            _llm = system_config.get_llm_instance()
            logger.info("[MCP Tools] LLM 自动初始化完成")
        except Exception as e:
            logger.warning(f"[MCP Tools] LLM 初始化失败: {e}")
    return _llm


# ============================================================
# LLM 驱动的工具调用
# ============================================================
async def _llm_tool_call(tool_name: str, agent_name: str, params: dict) -> dict:
    """
    使用 LLM 生成逼真的工具调用结果
    当 LLM 不可用时，返回模拟数据
    """
    llm = _get_llm()
    if llm is None:
        return _fallback_mock(tool_name, params)

    prompt = _build_tool_prompt(tool_name, agent_name, params)
    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # 尝试解析 JSON
        json_match = __import__('re').search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        return {"result": content.strip()}
    except Exception as e:
        logger.error(f"[MCP Tools] LLM 调用失败 {tool_name}: {e}")
        return _fallback_mock(tool_name, params)


def _build_tool_prompt(tool_name: str, agent_name: str, params: dict) -> str:
    """构建工具调用的 LLM prompt"""
    return f"""你是跨境电商系统的 {agent_name} 专家。有一个工具调用需要你模拟返回结果。

工具名称: {tool_name}
调用参数: {json.dumps(params, ensure_ascii=False)}

请根据工具名称和参数，生成一个合理的、逼真的 JSON 返回结果。结果应该包含具体数据，而不是空值。
只返回 JSON，不要包含其他文字。"""


def _fallback_mock(tool_name: str, params: dict) -> dict:
    """LLM 不可用时的模拟数据降级"""
    # 根据工具名称生成有意义的模拟数据
    mock_data = {
        "search_competitor_products": {
            "products": [
                {"name": "竞品A", "price": 59.99, "rating": 4.3, "reviews": 1200, "market_share": "15%"},
                {"name": "竞品B", "price": 79.99, "rating": 4.5, "reviews": 850, "market_share": "22%"},
                {"name": "竞品C", "price": 39.99, "rating": 4.1, "reviews": 3200, "market_share": "35%"},
            ],
            "total_found": 45,
            "source": "mock_data"
        },
        "analyze_market_trends": {
            "trend": "上升",
            "growth_rate": "15.2%",
            "seasonality": "Q4旺季",
            "search_volume_trend": [{"month": "Jan", "volume": 80000}, {"month": "Jun", "volume": 120000}],
            "source": "mock_data"
        },
        "fetch_product_rankings": {
            "rankings": [
                {"rank": 1, "name": "热销商品1", "bsr": 150, "rating": 4.7},
                {"rank": 2, "name": "热销商品2", "bsr": 320, "rating": 4.5},
            ],
            "source": "mock_data"
        },
        "generate_selection_report": {
            "report": "基于市场分析，推荐以下选品方向：1) 蓝牙降噪耳机（利润率35%，需求增长15%）；2) 无线充电器（利润率55%，竞争度低）。建议优先入场蓝牙耳机品类。",
            "score": 85.5,
            "recommended_products": [{"name": "蓝牙降噪耳机 Pro", "reason": "高需求+合理竞争", "score": 92}],
            "source": "mock_data"
        },
        "generate_ad_plan": {
            "plan": {
                "budget_allocation": {"google": "60%", "facebook": "30%", "tiktok": "10%"},
                "targeting": {"age": "18-45", "interests": ["电子产品", "音乐"], "locations": ["US", "UK"]},
                "estimated_impressions": 50000,
                "estimated_clicks": 1500,
                "estimated_conversions": 75,
                "estimated_roas": 4.5,
            },
            "source": "mock_data"
        },
        "lookup_order_status": {
            "order_id": params.get("order_id", "ORD-001"),
            "status": "已发货",
            "estimated_delivery": "2026-07-20",
            "tracking_number": "TRK-US-12345",
            "carrier": "FedEx",
            "source": "mock_data"
        },
        "search_knowledge_base": {
            "results": [
                {"content": "退换货政策：30天无理由退换货，需保持商品原包装完整。", "score": 0.95},
                {"content": "退款流程：收到退货后3-5个工作日内退款到原支付方式。", "score": 0.88},
            ],
            "source": "mock_data"
        },
        "process_refund_request": {
            "refund_id": "RF-20260713-001",
            "status": "处理中",
            "estimated_refund_time": "3-5个工作日",
            "refund_amount": params.get("refund_amount", 0),
            "source": "mock_data"
        },
        "generate_response": {
            "response": "感谢您的咨询！根据我们的政策，退换货需要在收到商品后30天内发起。商品需保持原包装完整。退款将在收到退货后3-5个工作日内处理。请问还有其他需要帮助的吗？",
            "source": "mock_data"
        },
        "forecast_demand": {
            "forecast": [
                {"product_id": "P001", "predicted_demand_30d": 350, "confidence": 0.95, "trend": "上升"},
                {"product_id": "P005", "predicted_demand_30d": 150, "confidence": 0.92, "trend": "稳定"},
            ],
            "source": "mock_data"
        },
        "check_stock": {
            "stock": [
                {"product_id": params.get("product_ids", ["P001"])[0], "quantity": 500, "warehouse": "深圳主仓", "status": "充足"},
            ],
            "source": "mock_data"
        },
        "track_shipment": {
            "tracking_number": params.get("tracking_number", "TRK-001"),
            "status": "运输中",
            "current_location": "洛杉矶转运中心",
            "estimated_delivery": "2026-07-18",
            "history": [
                {"time": "2026-07-10 08:00", "status": "已揽收", "location": "深圳"},
                {"time": "2026-07-12 06:00", "status": "清关完成", "location": "深圳海关"},
                {"time": "2026-07-14 10:00", "status": "抵达目的国", "location": "洛杉矶"},
            ],
            "source": "mock_data"
        },
        "create_campaign": {
            "campaign_id": "CAMP-20260713-001",
            "name": params.get("campaign_name", "新活动"),
            "status": "已创建",
            "start_date": params.get("start_date", "2026-07-13"),
            "source": "mock_data"
        },
        "segment_users": {
            "segments": [
                {"name": "高价值客户", "count": 320, "avg_order_value": 250.00, "purchase_frequency": "每周"},
                {"name": "活跃客户", "count": 1200, "avg_order_value": 80.00, "purchase_frequency": "每月"},
                {"name": "沉睡客户", "count": 3500, "avg_order_value": 45.00, "purchase_frequency": "90天以上"},
                {"name": "新客户", "count": 800, "avg_order_value": 60.00, "purchase_frequency": "首次"},
            ],
            "segment_stats": {"total_users": 5820, "active_rate": "26.1%"},
            "source": "mock_data"
        },
        "create_order": {
            "order_id": "ORD-20260713-001",
            "status": "已创建",
            "total": 159.99,
            "source": "mock_data"
        },
        "generate_personalized_feed": {
            "recommendations": [
                {"product_id": 1, "name": "蓝牙降噪耳机 Pro", "reason": "基于您的浏览历史", "score": 0.95},
                {"product_id": 5, "name": "智能手表 Ultra", "reason": "热门商品", "score": 0.88},
                {"product_id": 4, "name": "男士运动跑鞋", "reason": "相似用户也购买了", "score": 0.82},
            ],
            "source": "mock_data"
        },
        "process_payment": {
            "transaction_id": "TXN-20260713-001",
            "status": "支付成功",
            "amount": params.get("amount", 0),
            "source": "mock_data"
        },
    }

    default = {"result": f"{tool_name} 执行完成", "source": "mock_data"}
    return mock_data.get(tool_name, default)


# 保留 _mock_api_call 和 _mock_db_query 兼容旧引用
def _mock_api_call(api_name: str, params: dict) -> dict:
    """模拟 API 调用（同步包装，供 lambda handler 使用）"""
    return _fallback_mock(api_name, params)


def _mock_db_query(table: str, query: dict) -> dict:
    """模拟数据库查询"""
    logger.info(f"[Mock DB] 查询 {table}: {query}")
    # 根据表名返回对应的模拟数据字典
    table_mock = {
        "orders": {
            "order_id": query.get("order_id", "ORD-001"),
            "status": "已发货",
            "payment_status": "已支付",
            "order_amount": 159.99,
            "currency": "USD",
            "created_at": "2026-07-01",
            "shipping_info": {
                "carrier": "FedEx",
                "tracking_number": "TRK-US-12345",
                "estimated_delivery": "2026-07-20",
                "current_location": "洛杉矶转运中心",
            },
            "items": [
                {"product_id": "P001", "name": "蓝牙降噪耳机 Pro", "quantity": 1, "price": 159.99},
            ],
            "source": "mock_data",
        },
        "users": {
            "user_id": query.get("user_id", "U001"),
            "name": "张三",
            "email": "zhangsan@example.com",
            "preferences": ["电子产品", "运动户外"],
            "member_level": "金牌会员",
            "source": "mock_data",
        },
        "inventory": {
            "warehouse_id": query.get("warehouse_id", "WH-001"),
            "products": [
                {"product_id": pid, "quantity": 500, "status": "充足"}
                for pid in query.get("product_ids", ["P001"])
            ],
            "source": "mock_data",
        },
        "payments": {
            "user_id": query.get("user_id", "U001"),
            "transactions": [
                {"transaction_id": "TXN-001", "amount": 159.99, "status": "success", "date": "2026-07-01"},
                {"transaction_id": "TXN-002", "amount": 79.99, "status": "success", "date": "2026-06-15"},
            ],
            "source": "mock_data",
        },
    }
    return table_mock.get(table, {"records": [], "table": table, "source": "mock_data"})


# ============================================================
# 1. Market Research Agent 工具
# ============================================================
MARKET_RESEARCH_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="search_competitor_products",
        description="搜索竞品商品信息，支持关键词、品类、价格区间筛选",
        category=MCPToolCategory.SEARCH,
        parameters={
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array", "items": {"type": "string"},
                    "description": "搜索关键词列表"
                },
                "category": {
                    "type": "string",
                    "description": "商品品类"
                },
                "price_min": {
                    "type": "number",
                    "description": "最低价格"
                },
                "price_max": {
                    "type": "number",
                    "description": "最高价格"
                },
                "market": {
                    "type": "string",
                    "description": "目标市场（国家代码）"
                },
                "limit": {
                    "type": "integer", "default": 20,
                    "description": "返回数量限制"
                }
            },
            "required": ["keywords", "market"]
        },
        handler=lambda **kwargs: _fallback_mock("search_competitor_products", kwargs)
    ),
    create_mcp_tool(
        name="analyze_market_trends",
        description="分析市场趋势，包括搜索量趋势、价格走势、季节性分析",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "商品品类"},
                "market": {"type": "string", "description": "目标市场"},
                "period": {
                    "type": "string", "enum": ["7d", "30d", "90d", "1y"],
                    "description": "分析周期"
                },
                "metrics": {
                    "type": "array", "items": {"type": "string"},
                    "description": "分析指标: search_volume, price_trend, seasonality, competition_level"
                }
            },
            "required": ["category", "market"]
        },
        handler=lambda **kwargs: _fallback_mock("analyze_market_trends", kwargs)
    ),
    create_mcp_tool(
        name="fetch_product_rankings",
        description="获取商品排名数据（BSR、评分、评论数等）",
        category=MCPToolCategory.QUERY,
        parameters={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "商品品类"},
                "market": {"type": "string", "description": "目标市场"},
                "ranking_type": {
                    "type": "string",
                    "enum": ["bestseller", "new_release", "most_wished", "most_gifted"],
                    "description": "排名类型"
                },
                "limit": {"type": "integer", "default": 50}
            },
            "required": ["category", "market"]
        },
        handler=lambda **kwargs: _fallback_mock("fetch_product_rankings", kwargs)
    ),
    create_mcp_tool(
        name="compare_price_ranges",
        description="对比不同市场的价格区间，辅助定价决策",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array", "items": {"type": "string"},
                    "description": "商品 ID 列表"
                },
                "markets": {
                    "type": "array", "items": {"type": "string"},
                    "description": "对比市场列表"
                }
            },
            "required": ["product_ids", "markets"]
        },
        handler=lambda **kwargs: {"price_comparison": {"US": {"min": 29.99, "max": 199.99, "avg": 89.99}, "CN": {"min": 99, "max": 1299, "avg": 399}}, "source": "mock_data"}
    ),
    create_mcp_tool(
        name="generate_selection_report",
        description="生成选品分析报告，综合评分并给出推荐",
        category=MCPToolCategory.GENERATION,
        parameters={
            "type": "object",
            "properties": {
                "analysis_data": {
                    "type": "object",
                    "description": "分析数据（竞品、趋势、排名、价格）"
                },
                "criteria": {
                    "type": "object",
                    "description": "评分标准权重 {profit_margin, demand, competition, seasonality}"
                }
            },
            "required": ["analysis_data"]
        },
        handler=lambda **kwargs: _fallback_mock("generate_selection_report", kwargs)
    ),
]


# ============================================================
# 2. Advertising Agent 工具
# ============================================================
ADVERTISING_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="create_ad_campaign",
        description="创建广告投放活动",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string"},
                "platform": {"type": "string", "enum": ["google", "facebook", "tiktok", "amazon"]},
                "budget": {"type": "number", "description": "日预算"},
                "targeting": {"type": "object", "description": "定向设置"},
                "creatives": {"type": "array", "description": "广告创意素材"},
                "start_date": {"type": "string", "description": "开始日期"},
                "end_date": {"type": "string", "description": "结束日期"}
            },
            "required": ["campaign_name", "platform", "budget"]
        },
        handler=lambda **kwargs: {"campaign_id": "AD-001", "status": "created"}
    ),
    create_mcp_tool(
        name="analyze_ad_performance",
        description="分析广告投放效果",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "date_range": {"type": "object", "description": "{start, end}"},
                "metrics": {
                    "type": "array",
                    "description": "指标: impressions, clicks, ctr, cpc, conversions, roas"
                }
            },
            "required": ["campaign_id"]
        },
        handler=lambda **kwargs: {"ctr": 0.035, "roas": 3.2, "conversions": 150}
    ),
    create_mcp_tool(
        name="optimize_ad_targeting",
        description="优化广告定向策略",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "optimization_goal": {
                    "type": "string",
                    "enum": ["conversions", "clicks", "impressions", "roas"]
                }
            },
            "required": ["campaign_id"]
        },
        handler=lambda **kwargs: {"suggestions": ["调整受众年龄范围", "增加兴趣标签"]}
    ),
    create_mcp_tool(
        name="generate_ad_plan",
        description="生成广告投放计划",
        category=MCPToolCategory.GENERATION,
        parameters={
            "type": "object",
            "properties": {
                "products": {"type": "array", "description": "推广商品列表"},
                "total_budget": {"type": "number"},
                "platforms": {"type": "array"},
                "duration_days": {"type": "integer"}
            },
            "required": ["products", "total_budget"]
        },
        handler=lambda **kwargs: {"plan": "广告计划", "estimated_reach": 50000}
    ),
]


# ============================================================
# 3. Customer Service Agent 工具
# ============================================================
CUSTOMER_SERVICE_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="search_knowledge_base",
        description="搜索 RAG 知识库获取 FAQ 和政策信息",
        category=MCPToolCategory.SEARCH,
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"},
                "top_k": {"type": "integer", "default": 5},
                "filters": {"type": "object", "description": "过滤条件 {category, language}"}
            },
            "required": ["query"]
        },
        handler=lambda **kwargs: {"results": [{"content": "FAQ内容", "score": 0.95}]}
    ),
    create_mcp_tool(
        name="lookup_order_status",
        description="查询订单状态",
        category=MCPToolCategory.QUERY,
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "user_id": {"type": "string"}
            },
            "required": ["order_id"]
        },
        handler=_get_adapter_handler("lookup_order_status", "customer_service")
    ),
    create_mcp_tool(
        name="process_refund_request",
        description="处理退款请求",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {"type": "string"},
                "refund_amount": {"type": "number"},
                "user_id": {"type": "string"}
            },
            "required": ["order_id", "reason"]
        },
        handler=lambda **kwargs: {"refund_id": "RF-001", "status": "processing"}
    ),
    create_mcp_tool(
        name="generate_response",
        description="生成客服回复",
        category=MCPToolCategory.GENERATION,
        parameters={
            "type": "object",
            "properties": {
                "user_question": {"type": "string"},
                "context": {"type": "object", "description": "上下文信息"},
                "tone": {"type": "string", "enum": ["professional", "friendly", "empathetic"]}
            },
            "required": ["user_question"]
        },
        handler=lambda **kwargs: {"response": "感谢您的咨询，我来帮您处理..."}
    ),
]


# ============================================================
# 4. Supply Chain Agent 工具
# ============================================================
SUPPLY_CHAIN_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="forecast_demand",
        description="基于历史数据预测未来需求",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "product_ids": {"type": "array", "items": {"type": "string"}},
                "forecast_period_days": {"type": "integer", "default": 30},
                "method": {"type": "string", "enum": ["moving_average", "arima", "prophet"]}
            },
            "required": ["product_ids"]
        },
        handler=lambda **kwargs: {"forecast": [{"product_id": "P001", "predicted_demand": 500}]}
    ),
    create_mcp_tool(
        name="recommend_replenishment",
        description="基于预测和库存推荐补货方案",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "warehouse_id": {"type": "string"},
                "product_ids": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["warehouse_id"]
        },
        handler=lambda **kwargs: {"replenishment_plan": [{"product_id": "P001", "quantity": 200}]}
    ),
    create_mcp_tool(
        name="evaluate_supplier",
        description="评估供应商（交期、质量、价格、可靠性）",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "supplier_id": {"type": "string"},
                "evaluation_period": {"type": "string", "default": "90d"}
            },
            "required": ["supplier_id"]
        },
        handler=lambda **kwargs: {"score": 88.5, "ratings": {"delivery": 90, "quality": 85, "price": 92}}
    ),
]


# ============================================================
# 5. Order Management Agent 工具
# ============================================================
ORDER_MANAGEMENT_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="create_order",
        description="创建新订单",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "items": {"type": "array", "description": "[{product_id, quantity, price}]"},
                "shipping_address": {"type": "object"},
                "payment_method": {"type": "string"}
            },
            "required": ["user_id", "items"]
        },
        handler=_get_adapter_handler("create_order", "order_management")
    ),
    create_mcp_tool(
        name="cancel_order",
        description="取消订单",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason": {"type": "string"}
            },
            "required": ["order_id"]
        },
        handler=_get_adapter_handler("cancel_order", "order_management")
    ),
    create_mcp_tool(
        name="query_order_details",
        description="查询订单详情",
        category=MCPToolCategory.QUERY,
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "include_shipping": {"type": "boolean", "default": True},
                "include_payment": {"type": "boolean", "default": True}
            },
            "required": ["order_id"]
        },
        handler=_get_adapter_handler("query_order_details", "order_management")
    ),
    create_mcp_tool(
        name="update_order_status",
        description="更新订单状态",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "new_status": {
                    "type": "string",
                    "enum": ["confirmed", "processing", "shipped", "delivered", "cancelled"]
                },
                "note": {"type": "string"}
            },
            "required": ["order_id", "new_status"]
        },
        handler=lambda **kwargs: {"order_id": kwargs.get("order_id"), "status": kwargs.get("new_status")}
    ),
]


# ============================================================
# 6. Recommendation Agent 工具
# ============================================================
RECOMMENDATION_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="get_user_profile",
        description="获取用户画像（偏好、行为、购买历史）",
        category=MCPToolCategory.QUERY,
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "include_behavior": {"type": "boolean", "default": True}
            },
            "required": ["user_id"]
        },
        handler=_get_adapter_handler("get_user_profile", "recommendation")
    ),
    create_mcp_tool(
        name="rank_products",
        description="基于协同过滤和内容推荐对商品排序",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "candidate_ids": {"type": "array", "items": {"type": "string"}},
                "algorithm": {
                    "type": "string",
                    "enum": ["collaborative", "content_based", "hybrid"]
                },
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["user_id"]
        },
        handler=lambda **kwargs: {"ranked_products": []}
    ),
    create_mcp_tool(
        name="generate_personalized_feed",
        description="生成个性化推荐信息流",
        category=MCPToolCategory.GENERATION,
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "page": {"type": "string", "enum": ["home", "product_detail", "cart", "checkout"]},
                "limit": {"type": "integer", "default": 20}
            },
            "required": ["user_id"]
        },
        handler=lambda **kwargs: {"recommendations": [], "reason": []}
    ),
]


# ============================================================
# 7. Inventory Agent 工具
# ============================================================
INVENTORY_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="check_stock",
        description="查询商品库存",
        category=MCPToolCategory.QUERY,
        parameters={
            "type": "object",
            "properties": {
                "product_ids": {"type": "array", "items": {"type": "string"}},
                "warehouse_id": {"type": "string"}
            },
            "required": ["product_ids"]
        },
        handler=_get_adapter_handler("check_stock", "inventory")
    ),
    create_mcp_tool(
        name="record_inbound",
        description="记录商品入库",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "quantity": {"type": "integer"},
                "warehouse_id": {"type": "string"},
                "batch_number": {"type": "string"},
                "supplier_id": {"type": "string"}
            },
            "required": ["product_id", "quantity", "warehouse_id"]
        },
        handler=lambda **kwargs: {"inbound_id": "IN-001", "status": "recorded"}
    ),
    create_mcp_tool(
        name="stock_alert",
        description="检查库存预警并生成补货告警",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "warehouse_id": {"type": "string"},
                "threshold_ratio": {"type": "number", "default": 0.2}
            },
            "required": ["warehouse_id"]
        },
        handler=lambda **kwargs: {"alerts": []}
    ),
]


# ============================================================
# 8. Payment Agent 工具
# ============================================================
PAYMENT_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="process_payment",
        description="处理支付",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string", "default": "USD"},
                "payment_method": {
                    "type": "string",
                    "enum": ["credit_card", "paypal", "alipay", "wechat_pay", "bank_transfer"]
                }
            },
            "required": ["order_id", "amount", "payment_method"]
        },
        handler=lambda **kwargs: {"transaction_id": "TXN-001", "status": "success"}
    ),
    create_mcp_tool(
        name="refund_payment",
        description="处理退款",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string"},
                "amount": {"type": "number"},
                "reason": {"type": "string"}
            },
            "required": ["transaction_id", "amount"]
        },
        handler=lambda **kwargs: {"refund_id": "RF-001", "status": "processing"}
    ),
    create_mcp_tool(
        name="query_payment_history",
        description="查询支付历史",
        category=MCPToolCategory.QUERY,
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "date_range": {"type": "object"},
                "limit": {"type": "integer", "default": 50}
            },
            "required": ["user_id"]
        },
        handler=_get_adapter_handler("query_payment_history", "payment")
    ),
]


# ============================================================
# 9. Logistics Agent 工具
# ============================================================
LOGISTICS_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="track_shipment",
        description="追踪物流状态",
        category=MCPToolCategory.QUERY,
        parameters={
            "type": "object",
            "properties": {
                "tracking_number": {"type": "string"},
                "carrier": {"type": "string"}
            },
            "required": ["tracking_number"]
        },
        handler=_get_adapter_handler("track_shipment", "logistics")
    ),
    create_mcp_tool(
        name="select_carrier",
        description="根据目的地和时效要求选择快递公司",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "origin": {"type": "object", "description": "{country, city, postal_code}"},
                "destination": {"type": "object", "description": "{country, city, postal_code}"},
                "weight_kg": {"type": "number"},
                "delivery_speed": {"type": "string", "enum": ["standard", "express", "economy"]}
            },
            "required": ["origin", "destination"]
        },
        handler=lambda **kwargs: {"recommended_carrier": "DHL", "estimated_days": 5, "cost": 25.50}
    ),
    create_mcp_tool(
        name="estimate_delivery",
        description="预估配送时间",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "destination": {"type": "object"}
            },
            "required": ["order_id"]
        },
        handler=_get_adapter_handler("estimate_delivery", "logistics")
    ),
]


# ============================================================
# 10. Marketing Agent 工具
# ============================================================
MARKETING_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="create_campaign",
        description="创建营销活动",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string"},
                "campaign_type": {
                    "type": "string",
                    "enum": ["flash_sale", "seasonal_promo", "new_user", "loyalty", "clearance"]
                },
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "budget": {"type": "number"},
                "target_segments": {"type": "array"}
            },
            "required": ["campaign_name", "campaign_type", "start_date", "end_date"]
        },
        handler=lambda **kwargs: {"campaign_id": "CAMP-001", "status": "created"}
    ),
    create_mcp_tool(
        name="distribute_coupons",
        description="分发优惠券",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "coupon_template_id": {"type": "string"},
                "user_segments": {"type": "array"},
                "quantity": {"type": "integer"},
                "expiry_days": {"type": "integer", "default": 30}
            },
            "required": ["coupon_template_id", "user_segments"]
        },
        handler=lambda **kwargs: {"distributed_count": 1000, "coupon_ids": []}
    ),
    create_mcp_tool(
        name="analyze_campaign_roi",
        description="分析营销活动 ROI",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "campaign_id": {"type": "string"},
                "metrics": {"type": "array", "description": "revenue, cost, conversion_rate, new_users"}
            },
            "required": ["campaign_id"]
        },
        handler=lambda **kwargs: {"roi": 3.5, "revenue": 50000, "cost": 14285}
    ),
]


# ============================================================
# 11. User Behavior Agent 工具
# ============================================================
USER_BEHAVIOR_TOOLS: List[MCPTool] = [
    create_mcp_tool(
        name="track_page_view",
        description="记录页面浏览事件",
        category=MCPToolCategory.ACTION,
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "page_url": {"type": "string"},
                "referrer": {"type": "string"},
                "duration_seconds": {"type": "number"},
                "session_id": {"type": "string"}
            },
            "required": ["user_id", "page_url"]
        },
        handler=lambda **kwargs: {"event_id": "EVT-001", "recorded": True}
    ),
    create_mcp_tool(
        name="analyze_behavior_pattern",
        description="分析用户行为模式",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "analysis_period": {"type": "string", "default": "30d"},
                "metrics": {"type": "array", "description": "bounce_rate, avg_session, conversion_funnel"}
            },
            "required": ["user_id"]
        },
        handler=lambda **kwargs: {"patterns": {}, "insights": []}
    ),
    create_mcp_tool(
        name="segment_users",
        description="用户分群分析",
        category=MCPToolCategory.ANALYSIS,
        parameters={
            "type": "object",
            "properties": {
                "segmentation_type": {
                    "type": "string",
                    "enum": ["rfm", "behavioral", "demographic", "lifetime_value"]
                },
                "segment_count": {"type": "integer", "default": 5}
            },
            "required": ["segmentation_type"]
        },
        handler=lambda **kwargs: {"segments": [], "segment_stats": {}}
    ),
]


# ============================================================
# 工具注册表（按 Agent 聚合）
# ============================================================
AGENT_TOOLS_REGISTRY: Dict[str, List[MCPTool]] = {
    "market_research": MARKET_RESEARCH_TOOLS,
    "advertising": ADVERTISING_TOOLS,
    "customer_service": CUSTOMER_SERVICE_TOOLS,
    "supply_chain": SUPPLY_CHAIN_TOOLS,
    "order_management": ORDER_MANAGEMENT_TOOLS,
    "recommendation": RECOMMENDATION_TOOLS,
    "inventory": INVENTORY_TOOLS,
    "payment": PAYMENT_TOOLS,
    "logistics": LOGISTICS_TOOLS,
    "marketing": MARKETING_TOOLS,
    "user_behavior": USER_BEHAVIOR_TOOLS,
}


def get_tools_for_agent(agent_name: str) -> List[MCPTool]:
    """获取指定 Agent 的工具列表"""
    return AGENT_TOOLS_REGISTRY.get(agent_name, [])