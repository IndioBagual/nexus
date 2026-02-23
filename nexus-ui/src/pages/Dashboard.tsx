import { ChronosHUD } from '../features/dashboard/ChronosHUD';
import { TreasuryHUD } from '../features/dashboard/TreasuryHUD';
import { RPGHUD } from '../features/dashboard/RPGHUD';
import { LibraryHUD } from '../features/dashboard/LibraryHUD';

export default function Dashboard() {
  return (
    <div className="h-full flex flex-col space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-100">Cockpit do Sistema</h1>
        <p className="text-zinc-500 text-sm mt-1">Visão geral da sua soberania operacional.</p>
      </div>

      {/* BENTO GRID */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-6 flex-1 auto-rows-min">
        {/* Linha 1 */}
        <div className="lg:col-span-8">
          <ChronosHUD />
        </div>
        <div className="lg:col-span-4">
          <TreasuryHUD />
        </div>
        
        {/* Linha 2 */}
        <div className="lg:col-span-5">
          <RPGHUD />
        </div>
        <div className="lg:col-span-7">
          <LibraryHUD />
        </div>
      </div>
    </div>
  );
}