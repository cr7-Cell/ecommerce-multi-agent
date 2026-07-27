"""
服务健康监控模块
================
提供 API 服务的健康检查、性能指标收集和告警功能。

监控指标:
  - 服务可用性: 健康检查端点响应状态
  - 响应时间: 各端点的平均/最大/最小响应时间
  - 请求量: 按时间窗口统计的请求数
  - 错误率: 4xx/5xx 错误占比
  - LLM 调用延迟: 各 LLM 调用的耗时分布
  - 工具调用统计: 各 MCP 工具的调用次数和成功率
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# 数据模型
# ============================================================

@dataclass
class RequestMetrics:
    """单次请求的性能指标"""
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LLMCallMetrics:
    """LLM 调用指标"""
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    duration_ms: float
    success: bool
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ToolCallMetrics:
    """MCP 工具调用指标"""
    tool_name: str
    agent_name: str
    duration_ms: float
    success: bool
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================
# 健康监控器
# ============================================================

class HealthMonitor:
    """
    服务健康监控器

    使用方式:
        monitor = HealthMonitor()

        # 记录请求
        monitor.record_request("/chat", "POST", 200, 150.5)

        # 记录 LLM 调用
        monitor.record_llm_call("deepseek", "deepseek-chat", 100, 200, 1200.0, True)

        # 记录工具调用
        monitor.record_tool_call("query_order_details", "order_management", 5.5, True)

        # 获取健康报告
        report = monitor.get_health_report()
    """

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self._request_history: List[RequestMetrics] = []
        self._llm_call_history: List[LLMCallMetrics] = []
        self._tool_call_history: List[ToolCallMetrics] = []
        self._start_time = datetime.now()

    def _clean_expired(self):
        """清理过期记录"""
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        cutoff_str = cutoff.isoformat()

        self._request_history = [
            r for r in self._request_history if r.timestamp > cutoff_str
        ]
        self._llm_call_history = [
            c for c in self._llm_call_history if c.timestamp > cutoff_str
        ]
        self._tool_call_history = [
            t for t in self._tool_call_history if t.timestamp > cutoff_str
        ]

    # ---- 记录方法 ----

    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """记录 API 请求"""
        self._request_history.append(RequestMetrics(
            endpoint=endpoint, method=method,
            status_code=status_code, duration_ms=duration_ms,
        ))

    def record_llm_call(self, provider: str, model: str,
                        prompt_tokens: int, completion_tokens: int,
                        duration_ms: float, success: bool, error: str = ""):
        """记录 LLM 调用"""
        self._llm_call_history.append(LLMCallMetrics(
            provider=provider, model=model,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            duration_ms=duration_ms, success=success, error=error,
        ))

    def record_tool_call(self, tool_name: str, agent_name: str,
                         duration_ms: float, success: bool, error: str = ""):
        """记录 MCP 工具调用"""
        self._tool_call_history.append(ToolCallMetrics(
            tool_name=tool_name, agent_name=agent_name,
            duration_ms=duration_ms, success=success, error=error,
        ))

    # ---- 健康检查 ----

    def is_healthy(self) -> bool:
        """检查服务是否健康"""
        self._clean_expired()

        if not self._request_history:
            return True  # 无请求，视为健康

        # 检查最近 5 分钟内的错误率
        total = len(self._request_history)
        errors = sum(1 for r in self._request_history if r.status_code >= 500)

        error_rate = errors / total if total > 0 else 0
        return error_rate < 0.05  # 错误率 < 5% 视为健康

    # ---- 性能报告 ----

    def get_health_report(self) -> Dict[str, Any]:
        """生成健康报告"""
        self._clean_expired()

        # 请求统计
        total_requests = len(self._request_history)
        error_requests = sum(1 for r in self._request_history if r.status_code >= 400)
        durations = [r.duration_ms for r in self._request_history]

        # LLM 统计
        total_llm_calls = len(self._llm_call_history)
        failed_llm_calls = sum(1 for c in self._llm_call_history if not c.success)
        llm_durations = [c.duration_ms for c in self._llm_call_history]
        total_prompt_tokens = sum(c.prompt_tokens for c in self._llm_call_history)
        total_completion_tokens = sum(c.completion_tokens for c in self._llm_call_history)

        # 工具统计
        total_tool_calls = len(self._tool_call_history)
        failed_tool_calls = sum(1 for t in self._tool_call_history if not t.success)
        tool_durations = [t.duration_ms for t in self._tool_call_history]

        # 按工具分组统计
        tool_stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})
        for t in self._tool_call_history:
            tool_stats[t.tool_name]["total"] += 1
            if t.success:
                tool_stats[t.tool_name]["success"] += 1
            else:
                tool_stats[t.tool_name]["failed"] += 1

        uptime_seconds = (datetime.now() - self._start_time).total_seconds()

        return {
            "status": "healthy" if self.is_healthy() else "degraded",
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": str(timedelta(seconds=int(uptime_seconds))),

            # API 请求指标
            "api": {
                "total_requests": total_requests,
                "error_count": error_requests,
                "error_rate": round(error_requests / total_requests * 100, 2) if total_requests > 0 else 0,
                "avg_response_ms": round(sum(durations) / len(durations), 2) if durations else 0,
                "max_response_ms": round(max(durations), 2) if durations else 0,
                "min_response_ms": round(min(durations), 2) if durations else 0,
                "p95_response_ms": round(self._percentile(durations, 95), 2) if durations else 0,
                "p99_response_ms": round(self._percentile(durations, 99), 2) if durations else 0,
            },

            # LLM 调用指标
            "llm": {
                "total_calls": total_llm_calls,
                "failed_calls": failed_llm_calls,
                "success_rate": round((total_llm_calls - failed_llm_calls) / total_llm_calls * 100, 2) if total_llm_calls > 0 else 100,
                "avg_duration_ms": round(sum(llm_durations) / len(llm_durations), 2) if llm_durations else 0,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
            },

            # MCP 工具调用指标
            "tools": {
                "total_calls": total_tool_calls,
                "failed_calls": failed_tool_calls,
                "success_rate": round((total_tool_calls - failed_tool_calls) / total_tool_calls * 100, 2) if total_tool_calls > 0 else 100,
                "avg_duration_ms": round(sum(tool_durations) / len(tool_durations), 2) if tool_durations else 0,
                "by_tool": {k: dict(v) for k, v in tool_stats.items()},
            },

            "window_minutes": self.window_minutes,
            "timestamp": datetime.now().isoformat(),
        }

    def get_quick_status(self) -> Dict[str, Any]:
        """快速状态（轻量级，适合频繁调用）"""
        self._clean_expired()
        return {
            "status": "healthy" if self.is_healthy() else "degraded",
            "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
            "total_requests": len(self._request_history),
            "total_llm_calls": len(self._llm_call_history),
            "total_tool_calls": len(self._tool_call_history),
            "timestamp": datetime.now().isoformat(),
        }

    def _percentile(self, data: List[float], p: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# ============================================================
# 全局单例
# ============================================================

_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """获取全局健康监控器"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor