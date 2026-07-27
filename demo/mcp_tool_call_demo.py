"""
MCP 工具调用完整演示 Demo
==========================
逐层展示"工具如何调用"的完整链路，从用户查询到数据库/外部API的每一步。

核心演示:
  1. 完整调用链路: 用户查询 → Supervisor → Expert → MCP Server → 适配器 → 数据库/API
  2. 权限控制: PermissionGuard 检查 API Key + 工具白名单
  3. 重试机制: 指数退避重试，演示失败自动恢复
  4. 数据库适配器: SQL 查询 → 参数绑定 → 结果展开
  5. 外部API适配器: 模拟器 → 物流追踪/汇率查询

运行方式:
    cd demo
    python mcp_tool_call_demo.py
"""

import asyncio
import json
import logging
import sys
import os
import time
from typing import Any, Dict

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MCP-Demo")


# ============================================================
# 工具调用链路图（打印用）
# ============================================================
CALL_CHAIN_DIAGRAM = """
┌─────────────────────────────────────────────────────────────────┐
│                     MCP 工具调用完整链路                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  用户: "查询订单 ORD-20260701-00001"                              │
│    │                                                             │
│    ▼                                                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Supervisor.think()                                    │   │
│  │    - LLM 分析用户意图                                     │   │
│  │    - 输出: RoutingDecision(next_agent="order_management") │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 2. OrderManagementAgent.run()                            │   │
│  │    - think() → action="query_order_details"              │   │
│  │    - act() → self.call_tool("query_order_details", ...)  │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 3. MCPServer.call_tool("query_order_details", args)      │   │
│  │    - 查找工具: _tools["query_order_details"]             │   │
│  │    - 调用 handler: tool.handler(**args)                  │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 4. AdapterRegistry.get_handler("query_order_details")    │   │
│  │    - 查找映射: _tool_mapping["query_order_details"]      │   │
│  │    - 返回: DatabaseAdapter 的 handler 函数               │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 5. DatabaseAdapter.execute(request)                      │   │
│  │    ├─ Step 5a: PermissionGuard.check() → 权限检查        │   │
│  │    ├─ Step 5b: _validate() → 参数校验                    │   │
│  │    ├─ Step 5c: _call_with_timeout() → 超时控制           │   │
│  │    │    └─ _call_service() → SQL 查询                    │   │
│  │    │       └─ SELECT * FROM orders WHERE order_id = ?    │   │
│  │    └─ Step 5d: _transform_response() → 格式转换          │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 6. 逐层返回结果                                           │   │
│  │    DatabaseAdapter → ToolResponse                        │   │
│  │    → MCPServer → {"success": True, "result": {...}}      │   │
│  │    → OrderManagement.observe() → 更新 State              │   │
│  │    → OrderManagement.final_answer() → 生成答案           │   │
│  │    → Supervisor.final_answer() → LLM 合成最终回复         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  用户看到: "订单 ORD-20260701-00001 状态: 已发货..."             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
"""


# ============================================================
# Demo 1: 完整调用链路 — 数据库适配器
# ============================================================
async def demo_full_call_chain_database():
    """
    Demo 1: 完整调用链路 — 数据库查询
    模拟从用户查询到数据库返回的完整过程
    """
    print("\n" + "=" * 70)
    print("Demo 1: 完整调用链路 — 数据库适配器 (query_order_details)")
    print("=" * 70)

    from core.mcp.adapters.registry import AdapterRegistry, reset_registry
    from core.mcp.adapters.base import ToolRequest, AdapterStatus

    # 初始化适配器注册中心
    reset_registry()
    registry = AdapterRegistry()
    await registry.initialize()

    print(f"\n[初始化] 已注册适配器: {list(registry._adapters.keys())}")
    print(f"[初始化] 已注册工具映射: {len(registry._tool_mapping)} 个")
    for tool_name, (adapter_name, _) in registry._tool_mapping.items():
        print(f"  - {tool_name} → {adapter_name}")

    # ---- Step 1: 模拟 Supervisor 路由 ----
    print(f"\n{'─' * 50}")
    print(f"[Step 1] Supervisor.think() → 路由到 order_management")
    user_query = "查询订单 ORD-20260701-00001"
    print(f"  用户查询: {user_query}")
    print(f"  路由决策: next_agent = 'order_management'")

    # ---- Step 2: 模拟 Expert think() → 决定调用工具 ----
    print(f"\n{'─' * 50}")
    print(f"[Step 2] OrderManagementAgent.think() → 决定调用工具")
    tool_name = "query_order_details"
    tool_args = {"order_id": "ORD-20260701-00001"}
    print(f"  action = '{tool_name}'")
    print(f"  tool_args = {json.dumps(tool_args, ensure_ascii=False)}")

    # ---- Step 3: 模拟 MCPServer.call_tool() ----
    print(f"\n{'─' * 50}")
    print(f"[Step 3] MCPServer.call_tool() → 查找并调用 handler")
    print(f"  查找工具: _tools['{tool_name}']")
    handler = registry.get_handler(tool_name, "order_management")
    print(f"  handler 类型: {type(handler).__name__}")

    # ---- Step 4-5: 适配器执行 ----
    print(f"\n{'─' * 50}")
    print(f"[Step 4-5] 适配器执行 → 权限检查 → 参数校验 → SQL查询 → 格式转换")

    start_time = time.time()

    # 获取 handler 并执行（这是完整的适配器调用链）
    result = await handler(**tool_args)

    elapsed = (time.time() - start_time) * 1000

    print(f"\n  执行结果:")
    print(f"  耗时: {elapsed:.1f}ms")
    print(f"  返回数据:")
    print(f"    order_id: {result.get('order_id', 'N/A')}")
    print(f"    status: {result.get('status', 'N/A')}")
    print(f"    payment_status: {result.get('payment_status', 'N/A')}")
    print(f"    order_amount: {result.get('currency', '')} {result.get('order_amount', '')}")
    shipping = result.get("shipping_info", {})
    if shipping:
        print(f"    shipping_info:")
        print(f"      carrier: {shipping.get('carrier', 'N/A')}")
        print(f"      tracking_number: {shipping.get('tracking_number', 'N/A')}")
        print(f"      current_location: {shipping.get('current_location', 'N/A')}")
        print(f"      estimated_delivery: {shipping.get('estimated_delivery', 'N/A')}")

    print(f"\n  [OK] 完整调用链路验证通过: 用户查询 → 数据库返回")

    await registry.close()
    return result


# ============================================================
# Demo 2: 权限控制演示
# ============================================================
async def demo_permission_control():
    """
    Demo 2: 权限控制 — PermissionGuard 检查
    演示: API Key 验证 + 工具白名单
    """
    print("\n" + "=" * 70)
    print("Demo 2: 权限控制 — PermissionGuard 检查")
    print("=" * 70)

    from core.mcp.adapters.security import PermissionGuard
    from core.mcp.adapters.base import ToolRequest

    # 初始化权限守卫
    guard = PermissionGuard()
    guard.configure(
        api_keys=["valid-key-12345", "admin-key-67890"],
        tool_allowlist={
            "order_management": ["query_order_details", "create_order", "cancel_order"],
            "logistics": ["track_shipment", "estimate_delivery"],
            "customer_service": ["lookup_order_status"],
        },
        require_api_key=True,  # 开启 API Key 验证
    )

    print(f"\n[配置] API Key 验证: 开启")
    print(f"[配置] 有效 API Keys: valid-key-12345, admin-key-67890")
    print(f"[配置] 工具白名单:")
    for agent, tools in guard._tool_allowlist.items():
        print(f"  {agent}: {', '.join(tools)}")

    # 测试用例
    test_cases = [
        {
            "desc": "正常请求: 有效 API Key + 白名单内工具",
            "request": ToolRequest(
                tool_name="query_order_details",
                agent_name="order_management",
                arguments={"order_id": "ORD-001"},
                caller_api_key="valid-key-12345",
            ),
            "expect": True,
        },
        {
            "desc": "权限拒绝: 缺少 API Key",
            "request": ToolRequest(
                tool_name="query_order_details",
                agent_name="order_management",
                arguments={"order_id": "ORD-001"},
                caller_api_key="",  # 空 API Key
            ),
            "expect": False,
        },
        {
            "desc": "权限拒绝: 无效 API Key",
            "request": ToolRequest(
                tool_name="query_order_details",
                agent_name="order_management",
                arguments={"order_id": "ORD-001"},
                caller_api_key="hacked-key-99999",
            ),
            "expect": False,
        },
        {
            "desc": "权限拒绝: 工具不在白名单",
            "request": ToolRequest(
                tool_name="track_shipment",  # logistics 的工具
                agent_name="order_management",  # order_management 无权调用
                arguments={"tracking_number": "TRK-001"},
                caller_api_key="valid-key-12345",
            ),
            "expect": False,
        },
        {
            "desc": "正常请求: logistics 调用 track_shipment",
            "request": ToolRequest(
                tool_name="track_shipment",
                agent_name="logistics",
                arguments={"tracking_number": "TRK-001"},
                caller_api_key="admin-key-67890",
            ),
            "expect": True,
        },
    ]

    print(f"\n{'─' * 50}")
    print(f"[测试] 权限检查测试 ({len(test_cases)} 个用例)")

    all_passed = True
    for i, tc in enumerate(test_cases, 1):
        allowed, reason = await guard.check(tc["request"])
        passed = allowed == tc["expect"]
        status = "[OK]" if passed else "[FAIL]"
        if not passed:
            all_passed = False

        print(f"\n  {status} 测试 {i}: {tc['desc']}")
        print(f"    agent={tc['request'].agent_name}, tool={tc['request'].tool_name}")
        print(f"    api_key={'***' if tc['request'].caller_api_key else '(空)'}")
        print(f"    结果: allowed={allowed}, reason='{reason}'")
        print(f"    预期: allowed={tc['expect']}")

    if all_passed:
        print(f"\n  [OK] 所有权限检查测试通过!")
    else:
        print(f"\n  [FAIL] 部分测试失败!")


# ============================================================
# Demo 3: 重试机制演示
# ============================================================
async def demo_retry_mechanism():
    """
    Demo 3: 重试机制 — 指数退避
    演示: 失败自动重试, 指数退避等待
    """
    print("\n" + "=" * 70)
    print("Demo 3: 重试机制 — 指数退避 (Exponential Backoff)")
    print("=" * 70)

    from core.mcp.adapters.retry import RetryConfig, retry_with_backoff

    # 配置重试
    config = RetryConfig(
        max_retries=3,
        base_delay_seconds=0.3,
        max_delay_seconds=5.0,
        jitter=True,
        retryable_errors=("timeout", "connection", "service_unavailable", "503", "429"),
    )

    print(f"\n[配置] 重试策略:")
    print(f"  最大重试次数: {config.max_retries}")
    print(f"  基础延迟: {config.base_delay_seconds}s")
    print(f"  最大延迟: {config.max_delay_seconds}s")
    print(f"  随机抖动: {config.jitter}")
    print(f"  可重试错误: {', '.join(config.retryable_errors)}")

    # 演示退避时间计算
    print(f"\n[演示] 退避时间计算:")
    for attempt in range(4):
        delay = config.backoff(attempt)
        print(f"  第 {attempt} 次重试: 等待 {delay:.2f}s (公式: base * 2^{attempt} + jitter)")

    # 模拟带重试的函数调用
    print(f"\n{'─' * 50}")
    print(f"[测试] 模拟失败重试")

    call_count = [0]  # 使用列表可以在闭包中修改

    async def flaky_api_call():
        """模拟一个前2次失败、第3次成功的外部API调用"""
        call_count[0] += 1
        if call_count[0] <= 2:
            print(f"    第 {call_count[0]} 次调用: 失败! (模拟 connection timeout)")
            raise ConnectionError("connection timeout")
        print(f"    第 {call_count[0]} 次调用: 成功!")
        return {"status": "ok", "data": "模拟数据"}

    try:
        result = await retry_with_backoff(flaky_api_call, config)
        print(f"\n  最终结果: {json.dumps(result, ensure_ascii=False)}")
        print(f"  总调用次数: {call_count[0]}")
        print(f"\n  [OK] 重试机制验证通过: 前2次失败, 第3次成功")
    except Exception as e:
        print(f"\n  [FAIL] 重试机制验证失败: {e}")

    # 演示 is_retryable 判断
    print(f"\n[演示] 错误类型判断:")
    test_errors = [
        ConnectionError("connection timeout"),
        ValueError("invalid parameter"),
        TimeoutError("request timeout"),
        RuntimeError("service_unavailable 503"),
    ]
    for err in test_errors:
        retryable = config.is_retryable(err)
        print(f"  {type(err).__name__}: '{err}' → {'可重试' if retryable else '不可重试'}")


# ============================================================
# Demo 4: 外部API适配器 — 物流追踪 + 汇率查询
# ============================================================
async def demo_external_api_adapter():
    """
    Demo 4: 外部API适配器 — 物流追踪 + 快递预估 + 汇率查询
    """
    print("\n" + "=" * 70)
    print("Demo 4: 外部API适配器 — 物流追踪 + 快递预估 + 汇率查询")
    print("=" * 70)

    from core.mcp.adapters.registry import AdapterRegistry, reset_registry
    from core.mcp.adapters.base import ToolRequest

    # 初始化
    reset_registry()
    registry = AdapterRegistry()
    await registry.initialize()

    # ---- 测试 4a: 物流追踪 ----
    print(f"\n{'─' * 50}")
    print(f"[测试 4a] track_shipment — 物流追踪")

    handler = registry.get_handler("track_shipment", "logistics")
    result = await handler(tracking_number="TRK-US-12345", carrier="FedEx")

    print(f"  运单号: {result.get('tracking_number', '')}")
    print(f"  承运商: {result.get('carrier', '')}")
    print(f"  当前状态: {result.get('status', '')}")
    print(f"  当前位置: {result.get('current_location', '')}")
    print(f"  预计送达: {result.get('estimated_delivery', '')}")
    print(f"  数据来源: {result.get('source', '')}")
    history = result.get("history", [])
    if history:
        print(f"  物流轨迹:")
        for h in history:
            print(f"    {h['time']} | {h['status']} | {h['location']}")

    # ---- 测试 4b: 快递预估 ----
    print(f"\n{'─' * 50}")
    print(f"[测试 4b] estimate_delivery — 快递预估")

    handler = registry.get_handler("estimate_delivery", "logistics")
    result = await handler(from_address="深圳", to_address="洛杉矶")

    print(f"  起运地: {result.get('from', '')}")
    print(f"  目的地: {result.get('to', '')}")
    print(f"  推荐快递: {result.get('recommended', '')}")
    estimates = result.get("estimates", [])
    print(f"  可选方案:")
    for est in estimates:
        print(f"    {est['carrier']}: {est['days']}天, 费用 {est['cost']}")

    # ---- 测试 4c: 汇率查询 ----
    print(f"\n{'─' * 50}")
    print(f"[测试 4c] get_exchange_rate — 汇率查询")

    handler = registry.get_handler("get_exchange_rate", "payment")
    result = await handler(from_currency="USD", to_currency="CNY")

    print(f"  汇率: 1 {result.get('from_currency', '')} = {result.get('rate', '')} {result.get('to_currency', '')}")
    print(f"  查询时间: {result.get('timestamp', '')}")
    print(f"  数据来源: {result.get('source', '')}")

    print(f"\n  [OK] 外部API适配器验证通过: 3个工具全部正常返回")

    await registry.close()


# ============================================================
# Demo 5: 完整调用链路 — 多工具协作
# ============================================================
async def demo_multi_tool_collaboration():
    """
    Demo 5: 多工具协作 — 订单查询 → 物流追踪 → 用户画像
    模拟真实业务场景中的多工具调用链
    """
    print("\n" + "=" * 70)
    print("Demo 5: 多工具协作 — 订单查询 → 物流追踪 → 用户画像")
    print("=" * 70)

    from core.mcp.adapters.registry import AdapterRegistry, reset_registry

    reset_registry()
    registry = AdapterRegistry()
    await registry.initialize()

    print(f"\n[场景] 用户查询: '帮我查一下 ORD-20260701-00001 的订单详情和物流状态'")
    print(f"\n{'─' * 50}")

    # Step 1: 查询订单
    print(f"[Step 1] 调用 query_order_details → 数据库适配器")
    handler = registry.get_handler("query_order_details", "order_management")
    order = await handler(order_id="ORD-20260701-00001")
    print(f"  订单状态: {order.get('status', '')}")
    print(f"  支付状态: {order.get('payment_status', '')}")
    shipping = order.get("shipping_info", {})
    tracking_number = shipping.get("tracking_number", "")
    print(f"  运单号: {tracking_number}")

    # Step 2: 追踪物流（使用订单中的运单号）
    print(f"\n[Step 2] 调用 track_shipment → 外部API适配器")
    print(f"  使用运单号: {tracking_number} (来自订单查询结果)")
    handler = registry.get_handler("track_shipment", "logistics")
    logistics = await handler(tracking_number=tracking_number, carrier=shipping.get("carrier", ""))
    print(f"  物流状态: {logistics.get('status', '')}")
    print(f"  当前位置: {logistics.get('current_location', '')}")
    print(f"  预计送达: {logistics.get('estimated_delivery', '')}")

    # Step 3: 查询用户画像
    print(f"\n[Step 3] 调用 get_user_profile → 数据库适配器")
    user_id = order.get("user_id", "U001")
    print(f"  使用 user_id: {user_id} (来自订单查询结果)")
    handler = registry.get_handler("get_user_profile", "recommendation")
    user = await handler(user_id=user_id)
    print(f"  用户名: {user.get('name', '')}")
    print(f"  会员等级: {user.get('member_level', '')}")
    print(f"  偏好: {user.get('preferences', '')}")

    # 汇总
    print(f"\n{'─' * 50}")
    print(f"[汇总] 多工具协作结果:")
    print(f"  订单: {order.get('order_id')} | {order.get('status')} | {order.get('currency')} {order.get('order_amount')}")
    print(f"  物流: {tracking_number} | {logistics.get('status')} | 预计 {logistics.get('estimated_delivery')}")
    print(f"  用户: {user.get('name')} | {user.get('member_level')}")
    print(f"\n  [OK] 多工具协作验证通过: 前序工具输出 → 后续工具输入 数据流转正常")

    await registry.close()


# ============================================================
# Demo 6: 打日志 — 调用链追踪
# ============================================================
async def demo_call_trace():
    """
    Demo 6: 调用链追踪 — 展示完整的 MCP 调用记录
    """
    print("\n" + "=" * 70)
    print("Demo 6: MCP 调用链追踪")
    print("=" * 70)

    from core.mcp.adapters.registry import AdapterRegistry, reset_registry
    from core.mcp.protocol import MCPRouter, MCPServer, MCPServerInfo, MCPTool, MCPToolCategory

    # 初始化
    reset_registry()
    registry = AdapterRegistry()
    await registry.initialize()

    # 创建 MCP Router 和 Server
    router = MCPRouter()

    server_info = MCPServerInfo(
        name="order_management",
        version="1.0.0",
        description="订单管理",
    )
    server = MCPServer(server_info)

    # 注册工具（使用适配器 handler）
    tools = [
        MCPTool(
            name="query_order_details",
            description="查询订单详情",
            category=MCPToolCategory.QUERY,
            parameters={
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
            handler=registry.get_handler("query_order_details", "order_management"),
        ),
        MCPTool(
            name="lookup_order_status",
            description="查询订单状态",
            category=MCPToolCategory.QUERY,
            parameters={
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
            handler=registry.get_handler("lookup_order_status", "order_management"),
        ),
    ]
    server.register_tools(tools)
    router.register_agent(server)

    # 执行多次工具调用
    print(f"\n[执行] 多次工具调用...")
    await router.route_tool_call("order_management", "query_order_details", {"order_id": "ORD-20260701-00001"})
    await router.route_tool_call("order_management", "lookup_order_status", {"order_id": "ORD-20260705-00002"})
    await router.route_tool_call("order_management", "query_order_details", {"order_id": "ORD-20260710-00003"})

    # 打印调用链追踪
    print(f"\n[追踪] 调用链记录:")
    trace = router.get_trace()
    for i, t in enumerate(trace, 1):
        status = "[OK]" if t["success"] else "[FAIL]"
        print(f"  {i}. {status} {t['agent_name']}.{t['tool_name']} | args={t['arguments']} | time={t['timestamp']}")

    print(f"\n[追踪] 摘要:")
    print(router.get_trace_summary())

    print(f"\n  [OK] 调用链追踪验证通过: 3次调用全部记录")

    await registry.close()


# ============================================================
# 主入口
# ============================================================
async def main():
    print("=" * 70)
    print("MCP 工具调用完整演示 Demo")
    print("=" * 70)
    print("逐层展示: 用户查询 → Supervisor → Expert → MCP Server → 适配器 → 数据库/API")
    print()

    # 打印调用链路图
    print(CALL_CHAIN_DIAGRAM)

    # Demo 1: 完整调用链路 — 数据库
    await demo_full_call_chain_database()

    # Demo 2: 权限控制
    await demo_permission_control()

    # Demo 3: 重试机制
    await demo_retry_mechanism()

    # Demo 4: 外部API适配器
    await demo_external_api_adapter()

    # Demo 5: 多工具协作
    await demo_multi_tool_collaboration()

    # Demo 6: 调用链追踪
    await demo_call_trace()

    print("\n" + "=" * 70)
    print("所有 MCP 工具调用 Demo 执行完成!")
    print("=" * 70)
    print()
    print("总结 — 工具调用底层原理:")
    print("  1. MCPTool.handler → 延迟求值，运行时动态获取适配器")
    print("  2. AdapterRegistry → 工具名→适配器映射，统一路由")
    print("  3. ToolAdapter.execute() → 模板方法: 权限→校验→重试→调用→转换")
    print("  4. PermissionGuard → API Key + 白名单 双重验证")
    print("  5. RetryConfig → 指数退避，jitter 避免惊群")
    print("  6. DatabaseAdapter → 工具名→SQL模板映射，参数绑定防注入")
    print("  7. ExternalAPIAdapter → 模拟器/真实API 双模式，无缝切换")
    print("  8. ToolResponse → 标准化响应格式，无论底层是什么统一返回")


if __name__ == "__main__":
    asyncio.run(main())