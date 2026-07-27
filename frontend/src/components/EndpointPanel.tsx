import { useState } from 'react';
import { Play, Copy, Check, ChevronDown, ChevronUp, X } from 'lucide-react';
import { useStore } from '../store/useStore';
import { useApi } from '../hooks/useApi';

interface Endpoint {
  method: string;
  path: string;
  description: string;
  body?: string;
}

const ENDPOINTS: Endpoint[] = [
  { method: 'GET', path: '/health', description: 'Health check' },
  { method: 'GET', path: '/agents', description: 'List all agents' },
  { method: 'GET', path: '/tools/order_management', description: 'Get agent tools' },
  { method: 'POST', path: '/chat', description: 'Send chat query', body: '{"query": "查询订单 ORD-20260701-00001"}' },
];

export default function EndpointPanel() {
  const { showEndpointPanel, toggleEndpointPanel, apiBaseUrl } = useStore();
  const { apiFetch } = useApi();
  const [results, setResults] = useState<Record<string, { data: string; status: string }>>({});
  const [loading, setLoading] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  const testEndpoint = async (ep: Endpoint) => {
    const key = `${ep.method} ${ep.path}`;
    setLoading(key);
    try {
      const options: RequestInit = { method: ep.method };
      if (ep.body) options.body = ep.body;
      const data = await apiFetch<unknown>(ep.path, options);
      setResults((prev) => ({ ...prev, [key]: { data: JSON.stringify(data, null, 2), status: 'success' } }));
    } catch (err) {
      setResults((prev) => ({
        ...prev,
        [key]: { data: err instanceof Error ? err.message : 'Error', status: 'error' },
      }));
    }
    setLoading(null);
  };

  const copyResult = (key: string, data: string) => {
    navigator.clipboard.writeText(data);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  if (!showEndpointPanel) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#0a0e17] border border-[#00d4aa]/20 rounded-2xl w-[640px] max-h-[80vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#00d4aa]/10">
          <h2 className="font-['Orbitron'] text-sm font-bold tracking-wider text-[#00d4aa]">
            API ENDPOINTS
          </h2>
          <div className="flex items-center gap-1 text-[10px] text-zinc-500">
            <span className="text-zinc-600">{apiBaseUrl}</span>
            <button onClick={toggleEndpointPanel} className="p-1 hover:text-zinc-300">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {ENDPOINTS.map((ep) => {
            const key = `${ep.method} ${ep.path}`;
            const result = results[key];
            const isExpanded = expanded[key];

            return (
              <div key={key} className="border border-zinc-800/50 rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 p-3 bg-[#0d1117]">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    ep.method === 'GET' ? 'bg-green-500/10 text-green-400' : 'bg-[#7c3aed]/10 text-[#7c3aed]'
                  }`}>
                    {ep.method}
                  </span>
                  <span className="text-xs text-zinc-300 font-mono flex-1">{ep.path}</span>
                  <span className="text-[10px] text-zinc-600">{ep.description}</span>
                  {result && (
                    <button
                      onClick={() => setExpanded((prev) => ({ ...prev, [key]: !prev[key] }))}
                      className="p-1 text-zinc-500 hover:text-zinc-300"
                    >
                      {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                  )}
                  <button
                    onClick={() => testEndpoint(ep)}
                    disabled={loading === key}
                    className="px-3 py-1 text-[10px] bg-[#00d4aa]/10 text-[#00d4aa] rounded-lg hover:bg-[#00d4aa]/20 transition-colors disabled:opacity-50 flex items-center gap-1"
                  >
                    {loading === key ? (
                      <span className="animate-pulse">...</span>
                    ) : (
                      <>
                        <Play className="w-3 h-3" /> Test
                      </>
                    )}
                  </button>
                </div>

                {ep.body && (
                  <div className="px-3 pb-2">
                    <pre className="text-[10px] text-zinc-500 bg-[#0a0e17] rounded p-2 overflow-x-auto">
                      {ep.body}
                    </pre>
                  </div>
                )}

                {result && isExpanded && (
                  <div className="border-t border-zinc-800/50">
                    <div className="flex items-center justify-between px-3 py-1.5">
                      <span className={`text-[10px] ${result.status === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                        {result.status === 'success' ? '200 OK' : 'Error'}
                      </span>
                      <button
                        onClick={() => copyResult(key, result.data)}
                        className="p-1 text-zinc-500 hover:text-zinc-300"
                      >
                        {copied === key ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                    <pre className="text-[10px] text-zinc-400 bg-[#0a0e17] rounded-b p-3 overflow-x-auto max-h-48 font-mono leading-relaxed">
                      {result.data}
                    </pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}