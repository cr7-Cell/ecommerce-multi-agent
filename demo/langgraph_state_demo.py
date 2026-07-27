"""
LangGraph StateGraph 编译与执行 Demo
=====================================
演示 LangGraph 核心能力：
1. StateGraph 编译执行（TypedDict State + 节点 + 条件边）
2. 状态持久化（MemorySaver checkpoint）
3. 断点恢复（interrupt_before + 人工审批）

基于项目实际的 Supervisor-Expert 协作模式简化实现。

运行方式:
    cd demo
    python langgraph_state_demo.py
"""

import asyncio
import json
import logging
import sys
import os
from typing import Annotated, Any, Dict, List, Literal, TypedDict
from operator import add

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Demo")


# ============================================================
# 1. 定义 State（TypedDict + Annotated reducer）
# ============================================================
def merge_expert_outputs(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """合并 expert_outputs — 累积而非替换"""
    merged = dict(left)
    merged.update(right)
    return merged


class DemoState(TypedDict):
    """Demo 状态定义 — 简化版 Supervisor-Expert 协作状态"""
    user_query: str                         # 用户查询
    next_agent: str                         # 下一个要执行的 Agent
    expert_outputs: Annotated[Dict[str, Any], merge_expert_outputs]  # Expert 输出累积（使用 reducer 合并）
    final_answer: str                       # 最终答案
    iteration_count: int                    # 迭代计数
    # 用于断点恢复的审批状态
    approval_status: str                    # pending / approved / rejected
    human_feedback: str                     # 人工反馈


# ============================================================
# 2. 节点函数
# ============================================================
def supervisor_node(state: DemoState) -> Dict[str, Any]:
    """
    Supervisor 节点 — 路由决策
    模拟 LLM 分析用户查询，决定调用哪个 Expert
    """
    query = state.get("user_query", "")
    iteration = state.get("iteration_count", 0)
    expert_outputs = state.get("expert_outputs", {})

    logger.info(f"[Supervisor] 迭代 {iteration}: 分析查询 '{query}'")

    # 模拟路由逻辑
    if "订单" in query and "order_management" not in expert_outputs:
        next_agent = "order_management"
        reasoning = "查询订单信息"
    elif ("物流" in query or "配送" in query) and "logistics" not in expert_outputs:
        next_agent = "logistics"
        reasoning = "追踪物流状态"
    elif expert_outputs:
        next_agent = "FINISH"
        reasoning = "所有 Expert 已完成"
    else:
        next_agent = "FINISH"
        reasoning = "无需调用 Expert"

    return {
        "next_agent": next_agent,
        "iteration_count": iteration + 1,
    }


def order_management_node(state: DemoState) -> Dict[str, Any]:
    """订单管理 Expert 节点 — 模拟查询订单"""
    logger.info("[OrderManagement] 查询订单...")

    order_data = {
        "order_id": "ORD-20260701-00001",
        "status": "已发货",
        "payment_status": "已支付",
        "order_amount": 159.99,
        "currency": "USD",
        "carrier": "FedEx",
        "tracking_number": "TRK-US-12345",
        "estimated_delivery": "2026-07-20",
        "current_location": "洛杉矶转运中心",
    }

    return {
        "expert_outputs": {"order_management": order_data},
        "next_agent": "supervisor",  # 返回 Supervisor 继续决策
    }


def logistics_node(state: DemoState) -> Dict[str, Any]:
    """物流追踪 Expert 节点 — 模拟物流查询"""
    logger.info("[Logistics] 追踪物流...")

    # 从前序 Expert 输出中提取信息
    order_output = state.get("expert_outputs", {}).get("order_management", {})
    tracking_number = order_output.get("tracking_number", "N/A")

    logistics_data = {
        "tracking_number": tracking_number,
        "status": "运输中",
        "current_location": "洛杉矶转运中心",
        "estimated_delivery": "2026-07-20",
        "history": [
            {"time": "2026-07-10 08:00", "status": "已揽收", "location": "深圳"},
            {"time": "2026-07-12 06:00", "status": "清关完成", "location": "深圳海关"},
            {"time": "2026-07-14 10:00", "status": "抵达目的国", "location": "洛杉矶"},
        ],
    }

    return {
        "expert_outputs": {"logistics": logistics_data},
        "next_agent": "supervisor",
    }


def aggregate_node(state: DemoState) -> Dict[str, Any]:
    """聚合节点 — 整合所有 Expert 输出，生成最终答案"""
    logger.info("[Aggregate] 生成最终答案...")

    expert_outputs = state.get("expert_outputs", {})
    order = expert_outputs.get("order_management", {})
    logistics = expert_outputs.get("logistics", {})

    parts = []
    if order:
        parts.append(
            f"订单 {order.get('order_id', '')} 状态: {order.get('status', '')}, "
            f"金额: {order.get('currency', '')} {order.get('order_amount', '')}"
        )
    if logistics:
        parts.append(
            f"物流: {logistics.get('carrier', order.get('carrier', ''))} "
            f"运单号 {logistics.get('tracking_number', '')}, "
            f"状态: {logistics.get('status', '')}, "
            f"预计送达: {logistics.get('estimated_delivery', '')}"
        )

    final_answer = "；".join(parts) if parts else "查询完成"

    return {
        "final_answer": final_answer,
        "next_agent": "FINISH",
    }


# ============================================================
# 3. 路由函数
# ============================================================
def route_after_supervisor(state: DemoState) -> Literal["order_management", "logistics", "aggregate"]:
    """Supervisor 节点后的条件路由"""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH":
        return "aggregate"
    return next_agent


def route_after_expert(state: DemoState) -> Literal["supervisor", "aggregate"]:
    """Expert 节点后的条件路由"""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "FINISH":
        return "aggregate"
    return "supervisor"


# ============================================================
# 4. 构建 StateGraph（核心 — 编译执行）
# ============================================================
def build_graph() -> StateGraph:
    """
    构建 StateGraph

    ┌─────────────┐
    │  __start__  │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Supervisor │ ← 路由决策
    └──────┬──────┘
           │
    ┌──────┼──────────┐
    │      │           │
    ▼      ▼           ▼
  Order  Logistics  Aggregate
  Mgmt               (聚合)
    │      │           │
    └──────┴───────────┘
           │
    ┌──────▼──────┐
    │   __end__   │
    └─────────────┘
    """
    workflow = StateGraph(DemoState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("order_management", order_management_node)
    workflow.add_node("logistics", logistics_node)
    workflow.add_node("aggregate", aggregate_node)

    # 设置入口
    workflow.set_entry_point("supervisor")

    # 条件边：Supervisor → Expert 或 Aggregate
    workflow.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "order_management": "order_management",
            "logistics": "logistics",
            "aggregate": "aggregate",
        },
    )

    # 条件边：Expert → Supervisor 或 Aggregate
    workflow.add_conditional_edges(
        "order_management",
        route_after_expert,
        {"supervisor": "supervisor", "aggregate": "aggregate"},
    )
    workflow.add_conditional_edges(
        "logistics",
        route_after_expert,
        {"supervisor": "supervisor", "aggregate": "aggregate"},
    )

    # 终边：Aggregate → END
    workflow.add_edge("aggregate", END)

    return workflow


# ============================================================
# 5. Demo 1: 基础编译执行
# ============================================================
async def demo_basic_execution():
    """Demo 1: 基础 StateGraph 编译与执行"""
    print("\n" + "=" * 60)
    print("Demo 1: 基础 StateGraph 编译与执行")
    print("=" * 60)

    workflow = build_graph()
    compiled = workflow.compile()

    print(f"\n图结构已编译:")
    print(f"  节点: {list(compiled.get_graph().nodes.keys())}")
    print(f"  边: {[e for e in compiled.get_graph().edges]}")

    initial_state: DemoState = {
        "user_query": "帮我查询订单 ORD-20260701-00001 的配送状态",
        "next_agent": "",
        "expert_outputs": {},
        "final_answer": "",
        "iteration_count": 0,
        "approval_status": "pending",
        "human_feedback": "",
    }

    print(f"\n初始状态: {json.dumps(initial_state, ensure_ascii=False, indent=2)}")

    # 执行图（限制递归深度）
    result = compiled.invoke(initial_state, {"recursion_limit": 25})

    print(f"\n最终结果:")
    print(f"  最终答案: {result.get('final_answer', '')}")
    print(f"  迭代次数: {result.get('iteration_count', 0)}")
    print(f"  Expert 输出: {json.dumps(result.get('expert_outputs', {}), ensure_ascii=False, indent=4)}")

    return result


# ============================================================
# 6. Demo 2: 状态持久化（MemorySaver Checkpoint）
# ============================================================
async def demo_checkpoint_persistence():
    """Demo 2: 状态持久化 — 使用 MemorySaver 保存和恢复执行状态"""
    print("\n" + "=" * 60)
    print("Demo 2: 状态持久化（MemorySaver Checkpoint）")
    print("=" * 60)

    workflow = build_graph()
    memory = MemorySaver()
    compiled = workflow.compile(checkpointer=memory)

    # 配置 thread_id 用于状态隔离
    config = {"configurable": {"thread_id": "demo-thread-001"}}

    initial_state: DemoState = {
        "user_query": "帮我查询订单 ORD-20260701-00001 的配送状态",
        "next_agent": "",
        "expert_outputs": {},
        "final_answer": "",
        "iteration_count": 0,
        "approval_status": "pending",
        "human_feedback": "",
    }

    # 执行并保存状态
    result = compiled.invoke(initial_state, config)

    print(f"\n执行完成，状态已保存到 checkpoint (thread_id=demo-thread-001)")
    print(f"  最终答案: {result.get('final_answer', '')}")

    # 查看 checkpoint 历史
    print(f"\nCheckpoint 历史:")
    for chk in memory.list(config):
        checkpoint_id = chk.config.get("configurable", {}).get("checkpoint_id", "?")
        metadata = chk.metadata if hasattr(chk, 'metadata') else {}
        print(f"  - checkpoint_id={checkpoint_id[:16]}..., source={metadata.get('source', '?')}")

    # 恢复状态 — 使用相同 thread_id 继续执行
    print(f"\n使用相同 thread_id 恢复状态...")
    # 查询已保存的状态
    saved_state = compiled.get_state(config)
    print(f"  已保存的 next_agent: {saved_state.values.get('next_agent', 'N/A')}")
    print(f"  已保存的 iteration_count: {saved_state.values.get('iteration_count', 0)}")

    return result


# ============================================================
# 7. Demo 3: 断点恢复（interrupt_before + 人工审批）
# ============================================================
async def demo_breakpoint_recovery():
    """Demo 3: 断点恢复 — 在 aggregate 前中断，人工审批后继续"""
    print("\n" + "=" * 60)
    print("Demo 3: 断点恢复（人工审批模式）")
    print("=" * 60)

    workflow = build_graph()
    memory = MemorySaver()
    # interrupt_before=["aggregate"]: 在进入 aggregate 节点前暂停
    compiled = workflow.compile(checkpointer=memory, interrupt_before=["aggregate"])

    config = {"configurable": {"thread_id": "demo-thread-002"}}

    initial_state: DemoState = {
        "user_query": "帮我查询订单 ORD-20260701-00001 的配送状态",
        "next_agent": "",
        "expert_outputs": {},
        "final_answer": "",
        "iteration_count": 0,
        "approval_status": "pending",
        "human_feedback": "",
    }

    # 第一次执行 — 会在 aggregate 前暂停
    print("\n第一次执行: 运行到 aggregate 前暂停...")
    result = compiled.invoke(initial_state, config)

    print(f"\n暂停状态:")
    print(f"  next_agent: {result.get('next_agent', '')}")
    print(f"  expert_outputs 已收集: {list(result.get('expert_outputs', {}).keys())}")
    print(f"  final_answer: {result.get('final_answer', '')} (尚未生成)")

    # 模拟人工审批
    print(f"\n模拟人工审批...")
    order_data = result.get("expert_outputs", {}).get("order_management", {})
    print(f"  订单状态: {order_data.get('status', '')}")
    print(f"  物流单号: {order_data.get('tracking_number', '')}")
    print(f"  审批结果: 通过 [OK]")

    # 更新状态后继续执行
    compiled.update_state(
        config,
        {"approval_status": "approved", "human_feedback": "审批通过，可以聚合输出"},
    )

    # 继续执行
    print(f"\n继续执行: 进入 aggregate 节点...")
    final_result = compiled.invoke(None, config)  # None 表示从当前状态继续

    print(f"\n最终结果:")
    print(f"  最终答案: {final_result.get('final_answer', '')}")
    print(f"  审批状态: {final_result.get('approval_status', '')}")
    print(f"  人工反馈: {final_result.get('human_feedback', '')}")

    return final_result


# ============================================================
# 8. Demo 4: 流式执行
# ============================================================
async def demo_streaming():
    """Demo 4: 流式执行 — 逐步观察每个节点的输出"""
    print("\n" + "=" * 60)
    print("Demo 4: 流式执行（逐步观察节点输出）")
    print("=" * 60)

    workflow = build_graph()
    compiled = workflow.compile()

    initial_state: DemoState = {
        "user_query": "帮我查询订单 ORD-20260701-00001 的配送状态",
        "next_agent": "",
        "expert_outputs": {},
        "final_answer": "",
        "iteration_count": 0,
        "approval_status": "pending",
        "human_feedback": "",
    }

    print(f"\n流式执行过程:")
    for step_idx, chunk in enumerate(compiled.stream(initial_state, {"recursion_limit": 25})):
        node_name = list(chunk.keys())[0]
        node_output = chunk[node_name]
        print(f"  Step {step_idx + 1}: 节点 '{node_name}' → {json.dumps(node_output, ensure_ascii=False)}")

    print(f"\n流式执行完成!")


# ============================================================
# 9. 主入口
# ============================================================
async def main():
    print("=" * 60)
    print("LangGraph StateGraph 编译与执行 Demo")
    print("=" * 60)
    print(f"核心特性演示:")
    print(f"  1. StateGraph 编译执行")
    print(f"  2. 状态持久化 (MemorySaver)")
    print(f"  3. 断点恢复 (interrupt_before)")
    print(f"  4. 流式执行 (stream)")
    print()

    # Demo 1: 基础编译执行
    await demo_basic_execution()

    # Demo 2: 状态持久化
    await demo_checkpoint_persistence()

    # Demo 3: 断点恢复
    await demo_breakpoint_recovery()

    # Demo 4: 流式执行
    await demo_streaming()

    print("\n" + "=" * 60)
    print("所有 Demo 执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())