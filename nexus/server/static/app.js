const API_BASE = '/api';

// Formatters
const formatCurrency = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
const formatDate = (str) => new Date(str).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });

async function loadChronos() {
    try {
        const res = await fetch(`${API_BASE}/chronos/today`);
        const tasks = await res.json();
        const container = document.getElementById('chronos-list');
        container.innerHTML = '';

        if (tasks.length === 0) {
            container.innerHTML = '<div class="text-slate-500 text-center py-10">All clear for today.</div>';
            return;
        }

        tasks.forEach(task => {
            const priorityColor = task.priority === 'high' ? 'border-red-500/50 text-red-100' : 'border-slate-600 text-slate-300';
            const html = `
                <div class="flex items-center justify-between p-3 rounded bg-slate-700/30 border-l-4 ${priorityColor} hover:bg-slate-700/50 transition">
                    <div>
                        <div class="font-medium">${task.title}</div>
                        <div class="text-xs text-slate-500">${task.due_date || 'No date'}</div>
                    </div>
                    <div class="text-xs uppercase bg-slate-800 px-2 py-1 rounded text-slate-400">${task.status}</div>
                </div>
            `;
            container.innerHTML += html;
        });
    } catch (e) { console.error("Chronos Error", e); }
}

async function loadTreasury() {
    try {
        const res = await fetch(`${API_BASE}/treasury/summary`);
        const data = await res.json();
        
        document.getElementById('treasury-total').innerText = formatCurrency(data.total_spent).replace('R$', '').trim();
        
        const catsContainer = document.getElementById('treasury-cats');
        catsContainer.innerHTML = '';
        data.top_categories.forEach(cat => {
            catsContainer.innerHTML += `
                <div class="flex justify-between items-center">
                    <span class="text-slate-400">${cat.category}</span>
                    <span class="font-mono text-white">${formatCurrency(cat.total)}</span>
                </div>
                <div class="w-full bg-slate-700 h-1 rounded-full mt-1 mb-2">
                    <div class="bg-emerald-500 h-1 rounded-full" style="width: ${cat.percent}%"></div>
                </div>
            `;
        });
    } catch (e) { console.error("Treasury Error", e); }
}

async function loadRPG() {
    try {
        const res = await fetch(`${API_BASE}/rpg/status`);
        const data = await res.json();
        
        document.getElementById('level-badge').innerText = `LVL ${data.player_level}`;
        
        const container = document.getElementById('rpg-stats');
        container.innerHTML = '';
        
        const attrs = ['STR', 'INT', 'WIS', 'CHA'];
        attrs.forEach(key => {
            const attr = data.attributes[key];
            const color = key === 'STR' ? 'bg-red-500' : key === 'INT' ? 'bg-blue-500' : key === 'WIS' ? 'bg-purple-500' : 'bg-yellow-500';
            
            container.innerHTML += `
                <div>
                    <div class="flex justify-between text-xs mb-1">
                        <span class="font-bold text-slate-300">${key} <span class="text-slate-500 font-normal">Lvl ${attr.level}</span></span>
                        <span class="text-slate-500">${attr.current_xp} / ${attr.next_level_xp} XP</span>
                    </div>
                    <div class="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div class="${color} h-2 rounded-full" style="width: ${attr.progress_percent}%"></div>
                    </div>
                </div>
            `;
        });
    } catch (e) { console.error("RPG Error", e); }
}

async function loadLibrary() {
    try {
        const res = await fetch(`${API_BASE}/library/notes?limit=5`);
        const notes = await res.json();
        const container = document.getElementById('library-list');
        container.innerHTML = '';

        notes.forEach(note => {
            container.innerHTML += `
                <div class="p-3 bg-slate-800/50 hover:bg-slate-700/50 rounded border border-slate-700/50 cursor-pointer transition flex justify-between items-center">
                    <div>
                        <div class="text-sm font-medium text-slate-200">${note.title}</div>
                        <div class="text-xs text-slate-500 flex gap-2 mt-1">
                            <span>${formatDate(note.created_at)}</span>
                            <span class="text-cyan-600">${note.tags.map(t=>'#'+t).join(' ')}</span>
                        </div>
                    </div>
                    <div class="text-slate-600">→</div>
                </div>
            `;
        });
    } catch (e) { console.error("Library Error", e); }
}

// Init
document.getElementById('date-display').innerText = new Date().toLocaleDateString('en-US', { weekday: 'long', day: 'numeric' });
loadChronos();
loadTreasury();
loadRPG();
loadLibrary();