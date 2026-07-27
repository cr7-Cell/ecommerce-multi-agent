import { useCallback } from 'react';
import { useStore, type AgentInfo, type ToolInfo, type ChatResponse } from '../store/useStore';

export function useApi() {
  const {
    apiBaseUrl, setIsConnected, setResponseTime, setAgents,
    setAgentTools, addToast, setIsLoading, addMessage, addHistory,
  } = useStore();

  const apiFetch = useCallback(async <T>(path: string, options?: RequestInit): Promise<T> => {
    const start = Date.now();
    try {
      const res = await fetch(`${apiBaseUrl}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      });
      const data = await res.json();
      setResponseTime(Date.now() - start);
      if (!res.ok) throw new Error(data.error || data.detail || `HTTP ${res.status}`);
      setIsConnected(true);
      return data as T;
    } catch (err) {
      setResponseTime(Date.now() - start);
      setIsConnected(false);
      throw err;
    }
  }, [apiBaseUrl, setIsConnected, setResponseTime]);

  const checkHealth = useCallback(async () => {
    try {
      await apiFetch<{ status: string }>('/health');
      addToast({ id: Date.now().toString(), type: 'success', message: 'API 连接成功' });
    } catch {
      addToast({ id: Date.now().toString(), type: 'error', message: 'API 连接失败' });
    }
  }, [apiFetch, addToast]);

  const loadAgents = useCallback(async () => {
    try {
      const data = await apiFetch<{ agents: AgentInfo[] }>('/agents');
      setAgents(data.agents);
    } catch {
      addToast({ id: Date.now().toString(), type: 'error', message: '加载 Agent 列表失败' });
    }
  }, [apiFetch, setAgents, addToast]);

  const loadTools = useCallback(async (agentName: string) => {
    try {
      const data = await apiFetch<{ agent: string; tools: ToolInfo[] }>(`/tools/${agentName}`);
      setAgentTools(data.tools);
    } catch {
      addToast({ id: Date.now().toString(), type: 'error', message: `加载 ${agentName} 工具列表失败` });
    }
  }, [apiFetch, setAgentTools, addToast]);

  const sendChat = useCallback(async (query: string) => {
    const msgId = Date.now().toString();
    setIsLoading(true);
    const start = Date.now();

    addMessage({
      id: msgId,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    });

    try {
      const data = await apiFetch<ChatResponse>('/chat', {
        method: 'POST',
        body: JSON.stringify({ query }),
      });

      const duration = Date.now() - start;

      let displayContent: string;
      try {
        const parsed = JSON.parse(data.answer);
        displayContent = parsed.answer || data.answer;
      } catch {
        displayContent = data.answer;
      }

      addMessage({
        id: `resp-${msgId}`,
        role: 'assistant',
        content: displayContent,
        rawResponse: data,
        timestamp: new Date().toISOString(),
        duration,
      });

      addHistory({
        id: msgId,
        query,
        response: data,
        timestamp: new Date().toISOString(),
        duration,
      });
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '请求失败';
      addMessage({
        id: `err-${msgId}`,
        role: 'assistant',
        content: `[ERROR] ${errorMsg}`,
        timestamp: new Date().toISOString(),
      });
      addToast({ id: msgId, type: 'error', message: errorMsg });
    } finally {
      setIsLoading(false);
    }
  }, [apiFetch, setIsLoading, addMessage, addHistory, addToast]);

  return { checkHealth, loadAgents, loadTools, sendChat, apiFetch };
}