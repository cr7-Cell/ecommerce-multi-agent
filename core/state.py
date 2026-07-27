"""
跨境电商多智能体系统 - 状态定义与映射函数
============================================
核心设计：Main Graph State ↔ Subgraph States 之间的数据流与映射关系

架构图:
┌─────────────────────────────────────────────────────────────┐
│                    Main Graph State (主图状态)                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  messages | user_query | current_task | assigned_     │  │
│  │  expert | task_history | expert_outputs | routing_    │  │
│  │  decision | final_answer | user_context | metadata    │  │
│  └───────────────────────────────────────────────────────┘  │
│         │              │              │                     │
│    map_main_to_    map_main_to_   map_main_to_              │
│    expert(A)       expert(B)      expert(C)                 │
│         │              │              │                     │
│         ▼              ▼              ▼                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Subgraph │  │ Subgraph │  │ Subgraph │  ...             │
│  │ State A  │  │ State B  │  │ State C  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│         │              │              │                     │
│    map_expert_    map_expert_   map_expert_                 │
│    to_main(A)     to_main(B)    to_main(C)                  │
│         │              │              │                     │
│         ▼              ▼              ▼                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │        expert_outputs[A]  expert_outputs[B]  ...       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
"""

from typing import Annotated, Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import operator
from datetime import datetime
from uuid import uuid4


# ============================================================
# 基础类型定义
# ============================================================
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class Message:
    """对话消息"""
    def __init__(self, role: str, content: str, agent: str = "user",
                 timestamp: str = ""):
        self.role = role
        self.content = content
        self.agent = agent
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "agent": self.agent,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        return cls(
            role=d.get("role", "user"),
            content=d.get("content", ""),
            agent=d.get("agent", "user"),
            timestamp=d.get("timestamp", "")
        )


@dataclass
class RoutingDecision:
    """Supervisor 路由决策"""
    next_agent: str
    reasoning: str
    task_description: str
    requires_multi_agent: bool = False
    agent_sequence: List[str] = field(default_factory=list)


@dataclass
class TaskRecord:
    """任务记录"""
    task_id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    input_data: dict = field(default_factory=dict)
    output_data: dict = field(default_factory=dict)
    error: Optional[str] = None
    started_at: str = ""
    completed_at: str = ""
    duration_ms: float = 0.0


# ============================================================
# Main Graph State（主图状态）
# ============================================================
class MainGraphState(TypedDict):
    """
    主图状态 —— 所有 Agent 共享的全局状态

    映射关系说明：
    - 主图状态中的字段通过 map_main_to_expert() 映射到子图状态
    - 子图状态通过 map_expert_to_main() 将结果写回主图状态
    """
    # === 对话信息 ===
    messages: Annotated[List[dict], operator.add]  # 消息列表（累加合并）
    user_query: str  # 用户原始查询

    # === 任务管理 ===
    current_task: str  # 当前任务描述
    assigned_expert: str  # 当前分配的专家
    task_history: List[dict]  # 任务历史记录

    # === 专家输出 ===
    expert_outputs: Dict[str, Any]  # 各专家执行结果 {agent_name: output}

    # === 路由控制 ===
    routing_decision: Optional[dict]  # Supervisor 路由决策
    next_agent: str  # 下一个要执行的 Agent（"FINISH" 表示结束）

    # === 用户上下文 ===
    user_context: dict  # 用户上下文信息 {user_id, name, preferences, ...}

    # === 最终输出 ===
    final_answer: str  # 最终答案

    # === 元数据 ===
    session_id: str  # 会话 ID
    iteration_count: int  # 循环迭代计数
    metadata: dict  # 额外元数据


# ============================================================
# Subgraph States（子图状态 - 各 Expert Agent 专用）
# ============================================================

class MarketResearchState(TypedDict):
    """选品分析 Agent 状态"""
    search_keywords: List[str]  # 搜索关键词
    target_market: str  # 目标市场（国家/地区）
    competitor_data: List[dict]  # 竞品数据
    market_trends: dict  # 市场趋势分析
    price_analysis: dict  # 价格区间分析
    selected_products: List[dict]  # 选品结果
    analysis_report: str  # 分析报告
    # 从主状态传入
    task_description: str
    user_context: dict


class AdvertisingState(TypedDict):
    """广告投放 Agent 状态"""
    target_products: List[dict]  # 目标推广商品
    budget: float  # 广告预算
    platform: str  # 广告平台（Google/Facebook/TikTok...）
    target_audience: dict  # 目标受众
    ad_creatives: List[dict]  # 广告创意素材
    campaign_id: str  # 广告活动 ID
    ad_plans: List[dict]  # 广告计划列表
    performance_metrics: dict  # 效果指标
    roi_analysis: dict  # ROI 分析
    # 从主状态传入
    task_description: str
    user_context: dict


class CustomerServiceState(TypedDict):
    """客服 Agent 状态"""
    user_question: str  # 用户问题
    conversation_context: List[dict]  # 对话上下文
    sentiment: str  # 情感分析结果
    intent: str  # 意图识别
    faq_results: List[dict]  # FAQ 检索结果
    knowledge_base_hits: List[dict]  # 知识库命中
    refund_eligible: bool  # 是否可退款
    order_info: Optional[dict]  # 关联订单信息
    generated_response: str  # 生成的回复
    escalated: bool  # 是否转人工
    # 从主状态传入
    task_description: str
    user_context: dict


class SupplyChainState(TypedDict):
    """供应链预测 Agent 状态"""
    forecast_period: int  # 预测周期（天）
    historical_orders: List[dict]  # 历史订单数据
    demand_forecast: dict  # 需求预测结果
    inventory_plan: dict  # 库存计划
    supplier_recommendations: List[dict]  # 供应商推荐
    warehouse_utilization: dict  # 仓储利用率
    turnover_rate: float  # 库存周转率
    replenishment_suggestions: List[dict]  # 补货建议
    # 从主状态传入
    task_description: str
    user_context: dict


class OrderManagementState(TypedDict):
    """订单管理 Agent 状态"""
    order_id: Optional[str]  # 订单 ID
    order_action: str  # 操作类型 (create/query/cancel/update)
    order_details: dict  # 订单详情
    customer_info: dict  # 客户信息
    product_list: List[dict]  # 订单商品列表
    order_status: str  # 订单状态
    payment_status: str  # 支付状态
    shipping_info: dict  # 配送信息
    order_history: List[dict]  # 订单历史
    # 从主状态传入
    task_description: str
    user_context: dict


class RecommendationState(TypedDict):
    """个性化推荐 Agent 状态"""
    user_profile: dict  # 用户画像
    browsing_history: List[dict]  # 浏览历史
    purchase_history: List[dict]  # 购买历史
    preferred_categories: List[str]  # 偏好品类
    candidate_products: List[dict]  # 候选商品池
    ranking_scores: List[dict]  # 排序分数
    recommended_products: List[dict]  # 推荐结果
    recommendation_reason: List[str]  # 推荐理由
    # 从主状态传入
    task_description: str
    user_context: dict


class InventoryState(TypedDict):
    """库存管理 Agent 状态"""
    warehouse_id: str  # 仓库 ID
    product_id: Optional[str]  # 商品 ID
    stock_level: int  # 当前库存量
    safety_stock: int  # 安全库存阈值
    inbound_records: List[dict]  # 入库记录
    outbound_records: List[dict]  # 出库记录
    stock_alerts: List[dict]  # 库存预警
    batch_info: dict  # 批次信息
    # 从主状态传入
    task_description: str
    user_context: dict


class PaymentState(TypedDict):
    """支付处理 Agent 状态"""
    payment_method: str  # 支付方式
    amount: float  # 支付金额
    currency: str  # 币种
    transaction_id: str  # 交易 ID
    payment_status: str  # 支付状态
    refund_info: dict  # 退款信息
    payment_history: List[dict]  # 支付历史
    reconciliation: dict  # 对账信息
    # 从主状态传入
    task_description: str
    user_context: dict


class LogisticsState(TypedDict):
    """物流追踪 Agent 状态"""
    tracking_number: str  # 运单号
    carrier: str  # 快递公司
    shipment_status: str  # 配送状态
    estimated_delivery: str  # 预计送达
    origin_address: dict  # 发货地址
    destination_address: dict  # 收货地址
    tracking_history: List[dict]  # 追踪历史
    delivery_exception: Optional[dict]  # 配送异常
    # 从主状态传入
    task_description: str
    user_context: dict


class MarketingState(TypedDict):
    """营销活动 Agent 状态"""
    campaign_type: str  # 活动类型 (coupon/discount/flash_sale)
    campaign_name: str  # 活动名称
    target_audience: dict  # 目标受众分群
    discount_rules: dict  # 折扣规则
    promotion_period: dict  # 活动周期 {start, end}
    coupon_templates: List[dict]  # 优惠券模板
    budget: float  # 活动预算
    performance_metrics: dict  # 效果指标
    roi: float  # 投资回报率
    # 从主状态传入
    task_description: str
    user_context: dict


class UserBehaviorState(TypedDict):
    """用户行为分析 Agent 状态"""
    user_id: str  # 用户 ID
    session_data: dict  # 会话数据
    click_stream: List[dict]  # 点击流
    page_views: List[dict]  # 页面浏览
    behavior_patterns: dict  # 行为模式
    user_segment: str  # 用户分群
    churn_risk: float  # 流失风险
    conversion_probability: float  # 转化概率
    segment_analysis: dict  # 分群分析
    # 从主状态传入
    task_description: str
    user_context: dict


# ============================================================
# 状态映射函数（State Mapping Functions）
# ============================================================
# 核心设计：
#   map_main_to_expert: MainGraphState → ExpertSubgraphState（提取→注入）
#   map_expert_to_main: ExpertSubgraphState → MainGraphState（结果→回写）
# 这两个函数构成了 Main Graph 与 Subgraph 之间的双向数据管道


def map_main_to_expert(main_state: MainGraphState, expert_name: str) -> Dict[str, Any]:
    """
    主图状态 → 子图状态 映射函数
    从主图状态中提取与特定 Expert 相关的数据，注入子图状态

    映射策略：
    - task_description: 从主状态的 current_task 复制
    - user_context: 从主状态直接引用
    - 其他字段: 从 expert_outputs 中提取该 Expert 的历史输出
    """
    base = {
        "task_description": main_state.get("current_task", ""),
        "user_context": main_state.get("user_context", {}),
        "expert_outputs": main_state.get("expert_outputs", {}),  # 前序 Expert 的输出
    }

    # 如果该 Expert 之前有输出，将其作为上下文传入
    prev_output = main_state.get("expert_outputs", {}).get(expert_name)
    if prev_output:
        base["previous_output"] = prev_output

    return base


def map_expert_to_main(expert_state: Dict[str, Any], expert_name: str,
                       main_state: MainGraphState) -> Dict[str, Any]:
    """
    子图状态 → 主图状态 映射函数
    将 Expert 执行结果写回主图状态

    回写策略：
    - expert_outputs: 将 Expert 完整输出存入 expert_outputs[expert_name]
    - task_history: 追加任务完成记录
    - messages: 追加 Expert 的响应消息
    - 其他字段: 根据 Expert 类型更新对应上下文
    """
    import copy

    # 构建 Expert 输出摘要
    expert_output = _extract_expert_output(expert_name, expert_state)

    updates = {
        "expert_outputs": {expert_name: copy.deepcopy(expert_output)},
    }

    # 追加任务历史
    task_record = {
        "agent": expert_name,
        "status": "completed",
        "output_summary": _summarize_output(expert_name, expert_output),
        "timestamp": datetime.now().isoformat()
    }
    updates["task_history"] = [task_record]

    # 追加消息
    response_msg = {
        "role": "assistant",
        "content": _format_expert_response(expert_name, expert_output),
        "agent": expert_name,
        "timestamp": datetime.now().isoformat()
    }
    updates["messages"] = [response_msg]

    return updates


def _extract_expert_output(expert_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """提取 Expert 输出中的关键字段"""
    # 根据不同的 Expert 类型，提取关键输出字段
    key_fields_map = {
        "market_research": ["selected_products", "analysis_report", "price_analysis",
                           "market_trends", "competitor_data", "summary"],
        "advertising": ["ad_plans", "campaign_id", "performance_metrics",
                       "roi_analysis", "budget"],
        "customer_service": ["generated_response", "sentiment", "intent",
                            "refund_eligible", "escalated", "order_info"],
        "supply_chain": ["demand_forecast", "inventory_plan",
                        "supplier_recommendations", "replenishment_suggestions",
                        "turnover_rate"],
        "order_management": ["order_details", "order_status", "order_history",
                            "payment_status", "shipping_info", "summary"],
        "recommendation": ["recommended_products", "ranking_scores",
                          "recommendation_reason", "user_profile"],
        "inventory": ["stock_level", "safety_stock", "stock_alerts",
                     "inbound_records", "outbound_records"],
        "payment": ["transaction_id", "payment_status", "refund_info",
                   "payment_history", "reconciliation"],
        "logistics": ["tracking_number", "shipment_status", "estimated_delivery",
                     "tracking_history", "delivery_exception"],
        "marketing": ["campaign_name", "discount_rules", "coupon_templates",
                     "performance_metrics", "roi"],
        "user_behavior": ["behavior_patterns", "user_segment", "churn_risk",
                         "conversion_probability", "segment_analysis"],
    }

    key_fields = key_fields_map.get(expert_name, [])
    output = {}
    for field in key_fields:
        if field in state:
            output[field] = state[field]
    return output


def _summarize_output(expert_name: str, output: Dict[str, Any]) -> str:
    """生成输出摘要"""
    summaries = {
        "market_research": f"选品分析完成，推荐 {len(output.get('selected_products', []))} 个商品",
        "advertising": f"广告计划生成完成，预算 {output.get('budget', 'N/A')}",
        "customer_service": f"客服回复: {output.get('generated_response', '')[:50]}...",
        "supply_chain": f"需求预测完成，库存周转率 {output.get('turnover_rate', 'N/A')}",
        "order_management": f"订单操作完成，状态: {output.get('order_status', 'N/A')}",
        "recommendation": f"推荐 {len(output.get('recommended_products', []))} 个商品",
        "inventory": f"库存查询完成，当前库存: {output.get('stock_level', 'N/A')}",
        "payment": f"支付处理完成，状态: {output.get('payment_status', 'N/A')}",
        "logistics": f"物流追踪: {output.get('shipment_status', 'N/A')}",
        "marketing": f"营销活动: {output.get('campaign_name', 'N/A')}",
        "user_behavior": f"用户分群: {output.get('user_segment', 'N/A')}",
    }
    return summaries.get(expert_name, f"{expert_name} 任务完成")


def _format_expert_response(expert_name: str, output: Dict[str, Any]) -> str:
    """格式化 Expert 响应消息"""
    formatters = {
        "market_research": lambda o: (
            f"📊 选品分析报告\n\n"
            f"市场趋势: {o.get('market_trends', {})}\n"
            f"推荐商品: {len(o.get('selected_products', []))} 个\n"
            f"详细报告: {o.get('analysis_report', '')}"
        ),
        "advertising": lambda o: (
            f"📢 广告投放计划\n\n"
            f"活动ID: {o.get('campaign_id', 'N/A')}\n"
            f"预算: {o.get('budget', 'N/A')}\n"
            f"ROI分析: {o.get('roi_analysis', {})}"
        ),
        "customer_service": lambda o: o.get('generated_response', ''),
        "supply_chain": lambda o: (
            f"📦 供应链分析\n\n"
            f"需求预测: {o.get('demand_forecast', {})}\n"
            f"补货建议: {len(o.get('replenishment_suggestions', []))} 条"
        ),
        "order_management": lambda o: (
            f"📋 订单信息\n\n"
            f"订单状态: {o.get('order_status', 'N/A')}\n"
            f"支付状态: {o.get('payment_status', 'N/A')}"
        ),
        "recommendation": lambda o: (
            f"🎯 个性化推荐\n\n"
            f"为您推荐 {len(o.get('recommended_products', []))} 个商品"
        ),
        "inventory": lambda o: (
            f"📊 库存信息\n\n"
            f"当前库存: {o.get('stock_level', 'N/A')}\n"
            f"预警: {len(o.get('stock_alerts', []))} 条"
        ),
        "payment": lambda o: (
            f"💰 支付状态: {o.get('payment_status', 'N/A')}"
        ),
        "logistics": lambda o: (
            f"🚚 物流状态: {o.get('shipment_status', 'N/A')}\n"
            f"预计送达: {o.get('estimated_delivery', 'N/A')}"
        ),
        "marketing": lambda o: (
            f"🎉 营销活动: {o.get('campaign_name', 'N/A')}\n"
            f"ROI: {o.get('roi', 'N/A')}"
        ),
        "user_behavior": lambda o: (
            f"👤 用户分析\n\n"
            f"用户分群: {o.get('user_segment', 'N/A')}\n"
            f"流失风险: {o.get('churn_risk', 'N/A')}\n"
            f"转化概率: {o.get('conversion_probability', 'N/A')}"
        ),
    }

    formatter = formatters.get(expert_name, lambda o: str(o))
    return formatter(output)


# ============================================================
# 状态初始化工厂函数
# ============================================================
def create_initial_main_state(user_query: str, user_context: dict = None) -> MainGraphState:
    """创建初始主图状态"""
    return MainGraphState(
        messages=[Message(role="user", content=user_query).to_dict()],
        user_query=user_query,
        current_task="",
        assigned_expert="",
        task_history=[],
        expert_outputs={},
        routing_decision=None,
        next_agent="supervisor",  # 从 Supervisor 开始
        user_context=user_context or {},
        final_answer="",
        session_id=str(uuid4()),
        iteration_count=0,
        metadata={"created_at": datetime.now().isoformat()}
    )


def create_initial_expert_state(expert_name: str, main_state: MainGraphState) -> Dict[str, Any]:
    """创建 Expert 子图初始状态（通过映射函数）"""
    expert_state = map_main_to_expert(main_state, expert_name)
    # 添加 Expert 特有字段的默认值
    expert_defaults = {
        "market_research": {
            "search_keywords": [], "target_market": "", "competitor_data": [],
            "market_trends": {}, "price_analysis": {}, "selected_products": [],
            "analysis_report": ""
        },
        "advertising": {
            "target_products": [], "budget": 0.0, "platform": "",
            "target_audience": {}, "ad_creatives": [], "campaign_id": "",
            "ad_plans": [], "performance_metrics": {}, "roi_analysis": {}
        },
        "customer_service": {
            "user_question": "", "conversation_context": [], "sentiment": "",
            "intent": "", "faq_results": [], "knowledge_base_hits": [],
            "refund_eligible": False, "order_info": None,
            "generated_response": "", "escalated": False
        },
        "supply_chain": {
            "forecast_period": 30, "historical_orders": [], "demand_forecast": {},
            "inventory_plan": {}, "supplier_recommendations": [],
            "warehouse_utilization": {}, "turnover_rate": 0.0,
            "replenishment_suggestions": []
        },
        "order_management": {
            "order_id": None, "order_action": "query", "order_details": {},
            "customer_info": {}, "product_list": [], "order_status": "",
            "payment_status": "", "shipping_info": {}, "order_history": []
        },
        "recommendation": {
            "user_profile": {}, "browsing_history": [], "purchase_history": [],
            "preferred_categories": [], "candidate_products": [],
            "ranking_scores": [], "recommended_products": [], "recommendation_reason": []
        },
        "inventory": {
            "warehouse_id": "", "product_id": None, "stock_level": 0,
            "safety_stock": 0, "inbound_records": [], "outbound_records": [],
            "stock_alerts": [], "batch_info": {}
        },
        "payment": {
            "payment_method": "", "amount": 0.0, "currency": "USD",
            "transaction_id": "", "payment_status": "pending",
            "refund_info": {}, "payment_history": [], "reconciliation": {}
        },
        "logistics": {
            "tracking_number": "", "carrier": "", "shipment_status": "",
            "estimated_delivery": "", "origin_address": {},
            "destination_address": {}, "tracking_history": [],
            "delivery_exception": None
        },
        "marketing": {
            "campaign_type": "", "campaign_name": "", "target_audience": {},
            "discount_rules": {}, "promotion_period": {}, "coupon_templates": [],
            "budget": 0.0, "performance_metrics": {}, "roi": 0.0
        },
        "user_behavior": {
            "user_id": "", "session_data": {}, "click_stream": [],
            "page_views": [], "behavior_patterns": {}, "user_segment": "",
            "churn_risk": 0.0, "conversion_probability": 0.0, "segment_analysis": {}
        },
    }

    expert_state.update(expert_defaults.get(expert_name, {}))
    return expert_state