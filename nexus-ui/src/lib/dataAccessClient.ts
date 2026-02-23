import type { 
  ChronosTodayResponse, TreasurySummaryResponse, RPGStatusResponse, 
  NotesListResponse, ChronosTasksResponse, TreasuryTransactionsResponse 
} from './apiTypes';

const DATA_API = import.meta.env.VITE_DATA_API_BASE_URL || 'http://localhost:8001';

export const dataAccessClient = {
  async fetchChronosToday(): Promise<ChronosTodayResponse> {
    const res = await fetch(`${DATA_API}/api/chronos/today`);
    if (!res.ok) throw new Error('Falha ao buscar tarefas');
    return res.json();
  },
  async fetchTreasurySummary(range: string = 'week'): Promise<TreasurySummaryResponse> {
    const res = await fetch(`${DATA_API}/api/treasury/summary?range=${range}`);
    if (!res.ok) throw new Error('Falha ao buscar finanças');
    return res.json();
  },
  async fetchRPGStatus(): Promise<RPGStatusResponse> {
    const res = await fetch(`${DATA_API}/api/rpg/status`);
    if (!res.ok) throw new Error('Falha ao buscar status do RPG');
    return res.json();
  },
  async fetchLibraryNotes(limit: number = 5, offset: number = 0): Promise<NotesListResponse> {
    const res = await fetch(`${DATA_API}/api/library/notes?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('Falha ao buscar notas');
    return res.json();
  },
  async fetchChronosTasks(status: 'open' | 'done'): Promise<ChronosTasksResponse> {
    const res = await fetch(`${DATA_API}/api/chronos/tasks?status=${status}`);
    if (!res.ok) throw new Error(`Falha ao buscar tarefas (${status})`);
    return res.json();
  },

  async fetchTreasuryTransactions(range: string = 'month'): Promise<TreasuryTransactionsResponse> {
    const res = await fetch(`${DATA_API}/api/treasury/transactions?range=${range}`);
    if (!res.ok) throw new Error('Falha ao buscar transações');
    return res.json();
  },

  async searchLibraryNotes(query: string): Promise<NotesListResponse> {
    const res = await fetch(`${DATA_API}/api/library/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error('Falha na busca de notas');
    return res.json();
  }
};