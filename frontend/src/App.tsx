import Sidebar from './components/Sidebar';
import ChatPanel from './components/ChatPanel';
import HistoryPanel from './components/HistoryPanel';
import EndpointPanel from './components/EndpointPanel';
import ToastContainer from './components/Toast';
import { useInit } from './hooks/useInit';

function App() {
  useInit();

  return (
    <div className="flex h-screen bg-[#0a0e17] text-zinc-200 overflow-hidden">
      <Sidebar />
      <ChatPanel />
      <HistoryPanel />
      <EndpointPanel />
      <ToastContainer />
    </div>
  );
}

export default App;