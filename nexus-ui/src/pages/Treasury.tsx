import { useQuery } from '@tanstack/react-query';
import { Wallet, Receipt } from 'lucide-react';
import { dataAccessClient } from '../lib/dataAccessClient';
import { ErrorState, EmptyState, SkeletonItem } from '../components/shared/SharedStates';

export default function Treasury() {
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['treasury', 'summary', 'month'],
    queryFn: () => dataAccessClient.fetchTreasurySummary('month'),
  });

  const { data: txData, isLoading: loadingTx, error, refetch } = useQuery({
    queryKey: ['treasury', 'transactions', 'month'],
    queryFn: () => dataAccessClient.fetchTreasuryTransactions('month'),
  });

  return (
    <div className="flex flex-col h-full space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Treasury</h1>
        <p className="text-zinc-500 text-sm mt-1">Controle de fluxo de caixa mensal.</p>
      </div>

      {/* Resumo do Mês */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-zinc-900/40 border border-zinc-800 rounded-lg">
          <div className="text-xs text-zinc-500 uppercase">Saldo Atual</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {loadingSummary ? '...' : `R$ ${summary?.current_balance?.toFixed(2) || '0.00'}`}
          </div>
        </div>
        <div className="p-4 bg-zinc-900/40 border border-zinc-800 rounded-lg">
          <div className="text-xs text-zinc-500 uppercase">Gastos do Mês</div>
          <div className="text-2xl font-bold text-red-400 mt-1">
            {loadingSummary ? '...' : `R$ ${summary?.monthly_expense?.toFixed(2) || '0.00'}`}
          </div>
        </div>
        <div className="p-4 bg-zinc-900/40 border border-zinc-800 rounded-lg">
          <div className="text-xs text-zinc-500 uppercase">Limite Restante</div>
          <div className="text-2xl font-bold text-zinc-300 mt-1">
            {loadingSummary ? '...' : summary?.remaining_limit !== undefined 
              ? `R$ ${summary.remaining_limit?.toFixed(2) || '0.00'}` 
              : summary?.monthly_limit ? 'Backend não processou' : 'Sem Limite'}
          </div>
        </div>
      </div>

      {/* Tabela de Transações */}
      <div className="flex-1 overflow-hidden bg-zinc-900/30 border border-zinc-800 rounded-lg flex flex-col">
        <div className="p-4 border-b border-zinc-800 flex items-center gap-2">
          <Receipt className="w-4 h-4 text-zinc-400" />
          <h3 className="font-semibold text-sm text-zinc-200">Transações (Mês Atual)</h3>
        </div>
        <div className="p-4 flex-1 overflow-auto">
          {loadingTx && <div className="space-y-2"><SkeletonItem /><SkeletonItem /></div>}
          {error && <ErrorState error={error as Error} onRetry={refetch} />}
          {txData?.transactions.length === 0 && <EmptyState icon={Receipt} message="Nenhuma transação neste mês." />}
          
          {txData && txData.transactions.length > 0 && (
            <table className="w-full text-left text-sm text-zinc-400">
              <thead className="text-xs text-zinc-500 uppercase bg-zinc-800/50">
                <tr>
                  <th className="px-4 py-3 rounded-tl-md">Data</th>
                  <th className="px-4 py-3">Categoria</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3 text-right rounded-tr-md">Valor</th>
                </tr>
              </thead>
              <tbody>
                {txData.transactions.map((tx) => (
                  <tr key={tx.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors">
                    <td className="px-4 py-3">{tx.date}</td>
                    <td className="px-4 py-3">{tx.category}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-[10px] font-medium ${tx.type === 'INCOME' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                        {tx.type}
                      </span>
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${tx.type === 'INCOME' ? 'text-emerald-400' : 'text-zinc-300'}`}>
                      R$ {tx.amount.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}