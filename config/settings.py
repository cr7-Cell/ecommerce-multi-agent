"""
跨境电商多智能体系统 - 全局配置
基于 MCP 协议 + LangGraph Supervisor-Expert 协作模式
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# Agent 角色枚举
# ============================================================
class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    MARKET_RESEARCH = "market_research"       # 选品分析
    ADVERTISING = "advertising"               # 广告投放
    CUSTOMER_SERVICE = "customer_service"     # 客服
    SUPPLY_CHAIN = "supply_chain"             # 供应链预测
    ORDER_MANAGEMENT = "order_management"     # 订单管理
    RECOMMENDATION = "recommendation"         # 个性化推荐
    INVENTORY = "inventory"                   # 库存管理
    PAYMENT = "payment"                       # 支付处理
    LOGISTICS = "logistics"                   # 物流追踪
    MARKETING = "marketing"                   # 营销活动
    USER_BEHAVIOR = "user_behavior"           # 用户行为分析


# ============================================================
# MCP 协议配置
# ============================================================
@dataclass
class MCPConfig:
    """MCP (Model Context Protocol) 配置"""
    server_name: str = "cross_border_ecommerce_mcp"
    server_version: str = "1.0.0"
    transport: str = "stdio"  # stdio | sse | streamable-http
    max_tools_per_server: int = 50
    tool_timeout_seconds: int = 30
    # MCP 工具目录: 每个 Agent 暴露的工具列表
    agent_tools_mapping: Dict[str, List[str]] = field(default_factory=lambda: {
        AgentRole.MARKET_RESEARCH: [
            "search_competitor_products",
            "analyze_market_trends",
            "fetch_product_rankings",
            "compare_price_ranges",
            "generate_selection_report"
        ],
        AgentRole.ADVERTISING: [
            "create_ad_campaign",
            "set_ad_budget",
            "analyze_ad_performance",
            "optimize_ad_targeting",
            "generate_ad_plan"
        ],
        AgentRole.CUSTOMER_SERVICE: [
            "search_knowledge_base",
            "lookup_order_status",
            "process_refund_request",
            "escalate_to_human",
            "generate_response"
        ],
        AgentRole.SUPPLY_CHAIN: [
            "forecast_demand",
            "analyze_inventory_turnover",
            "recommend_replenishment",
            "evaluate_supplier",
            "optimize_warehouse"
        ],
        AgentRole.ORDER_MANAGEMENT: [
            "create_order",
            "cancel_order",
            "update_order_status",
            "query_order_details",
            "merge_orders"
        ],
        AgentRole.RECOMMENDATION: [
            "get_user_profile",
            "compute_similarity",
            "rank_products",
            "generate_personalized_feed",
            "track_recommendation_click"
        ],
        AgentRole.INVENTORY: [
            "check_stock",
            "record_inbound",
            "record_outbound",
            "stock_alert",
            "inventory_count"
        ],
        AgentRole.PAYMENT: [
            "process_payment",
            "refund_payment",
            "verify_transaction",
            "query_payment_history",
            "reconcile_accounts"
        ],
        AgentRole.LOGISTICS: [
            "track_shipment",
            "estimate_delivery",
            "select_carrier",
            "generate_label",
            "update_tracking"
        ],
        AgentRole.MARKETING: [
            "create_campaign",
            "distribute_coupons",
            "analyze_campaign_roi",
            "segment_audience",
            "schedule_promotion"
        ],
        AgentRole.USER_BEHAVIOR: [
            "track_page_view",
            "track_click",
            "track_purchase",
            "analyze_behavior_pattern",
            "segment_users"
        ],
    })


# ============================================================
# LLM 配置
# ============================================================
@dataclass
class LLMConfig:
    """LLM 模型配置"""
    provider: str = "deepseek"  # openai | ollama | azure
    model_name: str  = "deepseek-chat"
    temperature: float = 0.1
    max_tokens: int = 8192

    deepseek_api_key: str = field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = field(default_factory=lambda: os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))

    # Ollama 本地部署配置
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:5b"


# ============================================================
# Supervisor 路由提示词
# ============================================================
SUPERVISOR_SYSTEM_PROMPT = """你是跨境电商多智能体系统的 Supervisor（主控 Agent）。

你的职责：
1. 分析用户请求，理解其意图和所需处理流程
2. 根据任务类型，将任务路由到最合适的 Expert Agent
3. 协调多个 Expert Agent 之间的协作顺序
4. 整合各 Expert 的输出，生成最终答案

可用的 Expert Agent 及其职责：
- market_research: 选品分析、竞品调研、市场趋势分析
- advertising: 广告投放策略、预算分配、效果分析
- customer_service: 客户咨询、售后处理、FAQ回答
- supply_chain: 需求预测、供应商评估、补货建议
- order_management: 订单创建、查询、取消、状态更新
- recommendation: 个性化商品推荐、用户画像分析
- inventory: 库存查询、入库出库、库存预警
- payment: 支付处理、退款、交易查询
- logistics: 物流追踪、快递选择、配送预估
- marketing: 营销活动创建、优惠券分发、效果分析
- user_behavior: 用户行为分析、用户分群、偏好挖掘

路由规则：
- 选品/市场调研 → market_research
- 广告投放/营销效果 → advertising
- 客户咨询/售后 → customer_service
- 供应链/补货/预测 → supply_chain
- 订单操作/查询 → order_management
- 商品推荐/个性化 → recommendation
- 库存查询/管理 → inventory
- 支付/退款/结算 → payment
- 物流/配送/追踪 → logistics
- 促销活动/优惠券 → marketing
- 用户分析/行为数据 → user_behavior

你必须以 JSON 格式输出路由决策：
{{
    "next_agent": "<agent_name>",
    "reasoning": "<路由理由>",
    "task_description": "<传递给专家的任务描述>",
    "requires_multi_agent": true/false,
    "agent_sequence": ["<agent1>", "<agent2>"]  // 多Agent协作时的执行顺序
}}

如果任务已完成，请设置 next_agent 为 "FINISH"。
"""

# ============================================================
# 数据库配置
# ============================================================
@dataclass
class DatabaseConfig:
    """数据库连接配置"""
    db_type: str = "postgresql"  # postgresql | mysql
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "cross_border_ecommerce")
    username: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "")
    # 向量数据库配置 (用于 RAG)
    vector_db_type: str = "pgvector"  # pgvector | milvus | chromadb
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536


# ============================================================
# LLM 实例工厂
# ============================================================
def get_llm(config: LLMConfig = None):
    """
    创建 LLM 实例，支持 OpenAI / DeepSeek / Ollama / Azure 后端

    返回: LangChain BaseChatModel 实例
    """
    if config is None:
        config = LLMConfig()

    if config.provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=config.ollama_model,
                base_url=config.ollama_base_url,
                temperature=config.temperature,
            )
        except ImportError:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=config.ollama_model,
                base_url=config.ollama_base_url,
                temperature=config.temperature,
            )
    elif config.provider == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            base_url=f"{config.deepseek_base_url.rstrip('/')}/v1",
            api_key=config.deepseek_api_key,
        )
    elif config.provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    elif config.provider == "azure":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    else:
        raise ValueError(f"不支持的 LLM provider: {config.provider}")


# ============================================================
# 全局配置聚合
# ============================================================
@dataclass
class SystemConfig:
    mcp: MCPConfig = field(default_factory=MCPConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    max_agent_iterations: int = 10
    enable_tracing: bool = True  # LangSmith/LangFuse 追踪
    log_level: str = "INFO"

    def get_llm_instance(self):
        """获取 LLM 实例"""
        return get_llm(self.llm)


# 单例
system_config = SystemConfig()