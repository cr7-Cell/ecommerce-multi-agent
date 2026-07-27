-- ============================================================
-- 跨境电商多智能体系统 - 数据库表结构设计
-- 数据库: cross_border_ecommerce
-- 版本: 1.0.0
-- 包含 14 张核心业务表 + 扩展枚举类型
-- ============================================================

-- 创建数据库（如需要）
-- CREATE DATABASE cross_border_ecommerce;
-- \c cross_border_ecommerce;

-- 启用 pgvector 扩展（用于向量知识库）
-- CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================================
-- 扩展枚举类型定义
-- ============================================================

-- 用户状态
DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('active', 'inactive', 'banned', 'pending');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 订单状态
DO $$ BEGIN
    CREATE TYPE order_status AS ENUM (
        'pending', 'confirmed', 'processing', 'shipped',
        'delivered', 'cancelled', 'refunded', 'returned'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 支付状态
DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM (
        'pending', 'processing', 'success', 'failed', 'refunded', 'partially_refunded'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 支付方式
DO $$ BEGIN
    CREATE TYPE payment_method AS ENUM (
        'credit_card', 'debit_card', 'paypal', 'alipay',
        'wechat_pay', 'bank_transfer', 'crypto', 'cod'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 物流状态
DO $$ BEGIN
    CREATE TYPE logistics_status AS ENUM (
        'pending', 'picked_up', 'in_transit', 'out_for_delivery',
        'delivered', 'failed_delivery', 'returned', 'lost'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 行为类型
DO $$ BEGIN
    CREATE TYPE behavior_type AS ENUM (
        'page_view', 'click', 'add_to_cart', 'remove_from_cart',
        'purchase', 'search', 'review', 'share', 'wishlist_add'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 库存操作类型
DO $$ BEGIN
    CREATE TYPE inventory_action AS ENUM (
        'inbound', 'outbound', 'transfer', 'adjustment', 'return', 'damage'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 营销活动类型
DO $$ BEGIN
    CREATE TYPE campaign_type AS ENUM (
        'flash_sale', 'seasonal_promo', 'new_user', 'loyalty',
        'clearance', 'bundle_deal', 'coupon', 'referral'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 广告平台
DO $$ BEGIN
    CREATE TYPE ad_platform AS ENUM ('google', 'facebook', 'tiktok', 'amazon', 'instagram', 'youtube');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 客服对话状态
DO $$ BEGIN
    CREATE TYPE conversation_status AS ENUM ('active', 'resolved', 'escalated', 'closed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Agent 任务状态
DO $$ BEGIN
    CREATE TYPE agent_task_status AS ENUM ('pending', 'running', 'success', 'failed', 'timeout');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ============================================================
-- 1. 用户信息表 (users)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    user_uuid       UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,

    -- 基本信息
    username        VARCHAR(100) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    full_name       VARCHAR(200),
    avatar_url      VARCHAR(500),

    -- 人口统计信息
    gender          VARCHAR(10),
    birth_date      DATE,
    country         VARCHAR(100),
    city            VARCHAR(100),
    timezone        VARCHAR(50) DEFAULT 'UTC',
    language        VARCHAR(10) DEFAULT 'en',

    -- 账户信息
    status          user_status DEFAULT 'active',
    email_verified  BOOLEAN DEFAULT FALSE,
    phone_verified  BOOLEAN DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 购物偏好（JSON 存储灵活扩展）
    preferences     JSONB DEFAULT '{}',
    -- 示例: {"categories": ["electronics","fashion"],
    --        "price_range": {"min": 10, "max": 500},
    --        "brands": ["Apple","Nike"],
    --        "shopping_frequency": "weekly"}

    -- 会员等级
    membership_level VARCHAR(20) DEFAULT 'normal',  -- normal, silver, gold, platinum
    reward_points    INTEGER DEFAULT 0,

    -- 元数据
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ  -- 软删除
);

-- 索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_country ON users(country);
CREATE INDEX idx_users_preferences ON users USING GIN (preferences);
CREATE INDEX idx_users_created_at ON users(created_at);

COMMENT ON TABLE users IS '用户信息表 - 存储注册用户个人信息、联系方式、账号信息、偏好';
COMMENT ON COLUMN users.preferences IS '用户购物偏好（JSONB）：品类偏好、价格区间、品牌偏好、购物频率';


-- ============================================================
-- 2. 商品信息表 (products)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    product_uuid    UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    sku             VARCHAR(100) NOT NULL UNIQUE,

    -- 基本信息
    name            VARCHAR(500) NOT NULL,
    name_en         VARCHAR(500),
    description     TEXT,
    description_en  TEXT,
    category_id     INTEGER,
    brand           VARCHAR(200),

    -- 价格信息
    base_price      DECIMAL(12,2) NOT NULL,
    sale_price      DECIMAL(12,2),
    currency        VARCHAR(3) DEFAULT 'USD',
    cost_price      DECIMAL(12,2),  -- 成本价

    -- 库存信息
    stock_quantity  INTEGER DEFAULT 0,
    min_stock       INTEGER DEFAULT 10,  -- 最低库存预警
    max_stock       INTEGER DEFAULT 1000,
    is_in_stock     BOOLEAN GENERATED ALWAYS AS (stock_quantity > 0) STORED,

    -- 规格属性
    attributes      JSONB DEFAULT '{}',
    -- 示例: {"color": ["black","white"], "size": ["S","M","L","XL"],
    --        "weight_kg": 0.5, "dimensions": {"l":10,"w":5,"h":2}}

    -- 图片
    main_image_url  VARCHAR(500),
    image_urls      JSONB DEFAULT '[]',  -- 多图片

    -- 评分
    avg_rating      DECIMAL(3,2) DEFAULT 0.00,
    review_count    INTEGER DEFAULT 0,
    sales_count     INTEGER DEFAULT 0,

    -- 市场信息
    target_market   VARCHAR(10) DEFAULT 'GLOBAL',  -- 目标市场国家代码
    hs_code         VARCHAR(20),  -- 海关编码

    -- 状态
    status          VARCHAR(20) DEFAULT 'active',  -- active, inactive, discontinued
    is_featured     BOOLEAN DEFAULT FALSE,

    -- 供应商
    supplier_id     INTEGER,

    -- 元数据
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

-- 索引
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_price ON products(base_price);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_rating ON products(avg_rating DESC);
CREATE INDEX idx_products_attributes ON products USING GIN (attributes);
CREATE INDEX idx_products_target_market ON products(target_market);
CREATE FULLTEXT INDEX idx_products_search ON products(name, description);

COMMENT ON TABLE products IS '商品信息表 - 记录所有商品信息，包括名称、描述、价格、库存、图片';


-- ============================================================
-- 3. 订单信息表 (orders)
-- ============================================================
CREATE TABLE IF NOT EXISTS orders (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    order_number    VARCHAR(50) NOT NULL UNIQUE,  -- 如 ORD-20260713-00001

    -- 用户信息
    user_id         BIGINT NOT NULL REFERENCES users(id),

    -- 订单状态
    status          order_status DEFAULT 'pending',
    payment_status  payment_status DEFAULT 'pending',
    fulfillment_status VARCHAR(20) DEFAULT 'unfulfilled',  -- unfulfilled, partial, fulfilled

    -- 金额信息
    subtotal        DECIMAL(12,2) NOT NULL,
    discount_amount DECIMAL(12,2) DEFAULT 0.00,
    tax_amount      DECIMAL(12,2) DEFAULT 0.00,
    shipping_amount DECIMAL(12,2) DEFAULT 0.00,
    total_amount    DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'USD',

    -- 配送信息
    shipping_address JSONB NOT NULL,
    -- 示例: {"name":"John","phone":"+1234567890",
    --        "country":"US","state":"CA","city":"LA",
    --        "address":"123 Main St","postal_code":"90001"}

    billing_address  JSONB,
    shipping_method  VARCHAR(50),
    tracking_number  VARCHAR(100),

    -- 备注
    customer_note   TEXT,
    internal_note   TEXT,
    cancel_reason   TEXT,

    -- 时间
    ordered_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at         TIMESTAMPTZ,
    shipped_at      TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,
    cancelled_at    TIMESTAMPTZ,

    -- 元数据
    source          VARCHAR(50) DEFAULT 'web',  -- web, app, api
    ip_address      VARCHAR(50),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_ordered_at ON orders(ordered_at DESC);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

COMMENT ON TABLE orders IS '订单信息表 - 存储用户订单信息，包含订单号、商品、金额、配送信息';


-- ============================================================
-- 3a. 订单明细表 (order_items)
-- ============================================================
CREATE TABLE IF NOT EXISTS order_items (
    id              BIGSERIAL PRIMARY KEY,
    order_id        BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id      BIGINT NOT NULL REFERENCES products(id),
    product_name    VARCHAR(500) NOT NULL,  -- 冗余存储，保留历史快照
    product_sku     VARCHAR(100) NOT NULL,
    product_image   VARCHAR(500),

    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(12,2) NOT NULL,
    total_price     DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

COMMENT ON TABLE order_items IS '订单明细表 - 订单中的商品项';


-- ============================================================
-- 4. 支付信息表 (payments)
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    transaction_id  VARCHAR(100) NOT NULL UNIQUE,  -- 第三方交易ID

    -- 关联
    order_id        BIGINT NOT NULL REFERENCES orders(id),
    user_id         BIGINT NOT NULL REFERENCES users(id),

    -- 支付信息
    amount          DECIMAL(12,2) NOT NULL,
    currency        VARCHAR(3) DEFAULT 'USD',
    status          payment_status DEFAULT 'pending',
    method          payment_method,

    -- 支付网关信息
    gateway         VARCHAR(50),  -- stripe, paypal, alipay
    gateway_response JSONB,  -- 网关返回原始数据

    -- 退款信息
    refund_amount   DECIMAL(12,2) DEFAULT 0.00,
    refund_reason   TEXT,
    refunded_at     TIMESTAMPTZ,

    -- 时间
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payments_order ON payments(order_id);
CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_transaction ON payments(transaction_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_created_at ON payments(created_at DESC);

COMMENT ON TABLE payments IS '支付信息表 - 记录支付方式、金额、时间、状态及退款信息';


-- ============================================================
-- 5. 物流信息表 (logistics)
-- ============================================================
CREATE TABLE IF NOT EXISTS logistics (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    order_id        BIGINT NOT NULL REFERENCES orders(id) UNIQUE,
    user_id         BIGINT NOT NULL REFERENCES users(id),

    -- 快递信息
    tracking_number VARCHAR(100) NOT NULL,
    carrier         VARCHAR(100) NOT NULL,  -- DHL, FedEx, UPS, 顺丰
    carrier_code    VARCHAR(20),

    -- 状态
    status          logistics_status DEFAULT 'pending',
    current_location VARCHAR(300),

    -- 地址
    origin_address  JSONB,
    destination_address JSONB,

    -- 时间
    estimated_delivery_date DATE,
    actual_delivery_date    DATE,
    shipped_at      TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,

    -- 费用
    shipping_cost   DECIMAL(12,2),
    insurance_cost  DECIMAL(12,2) DEFAULT 0.00,
    weight_kg       DECIMAL(8,3),

    -- 异常
    has_exception   BOOLEAN DEFAULT FALSE,
    exception_detail JSONB,

    -- 元数据
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_logistics_order ON logistics(order_id);
CREATE INDEX idx_logistics_tracking ON logistics(tracking_number);
CREATE INDEX idx_logistics_carrier ON logistics(carrier);
CREATE INDEX idx_logistics_status ON logistics(status);
CREATE INDEX idx_logistics_estimated_delivery ON logistics(estimated_delivery_date);

COMMENT ON TABLE logistics IS '物流信息表 - 配送地址、快递公司、运单号、物流状态';


-- ============================================================
-- 5a. 物流追踪明细表 (logistics_tracking_details)
-- ============================================================
CREATE TABLE IF NOT EXISTS logistics_tracking_details (
    id              BIGSERIAL PRIMARY KEY,
    logistics_id    BIGINT NOT NULL REFERENCES logistics(id) ON DELETE CASCADE,

    status          VARCHAR(100),
    location        VARCHAR(300),
    description     TEXT,
    event_time      TIMESTAMPTZ NOT NULL,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_logistics_tracking_logistics ON logistics_tracking_details(logistics_id);
CREATE INDEX idx_logistics_tracking_event_time ON logistics_tracking_details(event_time DESC);

COMMENT ON TABLE logistics_tracking_details IS '物流追踪明细表 - 每个物流节点的状态变化';


-- ============================================================
-- 6. 用户行为数据分析表 (user_behaviors)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_behaviors (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id),  -- 可为空（匿名用户）
    session_id      VARCHAR(100) NOT NULL,

    -- 行为类型
    behavior_type   behavior_type NOT NULL,
    page_url        VARCHAR(1000),
    referrer_url    VARCHAR(1000),

    -- 关联商品
    product_id      BIGINT REFERENCES products(id),

    -- 行为数据
    duration_seconds DECIMAL(10,2),  -- 页面停留时长
    scroll_depth    INTEGER,  -- 滚动深度百分比
    interaction_data JSONB,  -- 交互详情
    -- 示例: {"clicks": 5, "hovers": 3, "cart_adds": 1}

    -- 设备信息
    device_type     VARCHAR(20),  -- desktop, mobile, tablet
    browser         VARCHAR(100),
    os              VARCHAR(50),
    country         VARCHAR(100),
    ip_address      VARCHAR(50),

    -- 来源
    utm_source      VARCHAR(100),
    utm_medium      VARCHAR(100),
    utm_campaign    VARCHAR(100),

    -- 时间
    event_time      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 分区表（按月分区，提升查询性能）
-- CREATE TABLE user_behaviors (...) PARTITION BY RANGE (event_time);

CREATE INDEX idx_user_behaviors_user ON user_behaviors(user_id);
CREATE INDEX idx_user_behaviors_session ON user_behaviors(session_id);
CREATE INDEX idx_user_behaviors_type ON user_behaviors(behavior_type);
CREATE INDEX idx_user_behaviors_product ON user_behaviors(product_id);
CREATE INDEX idx_user_behaviors_event_time ON user_behaviors(event_time DESC);
CREATE INDEX idx_user_behaviors_user_time ON user_behaviors(user_id, event_time DESC);

COMMENT ON TABLE user_behaviors IS '用户行为数据分析表 - 浏览、点击、购买等行为数据';


-- ============================================================
-- 7. 库存管理表 (inventory)
-- ============================================================
CREATE TABLE IF NOT EXISTS inventory (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    product_id      BIGINT NOT NULL REFERENCES products(id),
    warehouse_id    INTEGER NOT NULL,
    sku             VARCHAR(100) NOT NULL,

    -- 库存数量
    quantity        INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,  -- 已预留（订单锁定）
    available_quantity INTEGER GENERATED ALWAYS AS
        (quantity - reserved_quantity) STORED,
    safety_stock    INTEGER DEFAULT 10,  -- 安全库存
    reorder_point   INTEGER DEFAULT 20,  -- 补货点

    -- 位置
    warehouse_name  VARCHAR(200),
    location_code   VARCHAR(50),  -- 库位编码
    zone            VARCHAR(50),  -- 区域

    -- 批次
    batch_number    VARCHAR(100),
    production_date DATE,
    expiry_date     DATE,

    -- 成本
    unit_cost       DECIMAL(12,2),
    total_value     DECIMAL(14,2) GENERATED ALWAYS AS
        (quantity * unit_cost) STORED,

    -- 状态
    status          VARCHAR(20) DEFAULT 'active',
    last_counted_at TIMESTAMPTZ,

    -- 元数据
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(product_id, warehouse_id, batch_number)
);

CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_status ON inventory(status);
CREATE INDEX idx_inventory_expiry ON inventory(expiry_date);
CREATE INDEX idx_inventory_quantity ON inventory(available_quantity);

COMMENT ON TABLE inventory IS '库存管理表 - 商品库存、仓储信息、批次管理';


-- ============================================================
-- 7a. 库存流水表 (inventory_transactions)
-- ============================================================
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id              BIGSERIAL PRIMARY KEY,
    inventory_id    BIGINT NOT NULL REFERENCES inventory(id),
    product_id      BIGINT NOT NULL REFERENCES products(id),
    warehouse_id    INTEGER NOT NULL,

    action          inventory_action NOT NULL,
    quantity_change INTEGER NOT NULL,
    quantity_before INTEGER NOT NULL,
    quantity_after  INTEGER NOT NULL,

    reference_type  VARCHAR(50),  -- order, purchase_order, adjustment
    reference_id    VARCHAR(100),
    note            TEXT,

    operator_id     BIGINT,  -- 操作人
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_inventory_trans_product ON inventory_transactions(product_id);
CREATE INDEX idx_inventory_trans_warehouse ON inventory_transactions(warehouse_id);
CREATE INDEX idx_inventory_trans_created ON inventory_transactions(created_at DESC);

COMMENT ON TABLE inventory_transactions IS '库存流水表 - 入库、出库、盘点等操作记录';


-- ============================================================
-- 8. 营销活动表 (marketing_campaigns)
-- ============================================================
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    campaign_code   VARCHAR(100) NOT NULL UNIQUE,
    name            VARCHAR(300) NOT NULL,
    campaign_type   campaign_type NOT NULL,
    description     TEXT,

    -- 时间
    start_date      TIMESTAMPTZ NOT NULL,
    end_date        TIMESTAMPTZ NOT NULL,

    -- 规则
    discount_rules  JSONB NOT NULL,
    -- 示例: {"type":"percentage","value":20,"max_discount":50,
    --        "min_order_amount":100,"applicable_categories":[1,2,3]}

    -- 预算
    total_budget    DECIMAL(12,2),
    used_budget     DECIMAL(12,2) DEFAULT 0.00,

    -- 目标
    target_segments JSONB,  -- 目标用户分群
    target_products JSONB,  -- 目标商品

    -- 状态
    status          VARCHAR(20) DEFAULT 'draft',  -- draft, active, paused, ended
    is_active       BOOLEAN DEFAULT FALSE,

    -- 效果
    total_orders    INTEGER DEFAULT 0,
    total_revenue   DECIMAL(14,2) DEFAULT 0.00,
    total_discount  DECIMAL(14,2) DEFAULT 0.00,
    roi             DECIMAL(8,4) GENERATED ALWAYS AS (
        CASE WHEN used_budget > 0
        THEN (total_revenue - used_budget) / used_budget
        ELSE 0 END
    ) STORED,

    -- 元数据
    created_by      BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_code ON marketing_campaigns(campaign_code);
CREATE INDEX idx_campaigns_type ON marketing_campaigns(campaign_type);
CREATE INDEX idx_campaigns_status ON marketing_campaigns(status);
CREATE INDEX idx_campaigns_dates ON marketing_campaigns(start_date, end_date);
CREATE INDEX idx_campaigns_active ON marketing_campaigns(is_active) WHERE is_active = TRUE;

COMMENT ON TABLE marketing_campaigns IS '营销活动表 - 优惠券、促销活动、折扣信息';


-- ============================================================
-- 8a. 优惠券表 (coupons)
-- ============================================================
CREATE TABLE IF NOT EXISTS coupons (
    id              BIGSERIAL PRIMARY KEY,
    coupon_code     VARCHAR(50) NOT NULL UNIQUE,
    campaign_id     BIGINT REFERENCES marketing_campaigns(id),

    discount_type   VARCHAR(20) NOT NULL,  -- percentage, fixed_amount, free_shipping
    discount_value  DECIMAL(12,2) NOT NULL,
    min_order_amount DECIMAL(12,2) DEFAULT 0.00,
    max_discount    DECIMAL(12,2),

    total_quantity  INTEGER NOT NULL,
    used_quantity   INTEGER DEFAULT 0,
    per_user_limit  INTEGER DEFAULT 1,

    start_date      TIMESTAMPTZ NOT NULL,
    expiry_date     TIMESTAMPTZ NOT NULL,

    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_coupons_code ON coupons(coupon_code);
CREATE INDEX idx_coupons_campaign ON coupons(campaign_id);
CREATE INDEX idx_coupons_expiry ON coupons(expiry_date);

COMMENT ON TABLE coupons IS '优惠券表 - 优惠券码、折扣规则、使用限制';


-- ============================================================
-- 9. 市场数据表 (market_data)
-- ============================================================
CREATE TABLE IF NOT EXISTS market_data (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    data_type       VARCHAR(50) NOT NULL,  -- competitor, trend, ranking, price

    -- 市场信息
    market          VARCHAR(10) NOT NULL,  -- 国家代码
    category        VARCHAR(100),
    keyword         VARCHAR(200),

    -- 数据内容
    data_source     VARCHAR(100),  -- amazon, ebay, shopee, aliexpress
    title           VARCHAR(500),
    data_content    JSONB NOT NULL,
    -- 示例: {"bsr": 1500, "price_range": {"min":19.99,"max":89.99,"avg":45.50},
    --        "monthly_sales": 2500, "competitor_count": 45,
    --        "trend": "rising", "seasonality": "Q4_peak"}

    -- 评分
    relevance_score DECIMAL(5,4),
    confidence_score DECIMAL(5,4),

    -- 时间
    data_date       DATE NOT NULL,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_market_data_type ON market_data(data_type);
CREATE INDEX idx_market_data_market ON market_data(market);
CREATE INDEX idx_market_data_category ON market_data(category);
CREATE INDEX idx_market_data_date ON market_data(data_date DESC);
CREATE INDEX idx_market_data_content ON market_data USING GIN (data_content);

COMMENT ON TABLE market_data IS '市场数据表 - 选品分析所需的竞品和趋势数据';


-- ============================================================
-- 10. 广告计划表 (advertising_plans)
-- ============================================================
CREATE TABLE IF NOT EXISTS advertising_plans (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    plan_code       VARCHAR(100) NOT NULL UNIQUE,
    name            VARCHAR(300) NOT NULL,

    -- 平台
    platform        ad_platform NOT NULL,
    external_campaign_id VARCHAR(100),  -- 外部平台广告活动ID

    -- 预算
    daily_budget    DECIMAL(12,2),
    total_budget    DECIMAL(12,2),
    spent_amount    DECIMAL(12,2) DEFAULT 0.00,

    -- 时间
    start_date      TIMESTAMPTZ NOT NULL,
    end_date        TIMESTAMPTZ NOT NULL,

    -- 定向
    targeting       JSONB,
    -- 示例: {"locations":["US","UK"],"age_range":[18,45],
    --        "interests":["electronics","gadgets"],"languages":["en"]}

    -- 素材
    creatives       JSONB,
    -- 示例: [{"type":"image","url":"...","headline":"...","cta":"Buy Now"}]

    -- 关联商品
    product_ids     JSONB,

    -- 效果指标
    impressions     INTEGER DEFAULT 0,
    clicks          INTEGER DEFAULT 0,
    ctr             DECIMAL(8,4) DEFAULT 0.0000,
    cpc             DECIMAL(10,4) DEFAULT 0.0000,
    conversions     INTEGER DEFAULT 0,
    conversion_rate DECIMAL(8,4) DEFAULT 0.0000,
    revenue         DECIMAL(14,2) DEFAULT 0.00,
    roas            DECIMAL(8,4) DEFAULT 0.0000,  -- Return on Ad Spend

    -- 状态
    status          VARCHAR(20) DEFAULT 'draft',  -- draft, active, paused, completed
    generated_by    VARCHAR(100),  -- 生成来源 Agent

    -- 元数据
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ad_plans_platform ON advertising_plans(platform);
CREATE INDEX idx_ad_plans_status ON advertising_plans(status);
CREATE INDEX idx_ad_plans_dates ON advertising_plans(start_date, end_date);
CREATE INDEX idx_ad_plans_roas ON advertising_plans(roas DESC);

COMMENT ON TABLE advertising_plans IS '广告计划表 - 广告投放Agent输出的广告计划';


-- ============================================================
-- 11. 客服对话表 (customer_service_conversations)
-- ============================================================
CREATE TABLE IF NOT EXISTS customer_service_conversations (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    user_id         BIGINT REFERENCES users(id),

    -- 对话信息
    subject         VARCHAR(300),
    status          conversation_status DEFAULT 'active',
    channel         VARCHAR(20) DEFAULT 'chat',  -- chat, email, phone

    -- 关联订单
    order_id        BIGINT REFERENCES orders(id),

    -- 标签
    intent          VARCHAR(50),  -- faq, order_query, refund, complaint, product_inquiry
    sentiment       VARCHAR(20),  -- positive, neutral, negative
    priority        VARCHAR(10) DEFAULT 'normal',  -- low, normal, high, urgent

    -- 处理信息
    handled_by_agent BOOLEAN DEFAULT TRUE,  -- 是否由Agent处理
    agent_name      VARCHAR(100),  -- 处理Agent名称
    escalated_to_human BOOLEAN DEFAULT FALSE,
    resolution      TEXT,

    -- 时间
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cs_conversations_user ON customer_service_conversations(user_id);
CREATE INDEX idx_cs_conversations_status ON customer_service_conversations(status);
CREATE INDEX idx_cs_conversations_intent ON customer_service_conversations(intent);
CREATE INDEX idx_cs_conversations_order ON customer_service_conversations(order_id);
CREATE INDEX idx_cs_conversations_agent ON customer_service_conversations(agent_name);
CREATE INDEX idx_cs_conversations_started ON customer_service_conversations(started_at DESC);

COMMENT ON TABLE customer_service_conversations IS '客服对话表 - 客服Agent处理的对话记录';


-- ============================================================
-- 11a. 客服消息表 (cs_messages)
-- ============================================================
CREATE TABLE IF NOT EXISTS cs_messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES customer_service_conversations(id) ON DELETE CASCADE,

    role            VARCHAR(20) NOT NULL,  -- user, assistant, system
    content         TEXT NOT NULL,
    message_type    VARCHAR(20) DEFAULT 'text',  -- text, image, faq_card, order_card

    metadata        JSONB,
    token_count     INTEGER,
    response_time_ms INTEGER,  -- 响应时间（毫秒）

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cs_messages_conversation ON cs_messages(conversation_id);
CREATE INDEX idx_cs_messages_created ON cs_messages(created_at);

COMMENT ON TABLE cs_messages IS '客服消息表 - 对话中的每条消息';


-- ============================================================
-- 12. 供应链预测表 (supply_chain_forecasts)
-- ============================================================
CREATE TABLE IF NOT EXISTS supply_chain_forecasts (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    product_id      BIGINT NOT NULL REFERENCES products(id),
    warehouse_id    INTEGER NOT NULL,

    -- 预测数据
    forecast_period_days INTEGER NOT NULL,
    forecast_date   DATE NOT NULL,
    forecast_method VARCHAR(50),  -- moving_average, arima, prophet

    -- 预测值
    predicted_demand INTEGER NOT NULL,
    confidence_lower INTEGER,
    confidence_upper INTEGER,
    confidence_level DECIMAL(5,4) DEFAULT 0.9500,

    -- 实际值（事后对比）
    actual_demand   INTEGER,
    forecast_error  DECIMAL(10,4),  -- MAPE
    forecast_accuracy DECIMAL(8,4),

    -- 库存建议
    recommended_reorder INTEGER,
    recommended_safety_stock INTEGER,
    lead_time_days  INTEGER,

    -- 成本
    estimated_cost  DECIMAL(12,2),
    potential_saving DECIMAL(12,2),

    -- 元数据
    generated_by    VARCHAR(100),  -- 生成Agent
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sc_forecasts_product ON supply_chain_forecasts(product_id);
CREATE INDEX idx_sc_forecasts_date ON supply_chain_forecasts(forecast_date DESC);
CREATE INDEX idx_sc_forecasts_product_date ON supply_chain_forecasts(product_id, forecast_date DESC);

COMMENT ON TABLE supply_chain_forecasts IS '供应链预测表 - 需求预测、库存建议、补货计划';


-- ============================================================
-- 13. Agent 任务日志表 (agent_task_logs)
-- ============================================================
CREATE TABLE IF NOT EXISTS agent_task_logs (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    task_id         UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    session_id      VARCHAR(100),

    -- Agent 信息
    agent_name      VARCHAR(100) NOT NULL,
    agent_role      VARCHAR(50) NOT NULL,
    task_type       VARCHAR(100),

    -- 任务状态
    status          agent_task_status DEFAULT 'pending',
    priority        VARCHAR(10) DEFAULT 'normal',

    -- 输入输出
    input_data      JSONB,
    output_data     JSONB,
    error_message   TEXT,

    -- ReAct 步骤记录
    react_steps     JSONB DEFAULT '[]',
    -- 示例: [{"step":1,"thought":"...","action":"search_competitor",
    --        "observation":"...","duration_ms":1234}]

    -- 工具调用记录
    tool_calls      JSONB DEFAULT '[]',
    -- 示例: [{"tool":"search_competitor_products","args":{...},
    --        "result":{...},"duration_ms":500,"success":true}]

    -- 性能指标
    duration_ms     INTEGER,
    token_usage     JSONB,  -- {"prompt_tokens": 500, "completion_tokens": 300}
    llm_model       VARCHAR(100),
    mcp_calls_count INTEGER DEFAULT 0,

    -- 时间
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 分区表（按月分区）
-- CREATE TABLE agent_task_logs (...) PARTITION BY RANGE (created_at);

CREATE INDEX idx_agent_logs_agent ON agent_task_logs(agent_name);
CREATE INDEX idx_agent_logs_status ON agent_task_logs(status);
CREATE INDEX idx_agent_logs_session ON agent_task_logs(session_id);
CREATE INDEX idx_agent_logs_created ON agent_task_logs(created_at DESC);
CREATE INDEX idx_agent_logs_agent_status ON agent_task_logs(agent_name, status);

COMMENT ON TABLE agent_task_logs IS 'Agent任务日志表 - 记录每个Agent的执行情况，用于监控和调试';
COMMENT ON COLUMN agent_task_logs.react_steps IS 'ReAct步骤记录：Thought → Action → Observation 完整链路';
COMMENT ON COLUMN agent_task_logs.tool_calls IS 'MCP工具调用详情：工具名、参数、结果、耗时';


-- ============================================================
-- 14. 向量知识库表 (knowledge_base)
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    -- 主键
    id              BIGSERIAL PRIMARY KEY,
    doc_uuid        UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    doc_id          VARCHAR(200) NOT NULL UNIQUE,

    -- 内容
    title           VARCHAR(500) NOT NULL,
    content         TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL DEFAULT 0,  -- 分块序号
    chunk_total     INTEGER DEFAULT 1,  -- 总分块数

    -- 分类
    category        VARCHAR(100) NOT NULL,  -- faq, policy, product_manual, shipping, returns
    sub_category    VARCHAR(200),
    tags            JSONB DEFAULT '[]',

    -- 市场
    market          VARCHAR(10) DEFAULT 'GLOBAL',  -- 目标市场
    language        VARCHAR(10) DEFAULT 'en',

    -- 向量（pgvector）
    -- embedding       vector(1536),  -- 需要 pgvector 扩展

    -- 元数据
    source_url      VARCHAR(1000),
    source_type     VARCHAR(50),  -- manual, crawled, imported
    author          VARCHAR(200),
    version         VARCHAR(20) DEFAULT '1.0',

    -- 质量
    review_status   VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected
    quality_score   DECIMAL(5,4),

    -- 使用统计
    search_count    INTEGER DEFAULT 0,
    last_used_at    TIMESTAMPTZ,

    -- 有效期
    valid_from      TIMESTAMPTZ,
    valid_until     TIMESTAMPTZ,

    -- 时间
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_kb_doc_id ON knowledge_base(doc_id);
CREATE INDEX idx_kb_category ON knowledge_base(category);
CREATE INDEX idx_kb_market ON knowledge_base(market);
CREATE INDEX idx_kb_language ON knowledge_base(language);
CREATE INDEX idx_kb_tags ON knowledge_base USING GIN (tags);
CREATE INDEX idx_kb_review_status ON knowledge_base(review_status);
CREATE FULLTEXT INDEX idx_kb_search ON knowledge_base(title, content);

-- 向量索引（需要 pgvector 扩展）
-- CREATE INDEX idx_kb_embedding ON knowledge_base
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

COMMENT ON TABLE knowledge_base IS '向量知识库表 - 存储RAG知识片段（FAQ、政策、产品说明书）';


-- ============================================================
-- 辅助表：供应商表
-- ============================================================
CREATE TABLE IF NOT EXISTS suppliers (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(300) NOT NULL,
    contact_person  VARCHAR(200),
    email           VARCHAR(255),
    phone           VARCHAR(50),
    country         VARCHAR(100),
    address         TEXT,
    rating          DECIMAL(3,2) DEFAULT 0.00,
    lead_time_days  INTEGER,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE suppliers IS '供应商表 - 商品供应商信息';


-- ============================================================
-- 辅助表：仓库表
-- ============================================================
CREATE TABLE IF NOT EXISTS warehouses (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(300) NOT NULL,
    code            VARCHAR(50) NOT NULL UNIQUE,
    country         VARCHAR(100) NOT NULL,
    city            VARCHAR(100),
    address         TEXT,
    capacity        INTEGER,
    status          VARCHAR(20) DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE warehouses IS '仓库表 - 仓储地点信息';


-- ============================================================
-- 外键约束补充
-- ============================================================
ALTER TABLE products ADD CONSTRAINT fk_products_supplier
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id);

ALTER TABLE inventory ADD CONSTRAINT fk_inventory_warehouse
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);

ALTER TABLE supply_chain_forecasts ADD CONSTRAINT fk_sc_forecasts_warehouse
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);

ALTER TABLE inventory_transactions ADD CONSTRAINT fk_inv_trans_warehouse
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id);


-- ============================================================
-- 更新时间触发器
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为所有含 updated_at 的表创建触发器
DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'users', 'products', 'orders', 'payments', 'logistics',
        'inventory', 'marketing_campaigns', 'advertising_plans',
        'customer_service_conversations', 'knowledge_base',
        'suppliers', 'warehouses'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
            tbl, tbl
        );
    END LOOP;
END;
$$;