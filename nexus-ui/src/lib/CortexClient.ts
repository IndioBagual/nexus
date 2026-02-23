import type { CortexChatResponse } from './apiTypes';

const CORTEX_API = import.meta.env.VITE_CORTEX_API_BASE_URL || 'http://localhost:8001';

export const cortexClient = {
  async chat(message: string): Promise<CortexChatResponse> {
    const res = await fetch(`${CORTEX_API}/cortex/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) throw new Error('Falha de comunicação com o Córtex');
    return res.json();
  }
};