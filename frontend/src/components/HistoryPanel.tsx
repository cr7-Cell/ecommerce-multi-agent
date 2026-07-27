import { useState, useEffect } from 'react';
import { Search, Clock, ChevronRight, Trash2 } from 'lucide-react';
import { useStore, type HistoryItem } from '../store/useStore';

export default function HistoryPanel() {
  const { history, historySearch, setHistorySearch, showHistory, toggleHistory } = useStore();
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);

  const filtered = history
    .filter((h) =>
      h.query.toLowerCase().includes(historySearch.toLowerCase())
    )
    .reverse();

  const clearHistory = () => {
    localStorage.removeItem('ecommerce-agent-history');
    useStore.setState({ history: [], historySearch: '' });
    setSelectedItem(null);
  };

  if (!showHistory) {
    return (
      <button
        onClick={toggleHistory}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-[#0a0e17] border border-[#00d4aa]/20 border-r-0 rounded-l-lg p-2 text-zinc-400 hover:text-[#00d4aa] transition-colors z-10"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    );
  }

  return (
    <aside className="w-72 h-screen bg-[#0a0e17]/95 backdrop-blur border-l border-[#00d4aa]/10 flex flex-col shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-[#00d4aa]/10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#00d4aa]" />
            <h2 className="font-['Orbitron'] text-xs font-bold tracking-wider text-zinc-300">
              HISTORY
            </h2>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={clearHistory}
              className="p-1 text-zinc-600 hover:text-red-400 transition-colors"
              title="Clear history"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={toggleHistory}
              className="p-1 text-zinc-600 hover:text-zinc-400 transition-colors"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-600" />
          <input
            type="text"
            value={historySearch}
            onChange={(e) => setHistorySearch(e.target.value)}
            placeholder="Search..."
            className="w-full bg-[#0d1117] border border-zinc-700/50 rounded-lg pl-8 pr-3 py-1.5 text-xs text-zinc-300 placeholder-zinc-600 focus:outline-none focus:border-[#00d4aa]/40 transition-colors"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <p className="text-xs text-zinc-600 text-center py-8">No history</p>
        )}
        {filtered.map((item) => (
          <button
            key={item.id}
            onClick={() => setSelectedItem(selectedItem?.id === item.id ? null : item)}
            className={`w-full text-left p-3 border-b border-zinc-800/30 transition-colors ${
              selectedItem?.id === item.id ? 'bg-[#00d4aa]/5' : 'hover:bg-white/5'
            }`}
          >
            <p className="text-xs text-zinc-300 truncate mb-1">{item.query}</p>
            <div className="flex items-center gap-2 text-[10px] text-zinc-600">
              <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
              <span>{item.duration}ms</span>
            </div>
          </button>
        ))}
      </div>

      {/* Detail */}
      {selectedItem && (
        <div className="p-3 border-t border-[#00d4aa]/10 bg-[#0d1117] max-h-48 overflow-y-auto">
          <p className="text-[10px] text-zinc-500 mb-1">Response</p>
          <p className="text-xs text-zinc-400 leading-relaxed">
            {(() => {
              try {
                const parsed = JSON.parse(selectedItem.response.answer);
                return parsed.answer || selectedItem.response.answer;
              } catch {
                return selectedItem.response.answer;
              }
            })()}
          </p>
        </div>
      )}
    </aside>
  );
}