import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckSquare, Clock } from 'lucide-react';
import { dataAccessClient } from '../lib/dataAccessClient';
import { ErrorState, EmptyState, SkeletonItem } from '../components/shared/SharedStates';

export default function Chronos() {
  const [activeTab, setActiveTab] = useState<'open' | 'done'>('open');

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['chronos', 'tasks', activeTab],
    queryFn: () => dataAccessClient.fetchChronosTasks(activeTab),
  });

  return (
    <div className="flex flex-col h-full space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Chronos</h1>
        <p className="text-zinc-500 text-sm mt-1">Gestão de tempo e prioridades.</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-zinc-800">
        <button 
          onClick={() => setActiveTab('open')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'open' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
        >
          Abertas
        </button>
        <button 
          onClick={() => setActiveTab('done')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'done' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}
        >
          Concluídas
        </button>
      </div>

      {/* Listagem */}
      <div className="flex-1 overflow-auto bg-zinc-900/30 border border-zinc-800 rounded-lg p-4">
        {isLoading && <div className="space-y-3"><SkeletonItem /><SkeletonItem /><SkeletonItem /></div>}
        {error && <ErrorState error={error as Error} onRetry={refetch} />}
        {data?.tasks.length === 0 && <EmptyState icon={activeTab === 'open' ? Clock : CheckSquare} message={`Nenhuma tarefa ${activeTab === 'open' ? 'pendente' : 'concluída'} encontrada.`} />}

        {data && data.tasks.length > 0 && (
          <ul className="space-y-2">
            {data.tasks.map((task) => (
              <li key={task.id} className="flex items-center justify-between p-3 bg-zinc-900/80 border border-zinc-800 rounded-md">
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${task.priority === 'high' ? 'bg-red-500' : task.priority === 'medium' ? 'bg-amber-500' : 'bg-blue-500'}`} />
                  <span className={`text-sm ${activeTab === 'done' ? 'text-zinc-500 line-through' : 'text-zinc-200'}`}>{task.title}</span>
                </div>
                {task.due_date && <span className="text-xs text-zinc-500">{task.due_date}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}