"""
数据库查询适配器
================
将 MCP 工具调用桥接到真实数据库（SQLite/PostgreSQL）。

支持的查询类型：
  - query_order_details: 订单查询
  - get_user_profile: 用户画像
  - check_stock: 库存检查
  - query_payment_history: 支付历史

数据库连接策略：
  - 优先使用 PostgreSQL（生产环境）
  - 降级到 SQLite 内存数据库（开发/测试环境，无需安装 PostgreSQL）
"""

import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.mcp.adapters.base import (
    ToolAdapter, ToolRequest, ToolResponse, AdapterStatus,
)

logger = logging.getLogger(__name__)


class DatabaseAdapter(ToolAdapter):
    """
    数据库适配器 — 将工具调用转换为 SQL 查询

    实现了从 MCP 工具参数到 SQL 查询的完整映射。
    每个工具名称对应一个 SQL 模板，参数自动绑定防止 SQL 注入。

    使用示例:
        adapter = DatabaseAdapter()
        await adapter.initialize("sqlite+aiosqlite:///")  # SQLite 内存库
        # 或
        await adapter.initialize("postgresql+asyncpg://user:pass@localhost/db")

        request = ToolRequest(
            tool_name="query_order_details",
            agent_name="order_management",
            arguments={"order_id": "ORD-001"},
        )
        response = await adapter.execute(request)
    """

    def __init__(self):
        super().__init__(
            name="database",
            description="数据库查询适配器：将 MCP 工具调用桥接到 SQL 数据库",
        )
        self._engine = None
        self._session_factory = None
        self._initialized = False

    async def initialize(self, database_url: str = None):
        """
        初始化数据库连接

        参数:
            database_url: SQLAlchemy 连接字符串
                - SQLite: "sqlite+aiosqlite:///ecommerce.db"
                - PostgreSQL: "postgresql+asyncpg://user:pass@localhost:5432/db"
        """
        if database_url is None:
            # 默认使用 SQLite 文件数据库（无需安装 PostgreSQL）
            database_url = "sqlite+aiosqlite:///ecommerce.db"

        self._engine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        # 如果是 SQLite，自动创建表结构
        if "sqlite" in database_url:
            await self._create_tables()

        self._initialized = True
        logger.info(f"[DatabaseAdapter] 数据库已连接: {database_url}")

    async def _create_tables(self):
        """为 SQLite 创建示例表结构"""
        async with self._engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    status TEXT DEFAULT 'pending',
                    payment_status TEXT DEFAULT 'unpaid',
                    order_amount REAL DEFAULT 0,
                    currency TEXT DEFAULT 'USD',
                    created_at TEXT,
                    shipping_carrier TEXT,
                    shipping_tracking TEXT,
                    shipping_location TEXT,
                    shipping_estimated TEXT
                )
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    preferences TEXT,
                    member_level TEXT DEFAULT '普通会员'
                )
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS inventory (
                    product_id TEXT,
                    warehouse_id TEXT,
                    quantity INTEGER DEFAULT 0,
                    status TEXT DEFAULT '充足',
                    PRIMARY KEY (product_id, warehouse_id)
                )
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS payments (
                    transaction_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    amount REAL,
                    status TEXT,
                    date TEXT
                )
            """))
            # 插入示例数据
            await self._seed_data(conn)
            logger.info("[DatabaseAdapter] SQLite 表结构已创建，示例数据已插入")

    async def _seed_data(self, conn):
        """插入示例数据"""
        # 先检查是否已有数据
        result = await conn.execute(text("SELECT COUNT(*) FROM orders"))
        count = result.scalar()
        if count > 0:
            return

        await conn.execute(text("""
            INSERT INTO orders VALUES
            ('ORD-20260701-00001', 'U001', '已发货', '已支付', 159.99, 'USD',
             '2026-07-01', 'FedEx', 'TRK-US-12345', '洛杉矶转运中心', '2026-07-20'),
            ('ORD-20260705-00002', 'U002', '处理中', '已支付', 79.99, 'USD',
             '2026-07-05', 'DHL', 'TRK-US-67890', '深圳海关', '2026-07-22'),
            ('ORD-20260710-00003', 'U001', '待发货', '已支付', 299.99, 'USD',
             '2026-07-10', 'UPS', 'TRK-US-11111', '深圳主仓', '2026-07-25')
        """))
        await conn.execute(text("""
            INSERT INTO users VALUES
            ('U001', '张三', 'zhangsan@example.com', '["电子产品","运动户外"]', '金牌会员'),
            ('U002', '李四', 'lisi@example.com', '["美妆","服饰"]', '银牌会员')
        """))
        await conn.execute(text("""
            INSERT INTO inventory VALUES
            ('P001', 'WH-001', 500, '充足'),
            ('P001', 'WH-002', 200, '充足'),
            ('P002', 'WH-001', 50, '紧张'),
            ('P005', 'WH-001', 300, '充足')
        """))
        await conn.execute(text("""
            INSERT INTO payments VALUES
            ('TXN-001', 'U001', 159.99, 'success', '2026-07-01'),
            ('TXN-002', 'U001', 79.99, 'success', '2026-06-15'),
            ('TXN-003', 'U002', 79.99, 'success', '2026-07-05')
        """))

    # ---- ToolAdapter 抽象方法实现 ----

    def _validate(self, arguments: Dict[str, Any]) -> None:
        """参数校验"""
        if not self._initialized:
            raise ValueError("数据库适配器未初始化，请先调用 initialize()")

    async def _call_service(self, request: ToolRequest) -> Any:
        """执行数据库查询"""
        # 工具名 → SQL 查询映射
        query_map = {
            "query_order_details": (
                "SELECT * FROM orders WHERE order_id = :order_id",
                {"order_id": request.arguments.get("order_id", "")},
            ),
            "get_user_profile": (
                "SELECT * FROM users WHERE user_id = :user_id",
                {"user_id": request.arguments.get("user_id", "")},
            ),
            "check_stock": (
                "SELECT * FROM inventory WHERE product_id IN :product_ids",
                {"product_ids": tuple(request.arguments.get("product_ids", ["P001"]))},
            ),
            "query_payment_history": (
                "SELECT * FROM payments WHERE user_id = :user_id ORDER BY date DESC",
                {"user_id": request.arguments.get("user_id", "")},
            ),
        }

        sql_template, params = query_map.get(
            request.tool_name,
            ("SELECT 1", {})
        )

        async with self._session_factory() as session:
            result = await session.execute(text(sql_template), params)
            rows = result.fetchall()

            if not rows:
                return {"found": False, "message": "未找到匹配记录"}

            # 将 SQLAlchemy Row 转为 dict 列表
            columns = result.keys()
            records = [dict(zip(columns, row)) for row in rows]

            # 单条查询返回 dict（含嵌套字段），多条查询返回 list
            if request.tool_name in ("query_order_details", "get_user_profile"):
                record = records[0] if records else {"found": False}
                # 如果是订单查询，展开 shipping_* 字段为嵌套 dict，方便 observe 解析
                if request.tool_name == "query_order_details" and isinstance(record, dict):
                    record = self._expand_order_fields(record)
                return record
            return records

    def _expand_order_fields(self, record: dict) -> dict:
        """将扁平的 shipping_* / payment_* 字段展开为嵌套结构"""
        shipping_fields = {
            "carrier": record.pop("shipping_carrier", ""),
            "tracking_number": record.pop("shipping_tracking", ""),
            "current_location": record.pop("shipping_location", ""),
            "estimated_delivery": record.pop("shipping_estimated", ""),
        }
        if any(shipping_fields.values()):
            record["shipping_info"] = shipping_fields
        return record

    def _transform_response(self, raw_result: Any, request: ToolRequest) -> ToolResponse:
        """将数据库查询结果转换为标准 ToolResponse"""
        if isinstance(raw_result, dict) and raw_result.get("found") is False:
            return ToolResponse(
                status=AdapterStatus.SUCCESS,
                data=raw_result,
                metadata={"rows": 0},
            )

        row_count = len(raw_result) if isinstance(raw_result, list) else 1
        return ToolResponse(
            status=AdapterStatus.SUCCESS,
            data=raw_result,
            metadata={"rows": row_count, "source": "database"},
        )

    async def close(self):
        """关闭数据库连接"""
        if self._engine:
            await self._engine.dispose()
            logger.info("[DatabaseAdapter] 数据库连接已关闭")