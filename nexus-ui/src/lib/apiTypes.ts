export interface Task { id: string; title: string; status: 'TODO' | 'DOING' | 'DONE'; priority: 'low' | 'medium' | 'high'; due_date: string | null; }
export interface Transaction { id: string; amount: number; type: 'INCOME' | 'EXPENSE'; category: string; date: string; }
export interface NoteMetadata { id: string; title: string; tags: string[]; last_modified: string; }

export interface ChronosTodayResponse { today: Task[]; overdue_count: number; }
export interface TreasurySummaryResponse { current_balance: number; monthly_expense: number; monthly_limit: number | null; recent_transactions: Transaction[]; }
export interface RPGStatusResponse { level: number; total_xp: number; xp_to_next: number; attributes: Record<string, number>; current_streak: number; }
export interface NotesListResponse { notes: NoteMetadata[]; total_count: number; }

export interface ChronosTasksResponse {
  tasks: Task[];
  total_count: number;
}

export interface TreasuryTransactionsResponse {
  transactions: Transaction[];
  total_count: number;
}

export interface ExecutionReportItem {
  tool: string;
  status: 'success' | 'error';
  details: string;
}

export interface Citation {
  type: 'note' | 'task' | 'transaction';
  id: string;
  title: string;
}

export interface CortexChatResponse {
  status: 'success' | 'needs_clarification';
  reply: string;
  execution_report?: ExecutionReportItem[];
  citations?: Citation[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'cortex';
  content: string;
  status?: 'success' | 'needs_clarification';
  execution_report?: ExecutionReportItem[];
  citations?: Citation[];
}

export interface TreasurySummaryResponse {
  current_balance: number;
  monthly_expense: number;
  monthly_limit: number | null;
  remaining_limit?: number | null; // <- NOVO: O Backend fará a conta
  recent_transactions: Transaction[];
}

export interface RPGStatusResponse {
  level: number;
  total_xp: number;
  xp_to_next: number;
  progress_percentage?: number; // <- NOVO: O Backend envia a % de XP
  attributes_max?: number; // <- NOVO: O Backend diz qual o nível máximo do atributo
  attributes: Record<string, number>;
  current_streak: number;
}