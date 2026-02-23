import { useQuery } from '@tanstack/react-query';
import { Wallet } from 'lucide-react';
import { dataAccessClient } from '../../lib/dataAccessClient';
import { HudCard } from '../../components/shared/HudCard';
import { ErrorState, EmptyState, SkeletonItem } from '../../components/shared/SharedStates';

export function TreasuryHUD() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['treasury', 'summary', 'week'],
    queryFn: () => dataAccessClient.fetchTreasurySummary('week'),
  });

  return (
    <HudCard title="Treasury: Fluxo Semanal" icon={Wallet}>
      {isLoading && <div className="space-y-2"><SkeletonItem /><SkeletonItem /></div>}
      {error && <ErrorState error={error as Error} onRetry={refetch} />}
      {!data && !isLoading && !error && <EmptyState icon={Wallet} message="Sem dados financeiros recentes." />}
      
      {data && (
        <div className="space-y-4">
          <div className="flex justify-between items-baseline">
            <span className="text-xs text-zinc-500 uppercase tracking-wider">Saldo Atual</span>
            <span className="text-2xl font-bold text-emerald-400">R$ {data.current_balance.toFixed(2)}</span>
          </div>
          <div className="space-y-2">
            <span className="text-xs text-zinc-500">Últimas Movimentações</span>
            {data.recent_transactions.slice(0, 3).map((tx) => (
              <div key={tx.id} className="flex justify-between text-sm items-center p-2 rounded-md hover:bg-zinc-800/50">
                <span className="text-zinc-300">{tx.category}</span>
                <span className={tx.type === 'INCOME' ? 'text-emerald-400' : 'text-red-400'}>
                  {tx.type === 'INCOME' ? '+' : '-'} R$ {tx.amount.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </HudCard>
  );
}