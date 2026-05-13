let pitcherRawData   = null;
let pitcherRoster    = null;

function initPitcherAnalytics() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    if (!user) {
        window.location.href = getBaseUrl() + 'login.html';
        return;
    }
    if (user.role === 'player') {
        window.location.href = getBaseUrl() + 'index.html';
        return;
    }

    const params   = new URLSearchParams(window.location.search);
    const playerId = params.get('player') || user.userId;

    // Load roster + pitcher data in parallel
    Promise.all([
        fetch(getBaseUrl() + 'data/roster.json').then(r => r.json()).catch(() => ({ players: [] })),
        fetch(getBaseUrl() + `data/pitchers/${playerId}.json`).then(r => r.json()).catch(() => null)
    ]).then(([roster, pitcherData]) => {
        pitcherRoster  = roster.players.find(p => p.id === playerId) || { name: playerId, position: 'P' };
        pitcherRawData = pitcherData;

        document.getElementById('pitcher-title').textContent = `${pitcherRoster.name} — Pitching Analytics`;
        document.getElementById('pitcher-meta').textContent  =
            [pitcherRoster.position, pitcherRoster.year, pitcherRoster.hometown].filter(Boolean).join('  ·  ');

        if (pitcherData && pitcherData.pitches && pitcherData.pitches.length) {
            renderPitcherDash(pitcherData);
        } else {
            showEmptyState();
        }
    });
}

function showEmptyState() {
    document.getElementById('pitcher-loading').classList.add('hidden');
    document.getElementById('pitcher-empty').classList.remove('hidden');
    document.getElementById('pitcher-content').classList.add('hidden');
}

function renderPitcherDash(data) {
    document.getElementById('pitcher-loading').classList.add('hidden');
    document.getElementById('pitcher-content').classList.remove('hidden');

    renderSeasonStats(data);
    renderArsenal(data.pitches);
    renderGameLog(data.games || []);
}

// ─── Season summary ───────────────────────────────────────────────────────────
function renderSeasonStats(data) {
    const games  = data.games || [];
    const totals = games.reduce((a, g) => ({
        IP: a.IP + (g.IP || 0),
        ER: a.ER + (g.ER || 0),
        H:  a.H  + (g.H  || 0),
        BB: a.BB + (g.BB || 0),
        K:  a.K  + (g.K  || 0),
        HR: a.HR + (g.HR || 0),
    }), { IP: 0, ER: 0, H: 0, BB: 0, K: 0, HR: 0 });

    const ERA  = totals.IP > 0 ? ((totals.ER * 9) / totals.IP).toFixed(2)  : '—';
    const WHIP = totals.IP > 0 ? ((totals.BB + totals.H) / totals.IP).toFixed(2) : '—';
    const K9   = totals.IP > 0 ? ((totals.K  * 9) / totals.IP).toFixed(1)  : '—';
    const BB9  = totals.IP > 0 ? ((totals.BB * 9) / totals.IP).toFixed(1)  : '—';
    const H9   = totals.IP > 0 ? ((totals.H  * 9) / totals.IP).toFixed(1)  : '—';

    const stats = [
        { label: 'ERA',  value: ERA },
        { label: 'IP',   value: totals.IP % 1 === 0 ? totals.IP : totals.IP.toFixed(1) },
        { label: 'K',    value: totals.K },
        { label: 'BB',   value: totals.BB },
        { label: 'WHIP', value: WHIP },
        { label: 'K/9',  value: K9 },
        { label: 'BB/9', value: BB9 },
        { label: 'H/9',  value: H9 },
    ];

    document.getElementById('season-stats-grid').innerHTML = stats.map(s =>
        `<div class="stat-box">
            <div class="stat-value">${s.value}</div>
            <div class="stat-label">${s.label}</div>
         </div>`
    ).join('');
}

// ─── Pitch arsenal ────────────────────────────────────────────────────────────
function renderArsenal(pitches) {
    const byType = {};
    pitches.forEach(p => {
        const t = p.PitchType || p.TaggedPitchType || 'Unknown';
        if (!byType[t]) byType[t] = { velos: [], spins: [] };
        if (p.Velo   || p.RelSpeed)  byType[t].velos.push(p.Velo   || p.RelSpeed);
        if (p.SpinRate)               byType[t].spins.push(p.SpinRate);
    });

    const total = pitches.length;
    const rows  = Object.entries(byType)
        .sort((a, b) => b[1].velos.length - a[1].velos.length)
        .map(([type, d]) => {
            const avg   = arr => arr.length ? (arr.reduce((s,v)=>s+v,0)/arr.length).toFixed(1) : '—';
            const max   = arr => arr.length ? Math.max(...arr).toFixed(1) : '—';
            const usage = ((d.velos.length / total) * 100).toFixed(1);
            return `<tr>
                <td>${type}</td>
                <td>${avg(d.velos)}</td>
                <td>${max(d.velos)}</td>
                <td>${d.spins.length ? Math.round(d.spins.reduce((s,v)=>s+v,0)/d.spins.length) : '—'}</td>
                <td>${usage}%</td>
            </tr>`;
        }).join('');

    document.getElementById('arsenal-tbody').innerHTML = rows || '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">No pitch data</td></tr>';
}

// ─── Game log ─────────────────────────────────────────────────────────────────
function renderGameLog(games) {
    const container = document.getElementById('game-log-section');
    if (!games.length) { container.classList.add('hidden'); return; }

    const rows = [...games]
        .sort((a, b) => new Date(b.GameDate) - new Date(a.GameDate))
        .map(g => {
            const era = g.IP > 0 ? ((g.ER * 9) / g.IP).toFixed(2) : '—';
            return `<tr>
                <td>${g.GameDate || '—'}</td>
                <td>${g.Opponent || '—'}</td>
                <td>${g.IP != null ? g.IP : '—'}</td>
                <td>${g.H  ?? '—'}</td>
                <td>${g.R  ?? '—'}</td>
                <td>${g.ER ?? '—'}</td>
                <td>${g.BB ?? '—'}</td>
                <td>${g.K  ?? '—'}</td>
                <td>${era}</td>
            </tr>`;
        }).join('');

    document.getElementById('game-log-tbody').innerHTML = rows;
}
