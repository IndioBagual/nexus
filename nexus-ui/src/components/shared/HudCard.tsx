export function HudCard({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div className="flex flex-col bg-zinc-900/40 border border-zinc-800 rounded-xl overflow-hidden shadow-sm h-full min-h-[300px]">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800 bg-zinc-900/80">
        <Icon className="w-4 h-4 text-zinc-400" />
        <h3 className="font-semibold text-sm tracking-wide text-zinc-200">{title}</h3>
      </div>
      <div className="flex-1 p-4 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}