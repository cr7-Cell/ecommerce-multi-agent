import { Activity, Layers, Server, Zap } from 'lucide-react';
import { useStore } from '../store/useStore';

export default function Sidebar() {
  const { agents, isConnected, responseTime, selectedAgent, setSelectedAgent, toggleEndpointPanel } = useStore();

  return (
    <aside className="w-64 h-screen bg-[#0a0e17]/90 backdrop-blur border-r border-[#00d4aa]/10 flex flex-col shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-[#00d4aa]/10">
        <div className="flex items-center gap-2 mb-2">
          <Layers className="w-5 h-5 text-[#00d4aa]" />
          <h1 className="font-['Orbitron'] text-sm font-bold tracking-wider text-[#00d4aa]">
            AGENT HUB
          </h1>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#00d4aa] shadow-[0_0_6px_#00d4aa]' : 'bg-red-500'}`} />
          <span className="text-zinc-400">
            {isConnected ? `Connected (${responseTime}ms)` : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Agent List */}
      <div className="flex-1 overflow-y-auto py-2">
        <p className="px-4 py-2 text-[10px] uppercase tracking-widest text-zinc-500">Agents</p>
        {agents.map((agent) => (
          <button
            key={agent.name}
            onClick={() => setSelectedAgent(agent.name)}
            className={`w-full text-left px-4 py-2.5 flex items-center gap-3 transition-all duration-200 group ${
              selectedAgent === agent.name
                ? 'bg-[#00d4aa]/10 border-r-2 border-[#00d4aa] text-[#00d4aa]'
                : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
            }`}
          >
            <Server className={`w-4 h-4 shrink-0 ${
              selectedAgent === agent.name ? 'text-[#00d4aa]' : 'text-zinc-600 group-hover:text-zinc-400'
            }`} />
            <div className="min-w-0">
              <p className="text-xs font-medium truncate">{agent.description}</p>
              <p className="text-[10px] text-zinc-500 truncate">{agent.name}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Bottom Actions */}
      <div className="p-3 border-t border-[#00d4aa]/10 space-y-1.5">
        <button
          onClick={toggleEndpointPanel}
          className="w-full flex items-center gap-2 px-3 py-2 text-xs text-zinc-400 hover:text-[#00d4aa] hover:bg-[#00d4aa]/5 rounded transition-colors"
        >
          <Activity className="w-4 h-4" />
          <span>API Endpoints</span>
        </button>
        <div className="flex items-center gap-2 px-3 py-2 text-[10px] text-zinc-600">
          <Zap className="w-3 h-3" />
          <span>DeepSeek</span>
        </div>
      </div>
    </aside>
  );
}