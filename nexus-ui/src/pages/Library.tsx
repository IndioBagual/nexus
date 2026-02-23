import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Search } from 'lucide-react';
import { dataAccessClient } from '../lib/dataAccessClient';
import { ErrorState, EmptyState, SkeletonItem } from '../components/shared/SharedStates';

export default function Library() {
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['library', 'notes', searchQuery],
    queryFn: () => searchQuery.trim() 
      ? dataAccessClient.searchLibraryNotes(searchQuery)
      : dataAccessClient.fetchLibraryNotes(50, 0), // Default list
  });

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Cérebro Digital</h1>
          <p className="text-zinc-500 text-sm mt-1">Sua base de conhecimento unificada (Zettelkasten).</p>
        </div>
      </div>

      {/* Barra de Busca */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
        <input 
          type="text" 
          placeholder="Pesquisar em todas as notas, entidades e memórias..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg py-2.5 pl-10 pr-4 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
        />
      </div>

      {/* Lista de Resultados */}
      <div className="flex-1 overflow-auto">
        {isLoading && <div className="space-y-3"><SkeletonItem /><SkeletonItem /><SkeletonItem /></div>}
        {error && <ErrorState error={error as Error} onRetry={refetch} />}
        {data?.notes.length === 0 && <EmptyState icon={BookOpen} message={searchQuery ? "Nenhum resultado encontrado para a busca." : "A biblioteca está vazia."} />}

        {data && data.notes.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.notes.map((note) => (
              <div key={note.id} className="bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 transition-colors p-4 rounded-xl flex flex-col h-32 cursor-pointer group">
                <h3 className="font-semibold text-zinc-200 group-hover:text-amber-400 transition-colors line-clamp-2">{note.title}</h3>
                <div className="mt-auto flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {note.tags.map((tag) => (
                      <span key={tag} className="text-[10px] px-2 py-0.5 bg-zinc-800 text-zinc-400 rounded-sm">#{tag}</span>
                    ))}
                  </div>
                  <span className="text-[10px] text-zinc-600">{note.last_modified}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}