import { useQuery } from '@tanstack/react-query';
import { BookOpen } from 'lucide-react';
import { dataAccessClient } from '../../lib/dataAccessClient';
import { HudCard } from '../../components/shared/HudCard';
import { ErrorState, EmptyState, SkeletonItem } from '../../components/shared/SharedStates';

export function LibraryHUD() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['library', 'notes', 5, 0],
    queryFn: () => dataAccessClient.fetchLibraryNotes(5, 0),
  });

  return (
    <HudCard title="Library: Acesso Recente" icon={BookOpen}>
      {isLoading && <div className="space-y-2"><SkeletonItem /><SkeletonItem /></div>}
      {error && <ErrorState error={error as Error} onRetry={refetch} />}
      {data?.notes.length === 0 && <EmptyState icon={BookOpen} message="O Zettelkasten está vazio." />}
      
      {data && data.notes.length > 0 && (
        <ul className="space-y-2">
          {data.notes.map((note) => (
            <li key={note.id} className="group p-2 rounded-md hover:bg-zinc-800/50 cursor-pointer transition-colors border border-transparent hover:border-zinc-700">
              <div className="text-sm font-medium text-zinc-200 group-hover:text-amber-400 transition-colors">{note.title}</div>
              <div className="flex gap-2 mt-1">
                {note.tags.map((tag) => (
                  <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-zinc-800 text-zinc-400 rounded-sm">#{tag}</span>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}
    </HudCard>
  );
}