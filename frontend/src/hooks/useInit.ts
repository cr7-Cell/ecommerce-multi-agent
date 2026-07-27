import { useEffect } from 'react';
import { useStore } from '../store/useStore';
import { useApi } from '../hooks/useApi';

export function useInit() {
  const { loadAgents, checkHealth } = useApi();
  const { setSelectedAgent, agents } = useStore();

  useEffect(() => {
    checkHealth();
    loadAgents();
  }, []);

  useEffect(() => {
    if (agents.length > 0 && !useStore.getState().selectedAgent) {
      setSelectedAgent(agents[0].name);
    }
  }, [agents, setSelectedAgent]);
}