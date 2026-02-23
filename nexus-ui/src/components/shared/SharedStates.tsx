import { AlertCircle, RefreshCw } from 'lucide-react';

export function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-6 text-center text-zinc-400 space-y-3">
      <AlertCircle className="w-8 h-8 text-red-500/80" />
      <p className="text-sm">{error.message}</p>
      <button 
        onClick={onRetry}
        className="flex items-center gap-2 px-3 py-1.5 text-xs bg-zinc-800 hover:bg-zinc-700 rounded-md transition-colors text-zinc-300"
      >
        <RefreshCw className="w-3 h-3" /> Tentar novamente
      </button>
    </div>
  );
}

export function EmptyState({ icon: Icon, message }: { icon: any; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-6 text-center text-zinc-500 space-y-3">
      <Icon className="w-8 h-8 opacity-50" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

export function SkeletonItem() {
  return <div className="h-10 w-full bg-zinc-800/50 animate-pulse rounded-md" />;
}