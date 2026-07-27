"""
SQLAlchemy ORM 模型定义
对应 database/schema.sql 中的所有表
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Numeric, Boolean,
    Date, DateTime, Float, ForeignKey, JSON, Enum as SAEnum,
    Index, UniqueConstraint, CheckConstraint, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB


class Base(DeclarativeBase):
    pass


# ============================================================
# 用户表
# ============================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    gender: Mapped[Optional[str]] = mapped_column(String(10))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    language: Mapped[str] = mapped_column(String(10), default="en")
    status: Mapped[str] = mapped_column(String(20), default="active")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict)
    membership_level: Mapped[str] = mapped_column(String(20), default="normal")
    reward_points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # 关系
    orders: Mapped[List["Order"]] = relationship(back_populates="user")
    payments: Mapped[List["Payment"]] = relationship(back_populates="user")
    behaviors: Mapped[List["UserBehavior"]] = relationship(back_populates="user")


# ============================================================
# 商品表
# ============================================================
class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    category_id: Mapped[Optional[int]] = mapped_column(Integer)
    brand: Mapped[Optional[str]] = mapped_column(String(200))
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    sale_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    cost_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    min_stock: Mapped[int] = mapped_column(Integer, default=10)
    max_stock: Mapped[int] = mapped_column(Integer, default=1000)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    main_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    image_urls: Mapped[dict] = mapped_column(JSONB, default=list)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    target_market: Mapped[str] = mapped_column(String(10), default="GLOBAL")
    hs_code: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="active")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("suppliers.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


# ============================================================
# 订单表
# ============================================================
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")
    fulfillment_status: Mapped[str] = mapped_column(String(20), default="unfulfilled")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    shipping_address: Mapped[dict] = mapped_column(JSONB, nullable=False)
    billing_address: Mapped[Optional[dict]] = mapped_column(JSONB)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(50))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    customer_note: Mapped[Optional[str]] = mapped_column(Text)
    internal_note: Mapped[Optional[str]] = mapped_column(Text)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(50), default="web")
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order")
    payment: Mapped[Optional["Payment"]] = relationship(back_populates="order", uselist=False)
    logistics: Mapped[Optional["Logistics"]] = relationship(back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    product_image: Mapped[Optional[str]] = mapped_column(String(500))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    order: Mapped["Order"] = relationship(back_populates="items")


# ============================================================
# 支付表
# ============================================================
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    method: Mapped[Optional[str]] = mapped_column(String(20))
    gateway: Mapped[Optional[str]] = mapped_column(String(50))
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSONB)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    order: Mapped["Order"] = relationship(back_populates="payment")
    user: Mapped["User"] = relationship(back_populates="payments")


# ============================================================
# 物流表
# ============================================================
class Logistics(Base):
    __tablename__ = "logistics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.id"), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    tracking_number: Mapped[str] = mapped_column(String(100), nullable=False)
    carrier: Mapped[str] = mapped_column(String(100), nullable=False)
    carrier_code: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    current_location: Mapped[Optional[str]] = mapped_column(String(300))
    origin_address: Mapped[Optional[dict]] = mapped_column(JSONB)
    destination_address: Mapped[Optional[dict]] = mapped_column(JSONB)
    estimated_delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    shipping_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    insurance_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 3))
    has_exception: Mapped[bool] = mapped_column(Boolean, default=False)
    exception_detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    order: Mapped["Order"] = relationship(back_populates="logistics")


# ============================================================
# 用户行为表
# ============================================================
class UserBehavior(Base):
    __tablename__ = "user_behaviors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"))
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    behavior_type: Mapped[str] = mapped_column(String(20), nullable=False)
    page_url: Mapped[Optional[str]] = mapped_column(String(1000))
    referrer_url: Mapped[Optional[str]] = mapped_column(String(1000))
    product_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("products.id"))
    duration_seconds: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    scroll_depth: Mapped[Optional[int]] = mapped_column(Integer)
    interaction_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    device_type: Mapped[Optional[str]] = mapped_column(String(20))
    browser: Mapped[Optional[str]] = mapped_column(String(100))
    os: Mapped[Optional[str]] = mapped_column(String(50))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    utm_source: Mapped[Optional[str]] = mapped_column(String(100))
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100))
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100))
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped[Optional["User"]] = relationship(back_populates="behaviors")


# ============================================================
# 库存表
# ============================================================
class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    safety_stock: Mapped[int] = mapped_column(Integer, default=10)
    reorder_point: Mapped[int] = mapped_column(Integer, default=20)
    warehouse_name: Mapped[Optional[str]] = mapped_column(String(200))
    location_code: Mapped[Optional[str]] = mapped_column(String(50))
    zone: Mapped[Optional[str]] = mapped_column(String(50))
    batch_number: Mapped[Optional[str]] = mapped_column(String(100))
    production_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_counted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 营销活动表
# ============================================================
class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    campaign_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    discount_rules: Mapped[dict] = mapped_column(JSONB, nullable=False)
    total_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    used_budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    target_segments: Mapped[Optional[dict]] = mapped_column(JSONB)
    target_products: Mapped[Optional[dict]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_discount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 市场数据表
# ============================================================
class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    keyword: Mapped[Optional[str]] = mapped_column(String(200))
    data_source: Mapped[Optional[str]] = mapped_column(String(100))
    title: Mapped[Optional[str]] = mapped_column(String(500))
    data_content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    relevance_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    data_date: Mapped[date] = mapped_column(Date, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================
# 广告计划表
# ============================================================
class AdvertisingPlan(Base):
    __tablename__ = "advertising_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    external_campaign_id: Mapped[Optional[str]] = mapped_column(String(100))
    daily_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    total_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    spent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    targeting: Mapped[Optional[dict]] = mapped_column(JSONB)
    creatives: Mapped[Optional[dict]] = mapped_column(JSONB)
    product_ids: Mapped[Optional[dict]] = mapped_column(JSONB)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
    cpc: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    roas: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    generated_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 客服对话表
# ============================================================
class CustomerServiceConversation(Base):
    __tablename__ = "customer_service_conversations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"))
    subject: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="active")
    channel: Mapped[str] = mapped_column(String(20), default="chat")
    order_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("orders.id"))
    intent: Mapped[Optional[str]] = mapped_column(String(50))
    sentiment: Mapped[Optional[str]] = mapped_column(String(20))
    priority: Mapped[str] = mapped_column(String(10), default="normal")
    handled_by_agent: Mapped[bool] = mapped_column(Boolean, default=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100))
    escalated_to_human: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 供应链预测表
# ============================================================
class SupplyChainForecast(Base):
    __tablename__ = "supply_chain_forecasts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, ForeignKey("warehouses.id"), nullable=False)
    forecast_period_days: Mapped[int] = mapped_column(Integer, nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_method: Mapped[Optional[str]] = mapped_column(String(50))
    predicted_demand: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence_lower: Mapped[Optional[int]] = mapped_column(Integer)
    confidence_upper: Mapped[Optional[int]] = mapped_column(Integer)
    confidence_level: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0.95)
    actual_demand: Mapped[Optional[int]] = mapped_column(Integer)
    forecast_error: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    forecast_accuracy: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    recommended_reorder: Mapped[Optional[int]] = mapped_column(Integer)
    recommended_safety_stock: Mapped[Optional[int]] = mapped_column(Integer)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    potential_saving: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    generated_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================
# Agent 任务日志表
# ============================================================
class AgentTaskLog(Base):
    __tablename__ = "agent_task_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_role: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[str] = mapped_column(String(10), default="normal")
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    react_steps: Mapped[dict] = mapped_column(JSONB, default=list)
    tool_calls: Mapped[dict] = mapped_column(JSONB, default=list)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    token_usage: Mapped[Optional[dict]] = mapped_column(JSONB)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100))
    mcp_calls_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================
# 知识库表
# ============================================================
class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    doc_uuid: Mapped[str] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True)
    doc_id: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_total: Mapped[int] = mapped_column(Integer, default=1)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    sub_category: Mapped[Optional[str]] = mapped_column(String(200))
    tags: Mapped[dict] = mapped_column(JSONB, default=list)
    market: Mapped[str] = mapped_column(String(10), default="GLOBAL")
    language: Mapped[str] = mapped_column(String(10), default="en")
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    source_type: Mapped[Optional[str]] = mapped_column(String(50))
    author: Mapped[Optional[str]] = mapped_column(String(200))
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 供应商表
# ============================================================
class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 仓库表
# ============================================================
class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)