import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Sparkles } from 'lucide-react';
import { useStore } from '../store/useStore';
import { useApi } from '../hooks/useApi';

const QUICK_TEMPLATES = [
  '你好，你是谁？',
  '查询订单 ORD-20260701-00001',
  '追踪物流 TRK-US-12345',
  '查询汇率 USD 转 CNY',
];

export default function ChatPanel() {
  const [input, setInput] = useState('');
  const { messages, isLoading, selectedAgent } = useStore();
  const { sendChat } = useApi();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput('');
    await sendChat(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTemplate = (tpl: string) => {
    setInput(tpl);
    inputRef.current?.focus();
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#0d1117]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-[#00d4aa]/10 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-[#00d4aa]" />
            </div>
            <div>
              <h2 className="text-lg font-['Orbitron'] text-zinc-300 tracking-wider mb-2">
                Multi-Agent System
              </h2>
              <p className="text-sm text-zinc-500 max-w-md">
                输入查询内容，系统将自动路由到对应的 Agent 进行处理。
                当前选中: <span className="text-[#00d4aa]">{selectedAgent || 'auto'}</span>
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {QUICK_TEMPLATES.map((tpl) => (
                <button
                  key={tpl}
                  onClick={() => handleTemplate(tpl)}
                  className="px-3 py-1.5 text-xs text-zinc-400 border border-zinc-700 rounded-full hover:border-[#00d4aa]/50 hover:text-[#00d4aa] hover:bg-[#00d4aa]/5 transition-all"
                >
                  {tpl}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-[#00d4aa]/15 border border-[#00d4aa]/30 text-zinc-200'
                  : 'bg-[#1a1f2e] border border-zinc-700/50 text-zinc-300'
              }`}
            >
              <div className="text-xs text-zinc-500 mb-1 font-['Orbitron'] tracking-wider">
                {msg.role === 'user' ? 'YOU' : 'SYSTEM'}
                {msg.duration && <span className="ml-2 text-zinc-600">{msg.duration}ms</span>}
              </div>
              <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {msg.content}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1f2e] border border-zinc-700/50 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2 text-zinc-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Processing...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-[#00d4aa]/10">
        <div className="flex items-center gap-3 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Enter your query..."
              disabled={isLoading}
              className="w-full bg-[#0a0e17] border border-[#00d4aa]/20 rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-[#00d4aa]/60 focus:shadow-[0_0_20px_rgba(0,212,170,0.1)] transition-all disabled:opacity-50"
            />
          </div>
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="shrink-0 w-10 h-10 bg-gradient-to-br from-[#00d4aa] to-[#00a88a] rounded-xl flex items-center justify-center hover:shadow-[0_0_20px_rgba(0,212,170,0.3)] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4 text-[#0a0e17]" />
          </button>
        </div>
      </div>
    </div>
  );
}