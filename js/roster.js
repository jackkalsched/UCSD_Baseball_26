// ─── Access control ───────────────────────────────────────────────────────────
function initRoster() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    if (!user) {
        window.location.href = getBaseUrl() + 'login.html';
        return;
    }
    if (user.role === 'player') {
        // Roster is coach/analyst only — send players home
        window.location.href = getBaseUrl() + 'index.html';
        return;
    }

    fetch(getBaseUrl() + 'data/roster.json')
        .then(r => { if (!r.ok) throw new Error('Roster data not found.'); return r.json(); })
        .then(data => renderRoster(data.players))
        .catch(err => {
            document.getElementById('roster-loading').classList.add('hidden');
            const el = document.getElementById('roster-error');
            el.classList.remove('hidden');
            el.textContent = err.message;
        });
}

// ─── Position cleanup (handles messy scraper output) ─────────────────────────
function cleanPosition(raw) {
    if (!raw) return '';
    // Strip height: 5'11", 6'2", etc.
    let p = raw.replace(/\d['']\d{1,2}["""]?/g, '').trim().replace(/\s+/g, ' ');
    // Remove duplicated prefix: "INF/OFINF/OF" → "INF/OF"
    for (let len = 1; len <= Math.floor(p.length / 2); len++) {
        if (p.slice(0, len) === p.slice(len, len * 2)) return p.slice(0, len);
    }
    return p;
}

function isPitcher(rawPosition) {
    const p = rawPosition.toUpperCase();
    return p.includes('RHP') || p.includes('LHP')
        || /(?:^|\/)SP(?:\/|$)/.test(p)
        || /(?:^|\/)RP(?:\/|$)/.test(p)
        || p === 'P';
}

// ─── UI helpers ───────────────────────────────────────────────────────────────
function playerInitials(name) {
    return name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();
}

const AVATAR_COLORS = [
    '#1a6b9e','#2d7a4f','#7a2d4f','#4f2d7a','#7a4f2d',
    '#1e5c7a','#5c3317','#17405c','#3d5c17','#5c1740'
];
function avatarColor(name) {
    let h = 0;
    for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
    return AVATAR_COLORS[h % AVATAR_COLORS.length];
}

function playerCard(p, cleanPos) {
    const analyticsPage = isPitcher(p.position)
        ? `pitcher_analytics.html?player=${encodeURIComponent(p.id)}`
        : `player_analytics.html?player=${encodeURIComponent(p.id)}`;

    const photoHtml = p.photo_url
        ? `<img src="${p.photo_url}" alt="${p.name}" class="roster-photo"
                onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
           <div class="roster-avatar" style="background:${avatarColor(p.name)};display:none;">${playerInitials(p.name)}</div>`
        : `<div class="roster-avatar" style="background:${avatarColor(p.name)};">${playerInitials(p.name)}</div>`;

    return `
        <div class="roster-card glass-panel">
            <div class="roster-photo-wrap">
                ${photoHtml}
                ${p.number ? `<span class="roster-number">#${p.number}</span>` : ''}
            </div>
            <div class="roster-card-info">
                <a href="${analyticsPage}" class="roster-name">${p.name}</a>
                <div class="roster-meta">
                    <span class="roster-position">${cleanPos}</span>
                    ${p.year ? `<span class="roster-year">${p.year}</span>` : ''}
                </div>
            </div>
        </div>`;
}

// ─── Render ───────────────────────────────────────────────────────────────────
function renderRoster(players) {
    document.getElementById('roster-loading').classList.add('hidden');

    // Clean position and recompute pitcher/hitter from position (overrides JSON type)
    const enriched = players.map(p => ({
        ...p,
        _cleanPos: cleanPosition(p.position),
        _isPitcher: isPitcher(p.position),
    }));

    const hitters  = enriched.filter(p => !p._isPitcher);
    const pitchers = enriched.filter(p =>  p._isPitcher);

    const render = (list, containerId) => {
        const el = document.getElementById(containerId);
        if (!list.length) { el.closest('.roster-section').classList.add('hidden'); return; }
        el.innerHTML = list
            .sort((a, b) => (parseInt(a.number) || 99) - (parseInt(b.number) || 99))
            .map(p => playerCard(p, p._cleanPos))
            .join('');
    };

    render(hitters,  'hitters-grid');
    render(pitchers, 'pitchers-grid');
    document.getElementById('roster-content').classList.remove('hidden');
}
