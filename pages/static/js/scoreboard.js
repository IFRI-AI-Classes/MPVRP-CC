const API_URL = window.APP_CONFIG?.API_URL;

// ── Init ─────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard();
});

// ── Leaderboard ──────────────────────────────────────────
async function loadLeaderboard() {
    const stateEl   = document.getElementById('lb-state');
    const tableEl   = document.getElementById('leaderboard-table');
    const tbody     = document.getElementById('leaderboard-body');
    const countEl   = document.getElementById('lb-count');
    const refreshBtn = document.getElementById('refresh-btn');

    stateEl.className   = 'lb-state';
    stateEl.innerText   = 'Loading…';
    stateEl.style.display = 'block';
    tableEl.style.display = 'none';
    refreshBtn.disabled = true;

    try {
        const res = await fetch(`${API_URL}/scoreboard`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();

        if (data.length === 0) {
            stateEl.innerText = "No submissions recorded yet. Be the first team on the leaderboard!";
            countEl.innerText = '';
            return;
        }

        const medals = { 1: '🥇', 2: '🥈', 3: '🥉' };

        tbody.replaceChildren(...data.map(row => {
            const tr = document.createElement('tr');
            tr.className = row.rank <= 3 ? 'bg-blue-50/40' : 'hover:bg-slate-50';
            [medals[row.rank] ?? row.rank, row.team, Number(row.score).toFixed(2), row.instances_validated, formatDate(row.last_submission)]
                .forEach((value, index) => {
                    const td = document.createElement('td');
                    td.className = `px-6 py-4 ${index === 2 ? 'font-semibold text-slate-950' : ''}`;
                    td.textContent = String(value);
                    tr.appendChild(td);
                });
            return tr;
        }));

        countEl.innerText = `${data.length} Team${data.length > 1 ? 's' : ''} on the scoreboard`;
        stateEl.style.display = 'none';
        tableEl.style.display = 'table';

    } catch (err) {
        stateEl.className = 'p-10 text-center text-red-600';
        stateEl.innerText = "Unable to load leaderboard. Check the server is reachable.";
        console.error('Leaderboard error:', err);
    } finally {
        refreshBtn.disabled = false;
    }
}

function formatDate(isoStr) {
    if (!isoStr) return '—';

    try {
        const d = new Date(isoStr);
        if (isNaN(d.getTime())) return isoStr;

        const months = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'];
        const month = months[d.getUTCMonth()];
        const day = d.getUTCDate();
        const year = d.getUTCFullYear();

        let hours = d.getUTCHours();
        const minutes = String(d.getUTCMinutes()).padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;

        return `${month} ${day}, ${year} ${hours}:${minutes} ${ampm} (UTC)`;
    } catch (err) {
        return isoStr;
    }
}
