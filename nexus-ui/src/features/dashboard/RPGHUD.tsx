import { useQuery } from '@tanstack/react-query';
import { Shield } from 'lucide-react';
import { dataAccessClient } from '../../lib/dataAccessClient';
import { HudCard } from '../../components/shared/HudCard';
import { ErrorState, EmptyState, SkeletonItem } from '../../components/shared/SharedStates';

export function RPGHUD() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['rpg', 'status'],
    queryFn: () => dataAccessClient.fetchRPGStatus(),
  });

  return (
    <HudCard title="Evolução" icon={Shield}>
      {isLoading && <div className="space-y-2"><SkeletonItem /><SkeletonItem /></div>}
      {error && <ErrorState error={error as Error} onRetry={refetch} />}
      {!data && !isLoading && !error && <EmptyState icon={Shield} message="Nenhum personagem ativo." />}
      
      {data && (
        <div className="space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-zinc-500 uppercase tracking-wider">Nível Atual</div>
              <div className="text-3xl font-bold text-amber-500">Lv. {data.level}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-zinc-500 uppercase tracking-wider">Streak</div>
              <div className="text-lg font-medium text-zinc-300">{data.current_streak} dias</div>
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-zinc-400">
              <span>XP Total: {data.total_xp}</span>
              <span>Faltam: {data.xp_to_next}</span>
            </div>
            {/* Barra de progresso rudimentar (Sem shadcn full component ainda) */}
            <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-amber-500 w-[60%]" /> {/* Mock width, lógica iria no backend */}
            </div>
          </div>
        </div>
      )}
    </HudCard>
  );
}