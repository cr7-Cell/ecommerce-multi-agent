import { create } from 'zustand';

export interface AgentInfo {
  name: string;
  description: string;
}

export interface ToolInfo {
  name: string;
  description: string;
  category: string;
  parameters: Record<string, unknown>;
  agent_name: string;
  timeout_seconds: number;
  requires_auth: boolean;
  tags: string[];
}

export interface ChatResponse {
  answer: string;
  expert_outputs: Record<string, unknown>;
  session_id: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  rawResponse?: ChatResponse;
  timestamp: string;
  duration?: number;
}

export interface HistoryItem {
  id: string;
  query: string;
  response: ChatResponse;
  timestamp: string;
  duration: number;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface AppState {
  apiBaseUrl: string;
  isConnected: boolean;
  responseTime: number;
  agents: AgentInfo[];
  selectedAgent: string;
  agentTools: ToolInfo[];
  messages: Message[];
  isLoading: boolean;
  history: HistoryItem[];
  historySearch: string;
  toasts: ToastMessage[];
  showEndpointPanel: boolean;
  showHistory: boolean;

  setApiBaseUrl: (url: string) => void;
  setIsConnected: (connected: boolean) => void;
  setResponseTime: (time: number) => void;
  setAgents: (agents: AgentInfo[]) => void;
  setSelectedAgent: (agent: string) => void;
  setAgentTools: (tools: ToolInfo[]) => void;
  addMessage: (msg: Message) => void;
  setIsLoading: (loading: boolean) => void;
  addHistory: (item: HistoryItem) => void;
  setHistorySearch: (search: string) => void;
  addToast: (toast: ToastMessage) => void;
  removeToast: (id: string) => void;
  toggleEndpointPanel: () => void;
  toggleHistory: () => void;
  loadHistory: () => void;
}

const HISTORY_KEY = 'ecommerce-agent-history';

function loadHistoryFromStorage(): HistoryItem[] {
  try {
    const data = localStorage.getItem(HISTORY_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

function saveHistoryToStorage(history: HistoryItem[]) {
  try {
    const trimmed = history.slice(-100);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
  } catch { /* ignore */ }
}

export const useStore = create<AppState>((set, get) => ({
  apiBaseUrl: 'https://imagination-then-reads-reward.trycloudflare.com',
  isConnected: false,
  responseTime: 0,
  agents: [],
  selectedAgent: '',
  agentTools: [],
  messages: [],
  isLoading: false,
  history: loadHistoryFromStorage(),
  historySearch: '',
  toasts: [],
  showEndpointPanel: false,
  showHistory: true,

  setApiBaseUrl: (url) => set({ apiBaseUrl: url }),
  setIsConnected: (connected) => set({ isConnected: connected }),
  setResponseTime: (time) => set({ responseTime: time }),
  setAgents: (agents) => set({ agents }),
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  setAgentTools: (tools) => set({ agentTools: tools }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setIsLoading: (loading) => set({ isLoading: loading }),
  addHistory: (item) => {
    const updated = [...get().history, item];
    saveHistoryToStorage(updated);
    set({ history: updated });
  },
  setHistorySearch: (search) => set({ historySearch: search }),
  addToast: (toast) => set((s) => ({ toasts: [...s.toasts, toast] })),
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  toggleEndpointPanel: () => set((s) => ({ showEndpointPanel: !s.showEndpointPanel })),
  toggleHistory: () => set((s) => ({ showHistory: !s.showHistory })),
  loadHistory: () => set({ history: loadHistoryFromStorage() }),
}));