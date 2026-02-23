export const queryKeys = {
  tasks: {
    all: ['tasks'] as const,
    list: (filters: string) => ['tasks', { filters }] as const,
  },
  proposals: {
    all: ['proposals'] as const,
    pending: ['proposals', 'pending'] as const,
  },
  rpg: ['rpg', 'status'] as const,
  treasury: ['treasury', 'summary'] as const,
};