import { useQuery } from '@tanstack/react-query';
import { Shield, Award, Zap } from 'lucide-react';
import { dataAccessClient } from '../lib/dataAccessClient';
import { ErrorState, SkeletonItem } from '../components/shared/SharedStates';

export default function RPG() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['rpg', 'status'],
    queryFn: () => dataAccessClient.fetchRPGStatus(),
  });

  return (
    <div className="flex flex-col h-full space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Status do Jogador</h1>
        <p className="text-zinc-500 text-sm mt-1">Evolução, atributos e consistência.</p>
      </div>

      {isLoading && <div className="space-y-4"><SkeletonItem /><SkeletonItem /></div>}
      {error && <ErrorState error={error as Error} onRetry={refetch} />}

      {data && (
        <>
          {/* Painel Principal */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-6 flex flex-col items-center justify-center text-center space-y-4">
              <div className="w-24 h-24 rounded-full border-4 border-amber-500 flex items-center justify-center bg-zinc-950 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
                <span className="text-3xl font-black text-amber-500">{data.level}</span>
              </div>
              <div>
                <h2 className="text-lg font-bold text-zinc-200">Guilherme</h2>
                <p className="text-sm text-zinc-500">Engenheiro de Sistemas</p>
              </div>
              <div className="w-full space-y-2">
                <div className="flex justify-between text-xs text-zinc-400 font-medium">
                  <span>XP: {data.total_xp}</span>
                  <span>Próximo Nível: {data.xp_to_next} XP</span>
                </div>
                <div className="h-3 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500" style={{ width: `${data.progress_percentage || 0}%` }} />
                </div>
              </div>
            </div>

            {/* Atributos e Streak */}
            <div className="flex flex-col gap-4">
              <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Zap className="text-amber-400 w-5 h-5" />
                  <span className="font-semibold text-zinc-200">Consistência (Streak)</span>
                </div>
                <span className="text-2xl font-bold text-zinc-100">{data.current_streak} dias</span>
              </div>

              <div className="bg-zinc-900/40 border border-zinc-800 rounded-xl p-5 flex-1">
                <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider mb-4">Árvore de Atributos</h3>
                <div className="space-y-4">
                  {Object.entries(data.attributes).map(([key, value]) => (
                    <div key={key} className="flex items-center">
                      <span className="w-12 text-xs font-bold text-zinc-400">{key}</span>
                      <div className="flex-1 h-2 mx-3 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(value / (data.attributes_max || 100)) * 100}%` }} />
                      </div>
                      <span className="w-6 text-right text-sm font-medium text-zinc-200">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Conquistas (Placeholder p/ MVP) */}
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-4">
              <Award className="text-zinc-400 w-4 h-4" />
              <h3 className="text-sm font-semibold text-zinc-200">Últimas Conquistas</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="p-3 border border-zinc-800 bg-zinc-900/50 rounded-lg flex flex-col items-center text-center opacity-50 grayscale hover:grayscale-0 transition-all cursor-not-allowed">
                  <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center mb-2">
                    <Award className="w-5 h-5 text-zinc-500" />
                  </div>
                  <span className="text-xs font-medium text-zinc-400">Bloqueado</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}