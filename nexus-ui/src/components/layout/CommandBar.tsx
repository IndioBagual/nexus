import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Command } from 'cmdk';
import { LayoutDashboard, CheckSquare, Wallet, Shield, BookOpen, Search, FileText } from 'lucide-react';
import { useDebounce } from '../../hooks/useDebounce';
import { dataAccessClient } from '../../lib/dataAccessClient';

export function CommandBar() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  
  // Regra: Debounce de 300ms
  const debouncedSearch = useDebounce(search, 300);

  // Toggle com Cmd+K ou Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  // Busca na API apenas se houver texto
  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['library', 'search', debouncedSearch],
    queryFn: () => dataAccessClient.searchLibraryNotes(debouncedSearch),
    enabled: debouncedSearch.length > 1, // Só busca se tiver mais de 1 letra
  });

  const runCommand = (command: () => void) => {
    setOpen(false);
    command();
    setSearch('');
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-zinc-950/80 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-zinc-950 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden">
        <Command 
          className="w-full" 
          loop 
          shouldFilter={false} // Desativamos o filtro local do cmdk para usar o filtro da API nas notas
        >
          <div className="flex items-center px-4 border-b border-zinc-800">
            <Search className="w-5 h-5 text-zinc-500 mr-2" />
            <Command.Input 
              value={search}
              onValueChange={setSearch}
              autoFocus
              placeholder="Digite um comando ou busque no Cérebro Digital..." 
              className="flex-1 h-14 bg-transparent text-zinc-100 placeholder:text-zinc-500 focus:outline-none"
            />
            <button onClick={() => setOpen(false)} className="text-xs text-zinc-500 px-2 py-1 bg-zinc-900 rounded border border-zinc-800">ESC</button>
          </div>

          <Command.List className="max-h-[60vh] overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-zinc-500">
              {isLoading ? 'Buscando no Córtex...' : 'Nenhum resultado encontrado.'}
            </Command.Empty>

            {/* SEÇÃO 1: Navegação (Sempre visível se não estiver pesquisando especificamente algo que retornou na API) */}
            {(!debouncedSearch || (!isLoading && searchResults?.notes.length === 0)) && (
              <Command.Group heading="Navegação" className="text-xs font-medium text-zinc-500 px-2 py-2">
                <Command.Item onSelect={() => runCommand(() => navigate('/dashboard'))} className="flex items-center gap-2 px-2 py-3 mt-1 text-sm text-zinc-200 rounded-md cursor-pointer aria-selected:bg-emerald-500/10 aria-selected:text-emerald-400 data-[selected=true]:bg-emerald-500/10 data-[selected=true]:text-emerald-400 transition-colors">
                  <LayoutDashboard className="w-4 h-4" /> Ir para Dashboard
                </Command.Item>
                <Command.Item onSelect={() => runCommand(() => navigate('/chronos'))} className="flex items-center gap-2 px-2 py-3 text-sm text-zinc-200 rounded-md cursor-pointer data-[selected=true]:bg-emerald-500/10 data-[selected=true]:text-emerald-400 transition-colors">
                  <CheckSquare className="w-4 h-4" /> Ir para Chronos
                </Command.Item>
                <Command.Item onSelect={() => runCommand(() => navigate('/treasury'))} className="flex items-center gap-2 px-2 py-3 text-sm text-zinc-200 rounded-md cursor-pointer data-[selected=true]:bg-emerald-500/10 data-[selected=true]:text-emerald-400 transition-colors">
                  <Wallet className="w-4 h-4" /> Ir para Treasury
                </Command.Item>
                <Command.Item onSelect={() => runCommand(() => navigate('/rpg'))} className="flex items-center gap-2 px-2 py-3 text-sm text-zinc-200 rounded-md cursor-pointer data-[selected=true]:bg-emerald-500/10 data-[selected=true]:text-emerald-400 transition-colors">
                  <Shield className="w-4 h-4" /> Ir para RPG
                </Command.Item>
                <Command.Item onSelect={() => runCommand(() => navigate('/library'))} className="flex items-center gap-2 px-2 py-3 text-sm text-zinc-200 rounded-md cursor-pointer data-[selected=true]:bg-emerald-500/10 data-[selected=true]:text-emerald-400 transition-colors">
                  <BookOpen className="w-4 h-4" /> Ir para Library
                </Command.Item>
              </Command.Group>
            )}

            {/* SEÇÃO 2: Resultados da Busca no Cérebro Digital */}
            {debouncedSearch.length > 1 && searchResults && searchResults.notes.length > 0 && (
              <Command.Group heading="Resultados do Zettelkasten" className="text-xs font-medium text-zinc-500 px-2 py-2 mt-2 border-t border-zinc-800/50 pt-4">
                {searchResults.notes.map((note) => (
                  <Command.Item 
                    key={note.id} 
                    onSelect={() => runCommand(() => navigate(`/library?noteId=${note.id}`))} 
                    className="flex items-center justify-between gap-2 px-2 py-3 mt-1 text-sm text-zinc-200 rounded-md cursor-pointer data-[selected=true]:bg-amber-500/10 data-[selected=true]:text-amber-400 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 opacity-70" />
                      <span>{note.title}</span>
                    </div>
                    <div className="flex gap-1">
                      {note.tags.map(tag => (
                        <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-zinc-800/50 text-zinc-400 rounded">#{tag}</span>
                      ))}
                    </div>
                  </Command.Item>
                ))}
              </Command.Group>
            )}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}