import { useQuery } from '@tanstack/react-query';
import { CheckSquare } from 'lucide-react';
import { dataAccessClient } from '../../lib/dataAccessClient';
import { HudCard } from '../../components/shared/HudCard';
import { ErrorState, EmptyState, SkeletonItem } from '../../components/shared/SharedStates';

export function ChronosHUD() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['chronos', 'today'],
    queryFn: () => dataAccessClient.fetchChronosToday(),
  });

  return (
    <HudCard title="Chronos: Hoje" icon={CheckSquare}>
      {isLoading && <div className="space-y-2"><SkeletonItem /><SkeletonItem /><SkeletonItem /></div>}
      {error && <ErrorState error={error as Error} onRetry={refetch} />}
      {data?.today.length === 0 && <EmptyState icon={CheckSquare} message="O dia está limpo. Nenhuma tarefa pendente." />}
      
      {data && data.today.length > 0 && (
        <ul className="space-y-2">
          {data.overdue_count > 0 && (
            <div className="text-xs text-red-400 mb-3 font-medium">{data.overdue_count} tarefas atrasadas requerem atenção.</div>
          )}
          {data.today.map((task) => (
            <li key={task.id} className="flex items-center gap-3 p-2 bg-zinc-800/30 rounded-md border border-zinc-800/50">
              <input type="checkbox" className="w-4 h-4 rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-0" />
              <span className="text-sm text-zinc-300">{task.title}</span>
            </li>
          ))}
        </ul>
      )}
    </HudCard>
  );
}