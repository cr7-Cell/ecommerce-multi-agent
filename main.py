"""
跨境电商多智能体系统 - 主入口
=============================
基于 MCP 协议 + LangGraph Supervisor-Expert 协作模式

启动方式:
    python main.py

API 服务启动:
    python main.py --api

交互式命令行:
    python main.py --cli
"""

import argparse
import asyncio
import logging
import sys
from typing import Any, Dict

from core.graph import MultiAgentGraph, build_langgraph
from core.supervisor import SupervisorAgent
from config.settings import system_config

# 配置日志
logging.basicConfig(
    level=getattr(logging, system_config.log_level),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('agent_system.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# 交互式命令行
# ============================================================
async def interactive_cli():
    """交互式命令行模式"""
    print("=" * 60)
    print("  跨境电商多智能体系统")
    print("  基于 MCP 协议 + Supervisor-Expert 协作模式")
    print("=" * 60)
    print("\n支持的 Agent:")
    print("  - 选品分析 (market_research)")
    print("  - 广告投放 (advertising)")
    print("  - 客服 (customer_service)")
    print("  - 供应链 (supply_chain)")
    print("  - 订单管理 (order_management)")
    print("  - 个性化推荐 (recommendation)")
    print("  - 库存管理 (inventory)")
    print("  - 支付处理 (payment)")
    print("  - 物流追踪 (logistics)")
    print("  - 营销活动 (marketing)")
    print("  - 用户行为分析 (user_behavior)")
    print("\n输入 'quit' 或 'exit' 退出\n")

    graph = MultiAgentGraph()

    while True:
        try:
            user_input = input("\n[You] ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("再见！")
                break

            print("\n[System] Processing...")
            result = await graph.run(user_input)

            print(f"\n[System]\n{result['final_answer']}")
            print(f"\n[调试] 执行 Agent: {list(result.get('expert_outputs', {}).keys())}")
            print(f"[调试] 迭代次数: {result.get('iteration_count', 0)}")

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            logger.error(f"处理失败: {e}")
            print(f"\n[ERROR] {e}")


# ============================================================
# API 服务（FastAPI）
# ============================================================
def start_api_server():
    """启动 API 服务"""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
    except ImportError:
        print("请安装依赖: pip install fastapi uvicorn")
        return

    app = FastAPI(
        title="跨境电商多智能体系统 API",
        description="基于 MCP 协议 + Supervisor-Expert 协作模式",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 全局图实例
    _graph = None

    def get_graph():
        nonlocal _graph
        if _graph is None:
            _graph = MultiAgentGraph()
        return _graph

    @app.get("/health")
    async def health():
        return {"status": "ok", "timestamp": __import__("datetime").datetime.now().isoformat()}

    @app.post("/chat")
    async def chat(request: dict):
        """处理用户请求"""
        user_query = request.get("query", "")
        user_context = request.get("context", {})

        if not user_query:
            return {"error": "query 不能为空"}

        graph = get_graph()
        result = await graph.run(user_query, user_context)

        return {
            "answer": result["final_answer"],
            "expert_outputs": result["expert_outputs"],
            "session_id": result["session_id"],
        }

    @app.get("/agents")
    async def list_agents():
        """列出所有 Agent"""
        return {
            "agents": [
                {"name": "market_research", "description": "选品分析"},
                {"name": "advertising", "description": "广告投放"},
                {"name": "customer_service", "description": "客服"},
                {"name": "supply_chain", "description": "供应链预测"},
                {"name": "order_management", "description": "订单管理"},
                {"name": "recommendation", "description": "个性化推荐"},
                {"name": "inventory", "description": "库存管理"},
                {"name": "payment", "description": "支付处理"},
                {"name": "logistics", "description": "物流追踪"},
                {"name": "marketing", "description": "营销活动"},
                {"name": "user_behavior", "description": "用户行为分析"},
            ]
        }

    @app.get("/tools/{agent_name}")
    async def list_tools(agent_name: str):
        """列出 Agent 的工具"""
        from core.mcp.tools import get_tools_for_agent
        tools = get_tools_for_agent(agent_name)
        return {
            "agent": agent_name,
            "tools": [t.to_dict() for t in tools],
        }

    print("启动 API 服务: http://localhost:7000")
    print("API 文档: http://localhost:7000/docs")
    uvicorn.run(app, host="0.0.0.0", port=7000)


# ============================================================
# 单次查询
# ============================================================
async def single_query(query: str):
    """单次查询模式"""
    graph = MultiAgentGraph()
    result = await graph.run(query)
    print(result["final_answer"])
    return result


# ============================================================
# 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="跨境电商多智能体系统")
    parser.add_argument("--api", action="store_true", help="启动 API 服务")
    parser.add_argument("--cli", action="store_true", help="启动交互式命令行")
    parser.add_argument("--query", type=str, help="单次查询")
    parser.add_argument("--build-graph", action="store_true", help="输出 LangGraph 图结构")

    args = parser.parse_args()

    if args.build_graph:
        graph = build_langgraph()
        if graph:
            print("LangGraph 图结构:")
            print(graph.get_graph().draw_ascii())
        return

    if args.api:
        start_api_server()
    elif args.query:
        asyncio.run(single_query(args.query))
    else:
        # 默认启动交互式 CLI
        asyncio.run(interactive_cli())


if __name__ == "__main__":
    main()