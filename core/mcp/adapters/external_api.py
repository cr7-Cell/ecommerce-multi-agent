"""
外部 API 适配器
===============
将 MCP 工具调用桥接到外部 HTTP API。

支持的外部服务：
  - 物流追踪（模拟 17track / FedEx 等 API）
  - 汇率查询（模拟实时汇率 API）

设计模式：外部 API 模拟器
  - 真实生产环境：替换为真实 API 调用（httpx → 外部服务）
  - 开发/测试环境：使用内置模拟器（无需外部 API Key）
  - 切换方式：修改 _api_base_url 和 _api_key
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

from core.mcp.adapters.base import (
    ToolAdapter, ToolRequest, ToolResponse, AdapterStatus,
)

logger = logging.getLogger(__name__)


class ExternalAPIAdapter(ToolAdapter):
    """
    外部 API 适配器 — HTTP 调用外部服务

    支持的工具：
      - track_shipment: 物流追踪
      - estimate_delivery: 配送预估
      - get_exchange_rate: 汇率查询

    真实 API 对接示例（替换 _call_service 中的模拟逻辑即可）：
      async def _call_service(self, request):
          async with httpx.AsyncClient() as client:
              resp = await client.get(
                  f"{self._api_base_url}/track/{request.arguments['tracking_number']}",
                  headers={"Authorization": f"Bearer {self._api_key}"},
              )
              return resp.json()
    """

    def __init__(self, api_base_url: str = "", api_key: str = ""):
        super().__init__(
            name="external_api",
            description="外部 API 适配器：HTTP 调用物流追踪、汇率查询等外部服务",
        )
        self._api_base_url = api_base_url
        self._api_key = api_key
        self._use_mock = not api_base_url  # 无真实 API 地址时使用模拟器

    # ---- ToolAdapter 抽象方法实现 ----

    def _validate(self, arguments: Dict[str, Any]) -> None:
        tool_name = arguments.get("_tool_name", "")
        if tool_name == "track_shipment":
            if not arguments.get("tracking_number"):
                raise ValueError("track_shipment 需要 tracking_number 参数")
        elif tool_name == "get_exchange_rate":
            if not arguments.get("from_currency") or not arguments.get("to_currency"):
                raise ValueError("get_exchange_rate 需要 from_currency 和 to_currency 参数")

    async def _call_service(self, request: ToolRequest) -> Any:
        """调用外部 API（或模拟器）"""
        if self._use_mock:
            return await self._mock_service(request)
        else:
            return await self._real_api_call(request)

    def _transform_response(self, raw_result: Any, request: ToolRequest) -> ToolResponse:
        """转换外部 API 响应"""
        return ToolResponse(
            status=AdapterStatus.SUCCESS,
            data=raw_result,
            metadata={"source": "external_api", "mock": self._use_mock},
        )

    # ---- 真实 API 调用 ----

    async def _real_api_call(self, request: ToolRequest) -> dict:
        """真实 HTTP API 调用（生产环境用）"""
        tool_name = request.tool_name
        args = request.arguments

        endpoints = {
            "track_shipment": f"/track/{args.get('tracking_number', '')}",
            "estimate_delivery": "/delivery/estimate",
            "get_exchange_rate": f"/exchange/{args.get('from_currency', 'USD')}/{args.get('to_currency', 'CNY')}",
        }

        url = f"{self._api_base_url.rstrip('/')}{endpoints.get(tool_name, '/')}"
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            if tool_name == "estimate_delivery":
                response = await client.post(url, json=args, headers=headers)
            else:
                response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    # ---- 模拟器（开发/测试环境） ----

    async def _mock_service(self, request: ToolRequest) -> dict:
        """内置模拟器 — 生成逼真的模拟数据"""
        tool_name = request.tool_name

        mock_handlers = {
            "track_shipment": self._mock_track_shipment,
            "estimate_delivery": self._mock_estimate_delivery,
            "get_exchange_rate": self._mock_exchange_rate,
        }

        handler = mock_handlers.get(tool_name, self._mock_default)
        return handler(request)

    def _mock_track_shipment(self, request: ToolRequest) -> dict:
        tracking_number = request.arguments.get("tracking_number", "TRK-000000")
        carriers = ["FedEx", "DHL", "UPS", "USPS", "顺丰国际"]
        locations = ["深圳", "广州海关", "香港", "洛杉矶", "纽约", "芝加哥", "旧金山"]

        # 根据运单号生成确定性的模拟数据
        seed = sum(ord(c) for c in tracking_number)
        random.seed(seed)

        statuses = ["已揽收", "运输中", "清关中", "到达目的国", "派送中", "已签收"]
        current_status = random.choice(statuses)
        current_location = random.choice(locations)

        # 生成物流历史
        history = []
        base_date = datetime.now() - timedelta(days=random.randint(3, 10))
        for i, status in enumerate(statuses[:statuses.index(current_status) + 1]):
            history.append({
                "time": (base_date + timedelta(days=i)).strftime("%Y-%m-%d %H:%M"),
                "status": status,
                "location": random.choice(locations),
            })

        return {
            "tracking_number": tracking_number,
            "carrier": random.choice(carriers),
            "status": current_status,
            "current_location": current_location,
            "estimated_delivery": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
            "history": history,
            "source": "mock_api",
        }

    def _mock_estimate_delivery(self, request: ToolRequest) -> dict:
        from_address = request.arguments.get("from_address", "深圳")
        to_address = request.arguments.get("to_address", "洛杉矶")

        return {
            "from": from_address,
            "to": to_address,
            "estimates": [
                {"carrier": "FedEx", "days": "3-5", "cost": "$25.00"},
                {"carrier": "DHL", "days": "2-4", "cost": "$35.00"},
                {"carrier": "UPS", "days": "4-6", "cost": "$20.00"},
                {"carrier": "顺丰国际", "days": "5-7", "cost": "$15.00"},
            ],
            "recommended": "DHL",
            "source": "mock_api",
        }

    def _mock_exchange_rate(self, request: ToolRequest) -> dict:
        from_cur = request.arguments.get("from_currency", "USD")
        to_cur = request.arguments.get("to_currency", "CNY")

        # 模拟汇率（接近真实值）
        rates = {
            ("USD", "CNY"): 7.25,
            ("USD", "EUR"): 0.92,
            ("USD", "GBP"): 0.79,
            ("USD", "JPY"): 149.50,
            ("CNY", "USD"): 0.138,
            ("EUR", "USD"): 1.09,
        }

        rate = rates.get((from_cur, to_cur), 1.0)
        # 添加小幅随机波动
        rate *= random.uniform(0.995, 1.005)

        return {
            "from_currency": from_cur,
            "to_currency": to_cur,
            "rate": round(rate, 4),
            "timestamp": datetime.now().isoformat(),
            "source": "mock_api",
        }

    def _mock_default(self, request: ToolRequest) -> dict:
        return {
            "result": f"模拟 {request.tool_name} 执行完成",
            "source": "mock_api",
        }