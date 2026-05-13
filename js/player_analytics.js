let rawPitchData = [];
let currentBatterHand = 'R';
let rawSchedule = [];

const MONTH_MAP = {
    Jan:'01', Feb:'02', Mar:'03', Apr:'04', May:'05', Jun:'06',
    Jul:'07', Aug:'08', Sep:'09', Oct:'10', Nov:'11', Dec:'12'
};

function scheduleIsoDate(dateStr) {
    const m = dateStr.match(/([A-Za-z]+) (\d+)/);
    if (!m) return null;
    const mo = MONTH_MAP[m[1]];
    return mo ? `2026-${mo}-${m[2].padStart(2, '0')}` : null;
}

function initAnalytics() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    if (!user) return;

    // Coaches can view any player via ?player= URL param.
    // Players are always locked to their own data — strip any ?player= param if it doesn't match.
    const params      = new URLSearchParams(window.location.search);
    const paramPlayer = params.get('player');
    const isCoach     = user.role !== 'player';

    if (!isCoach && paramPlayer && paramPlayer !== user.userId) {
        // Player trying to view someone else's page — redirect to their own (no param)
        window.location.replace('player_analytics.html');
        return;
    }

    const userId = (isCoach && paramPlayer) ? paramPlayer : user.userId;

    document.getElementById('analytics-title').textContent = `${userId}'s Analytics`;

    // Show "Back to Roster" only when a coach is viewing a specific player
    if (isCoach && paramPlayer) {
        const backBtn = document.getElementById('back-to-roster');
        if (backBtn) backBtn.classList.remove('hidden');
    }

    fetchData(userId);

    ['pitcherHandFilter', 'pitchTypeFilter', 'countFilter', 'dateFrom', 'dateTo']
        .forEach(id => document.getElementById(id).addEventListener('change', updateDash));

    document.getElementById('gameSelector').addEventListener('change', e => {
        const iso = e.target.value;
        const from = document.getElementById('dateFrom');
        const to   = document.getElementById('dateTo');
        if (iso) {
            from.value = iso;
            to.value   = iso;
        } else {
            const dates = rawPitchData.map(p => p.GameDate).filter(Boolean).sort();
            if (dates.length) { from.value = dates[0]; to.value = dates[dates.length - 1]; }
        }
        renderBoxScore(iso);
        updateDash();
    });
}

function fetchData(userId) {
    const safeName = userId.replace(/[^a-zA-Z0-9 ]/g, "").trim();
    const playerUrl   = getBaseUrl() + `data/hitters/${safeName}.json`;
    const scheduleUrl = getBaseUrl() + 'data/schedule.json';

    Promise.all([
        fetch(playerUrl).then(r => { if (!r.ok) throw new Error("Data not found for this player. Ensure the Python pipeline has run."); return r.json(); }),
        fetch(scheduleUrl).then(r => r.json()).catch(() => ({ games: [] }))
    ])
    .then(([data, schedule]) => {
        rawPitchData    = data.pitches;
        currentBatterHand = data.hand || 'R';
        rawSchedule     = schedule.games || [];

        const dates = rawPitchData.map(p => p.GameDate).filter(Boolean).sort();
        if (dates.length) {
            const from = document.getElementById('dateFrom');
            const to   = document.getElementById('dateTo');
            from.min = to.min = dates[0];
            from.max = to.max = dates[dates.length - 1];
            from.value = dates[0];
            to.value   = dates[dates.length - 1];
        }

        populateGameSelector();
        document.getElementById('loading-state').classList.add('hidden');
        document.getElementById('analytics-content').classList.remove('hidden');
        renderRollingChart(rawPitchData);
        updateDash();
    })
    .catch(err => {
        document.getElementById('loading-state').classList.add('hidden');
        const errDiv = document.getElementById('error-state');
        errDiv.classList.remove('hidden');
        errDiv.textContent = err.message;
    });
}

function populateGameSelector() {
    const sel = document.getElementById('gameSelector');
    if (!sel) return;
    while (sel.options.length > 1) sel.remove(1);

    const pitchDates = new Set(rawPitchData.map(p => p.GameDate).filter(Boolean));

    rawSchedule
        .filter(g => g.status === 'completed')
        .forEach(g => {
            const iso = scheduleIsoDate(g.date);
            if (!iso || !pitchDates.has(iso)) return;
            const ha  = g.home_away === 'away' ? '@' : 'vs';
            const opp = g.opponent.replace(/^#\d+\s*/, '');
            const res = g.result ? `  ·  ${g.result}` : '';
            const label = `${g.date.replace(/ \(\w+\)/, '')}  ${ha} ${opp}${res}`;
            sel.appendChild(new Option(label, iso));
        });
}

function renderBoxScore(isoDate) {
    const section = document.getElementById('box-score-section');
    const tbody   = document.getElementById('box-score-body');
    const titleEl = document.getElementById('box-score-title');

    if (!isoDate) { section.classList.add('hidden'); return; }

    const pitches = rawPitchData.filter(p => p.GameDate === isoDate);
    if (!pitches.length) { section.classList.add('hidden'); return; }

    // Game label from schedule
    const game = rawSchedule.find(g => scheduleIsoDate(g.date) === isoDate);
    if (game && titleEl) {
        const ha  = game.home_away === 'away' ? '@' : 'vs';
        const opp = game.opponent.replace(/^#\d+\s*/, '');
        titleEl.textContent = `${game.date.replace(/ \(\w+\)/, '')}  ${ha} ${opp}${game.result ? '  ·  ' + game.result : ''}`;
    }

    let AB = 0, H = 0, doubles = 0, triples = 0, HR = 0, totalBases = 0, BB = 0, K = 0;
    let xwobaSum = 0, xwobaCount = 0;

    pitches.forEach(p => {
        const pr  = (p.PlayResult || '').toLowerCase();
        const kbb = (p.KorBB     || '').toLowerCase();
        if (pr.includes('walk') || kbb.includes('walk')) {
            BB++;
        } else if (pr.includes('strikeout') || kbb.includes('strikeout')) {
            K++; AB++;
        } else {
            const bases = getBases(p.PlayResult);
            if (bases >= 0) {
                AB++;
                if (bases > 0) H++;
                if (bases === 2) doubles++;
                if (bases === 3) triples++;
                if (bases === 4) HR++;
                totalBases += bases;
            }
        }
        const xw = getExpectedwOBA(p);
        if (xw !== null) { xwobaSum += xw; xwobaCount++; }
    });

    const stat = (num, den, dec) =>
        den > 0 ? (num / den).toFixed(dec).replace(/^0\./, '.') : '---';

    tbody.innerHTML = `<tr>
        <td>${AB}</td>
        <td>${H}</td>
        <td>${doubles}</td>
        <td>${triples}</td>
        <td>${HR}</td>
        <td>${BB}</td>
        <td>${K}</td>
        <td>${stat(H, AB, 3)}</td>
        <td>${stat(totalBases, AB, 3)}</td>
        <td>${xwobaCount > 0 ? stat(xwobaSum, xwobaCount, 3) : '---'}</td>
    </tr>`;

    section.classList.remove('hidden');
}

function updateDash() {
    const pHand    = document.getElementById('pitcherHandFilter').value;
    const pType    = document.getElementById('pitchTypeFilter').value;
    const count    = document.getElementById('countFilter').value;
    const dateFrom = document.getElementById('dateFrom').value;
    const dateTo   = document.getElementById('dateTo').value;

    const filtered = rawPitchData.filter(p => {
        if (pHand !== 'All' && p.PitcherHand !== pHand) return false;

        if (pType !== 'All') {
            const t = p.PitchType ? p.PitchType.toLowerCase() : '';
            if (pType === 'Fastball' && !['fastball','sinker','cutter','four-seam','two-seam'].some(x => t.includes(x))) return false;
            if (pType === 'Offspeed' && !['changeup','splitter'].some(x => t.includes(x))) return false;
            if (pType === 'Breaking' && !['slider','curveball','sweeper','slurve'].some(x => t.includes(x))) return false;
        }

        if (dateFrom && p.GameDate && p.GameDate < dateFrom) return false;
        if (dateTo   && p.GameDate && p.GameDate > dateTo)   return false;

        if (count !== 'All') {
            const [cb, cs] = count.split('-').map(Number);
            if ((parseInt(p.Balls) || 0) !== cb || (parseInt(p.Strikes) || 0) !== cs) return false;
        }

        return true;
    });

    renderHeatmaps(filtered);
    renderRollingChart(filtered);
}

// 5x5 grid boundaries (used for zone box coords)
const x_edges = [-3.0, -0.83, -0.27, 0.27, 0.83, 3.0];
const y_edges = [0.0, 1.5, 2.16, 2.83, 3.5, 5.0];

function getBases(result) {
    if (!result) return -1;
    const r = result.toLowerCase();
    if (r.includes('home')) return 4;
    if (r.includes('triple')) return 3;
    if (r.includes('double')) return 2;
    if (r.includes('single')) return 1;
    if (r.includes('out') || r.includes('error') || r.includes('fielderschoice')) return 0;
    return -1;
}

function getExpectedwOBA(p) {
    if (p.xwOBA !== undefined && p.xwOBA !== null) return parseFloat(p.xwOBA);
    // Fallback: league-average xwOBA by outcome (normalized 0–1 scale, 2024 MLB weights)
    const bases = getBases(p.PlayResult);
    if (bases === 4) return 0.890; // HR
    if (bases === 3) return 0.750; // Triple
    if (bases === 2) return 0.500; // Double
    if (bases === 1) return 0.280; // Single
    if (bases === 0) return 0.000; // Out
    if (p.KorBB && p.KorBB.toLowerCase().includes('walk'))      return 0.290;
    if (p.KorBB && p.KorBB.toLowerCase().includes('strikeout')) return 0.000;
    return null;
}

// ─── Heatmap rendering ────────────────────────────────────────────────────────

// D1 college baseball percentile benchmarks:
//   SLG  — 0.200 (0th %ile, cold) | ~0.550 D1 avg (midpoint, yellow) | 0.900 (100th %ile, hot)
//   xwOBA — 0.250 (0th %ile) | ~0.375 D1 avg | 0.500 (100th %ile)
const D1_SCALE = {
    SLG:   { min: 0.200, max: 0.900 },
    xwOBA: { min: 0.250, max: 0.500 }
};

function renderHeatmaps(data) {
    plotHeatmap('slg-heatmap',   data, p => { const b = getBases(p.PlayResult); return b >= 0 ? b : null; }, 'SLG',   D1_SCALE.SLG.min, D1_SCALE.SLG.max);
    plotHeatmap('xwoba-heatmap', data, p => getExpectedwOBA(p),                                              'xwOBA', D1_SCALE.xwOBA.min, D1_SCALE.xwOBA.max);
}

function plotHeatmap(containerId, pitches, valueFunc, metricLabel, fixedMin, fixedMax) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    // Coordinate range matched to actual pitch data extent (±1.5 ft typical).
    // Extends slightly beyond so the kernel fades naturally at the edges.
    // y range includes plate area below y=0 and room above the zone top.
    const xMin = -2.0, xMax = 2.0; // 4 ft — zone takes up ~42% of width
    const yMin = -0.3, yMax = 5.1; // 5.4 ft — plate at bottom, small padding above

    const pxFt = 90;
    const DW      = Math.round((xMax - xMin) * pxFt); // 360
    const DH_leg  = 82;
    const DH_map  = Math.round((yMax - yMin) * pxFt); // 486
    const DH      = DH_leg + DH_map;

    const canvas = document.createElement('canvas');
    canvas.width = DW; canvas.height = DH;
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    canvas.style.display = 'block';
    canvas.style.borderRadius = '6px';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    const toX = fx => (fx - xMin) / (xMax - xMin) * DW;
    const toY = fy => DH_leg + (1 - (fy - yMin) / (yMax - yMin)) * DH_map;

    ctx.clearRect(0, 0, DW, DH);

    // Rulebook zone edges (ft): x ±0.83, y 1.5–3.5. Exclude pitches more than 1 ft outside.
    const CUTOFF = 1.0;
    const zoneXlo = x_edges[1] - CUTOFF, zoneXhi = x_edges[4] + CUTOFF; // -1.83 to 1.83
    const zoneYlo = y_edges[1] - CUTOFF, zoneYhi = y_edges[4] + CUTOFF; // 0.5  to 4.5

    const pts = [];
    pitches.forEach(p => {
        const x = parseFloat(p.PlateLocSide);
        const y = parseFloat(p.PlateLocHeight);
        const v = valueFunc(p);
        if (isNaN(x) || isNaN(y) || v === null) return;
        if (x < zoneXlo || x > zoneXhi || y < zoneYlo || y > zoneYhi) return;
        pts.push({ x, y, v });
    });

    if (pts.length > 0) {
        const minVal = fixedMin;
        const maxVal = fixedMax;

        // Kernel regression over full display range.
        // Alpha uses the MAX single-pitch kernel weight at each point — transparency
        // is independent of pitch count, fading naturally where no pitch was thrown.
        const GW = 100, GH = 100;
        const bw       = 0.15;  // bandwidth (ft) — compact blobs, clear hot/cold spots
        const alphaRef = 0.42;  // max-weight threshold for full opacity

        const off = document.createElement('canvas');
        off.width = GW; off.height = GH;
        const offCtx = off.getContext('2d');
        const imgData = offCtx.createImageData(GW, GH);

        for (let gy = 0; gy < GH; gy++) {
            const fy = yMax - (gy + 0.5) / GH * (yMax - yMin);
            for (let gx = 0; gx < GW; gx++) {
                const fx = xMin + (gx + 0.5) / GW * (xMax - xMin);
                let wSum = 0, wTot = 0, wMax = 0;
                for (const p of pts) {
                    const dx = (fx - p.x) / bw;
                    const dy = (fy - p.y) / bw;
                    const w = Math.exp(-0.5 * (dx * dx + dy * dy));
                    if (w > wMax) wMax = w;
                    wSum += w * p.v;
                    wTot += w;
                }
                const idx = (gy * GW + gx) * 4;
                // sqrt gives a smooth, gradual fade rather than a hard edge
                const alpha = Math.round(Math.sqrt(Math.min(1, wMax / alphaRef)) * 255);
                if (alpha < 3) {
                    imgData.data[idx + 3] = 0;
                } else {
                    const t = maxVal > minVal
                        ? Math.max(0, Math.min(1, (wSum / wTot - minVal) / (maxVal - minVal)))
                        : 0.5;
                    const [r, g, b] = heatRgb(t);
                    imgData.data[idx]     = r;
                    imgData.data[idx + 1] = g;
                    imgData.data[idx + 2] = b;
                    imgData.data[idx + 3] = alpha;
                }
            }
        }
        offCtx.putImageData(imgData, 0, 0);

        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(off, 0, DH_leg, DW, DH_map);

        drawLegend(ctx, DW, DH_leg, metricLabel, fixedMin, fixedMax, pts.length);
    }

    // Chase zone — dashed white
    ctx.strokeStyle = 'rgba(255,255,255,0.5)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 5]);
    ctx.strokeRect(toX(-1.2), toY(4.0), toX(1.2) - toX(-1.2), toY(1.0) - toY(4.0));

    // Strike zone — solid white
    ctx.setLineDash([]);
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 2.5;
    ctx.strokeRect(
        toX(x_edges[1]), toY(y_edges[4]),
        toX(x_edges[4]) - toX(x_edges[1]),
        toY(y_edges[1]) - toY(y_edges[4])
    );

    // Home plate — drawn last so it sits on top of any fade-out heatmap
    drawHomePlate(ctx, toX, toY);
}

function heatRgb(t) {
    // Blue → cyan → yellow → orange → red (no green — matches TruMedia/Savant style).
    // Yellow at t=0.50 = D1 average; cold below, hot above.
    const stops = [
        [0.00, [  0,   0, 160]],
        [0.17, [  0,  90, 255]],
        [0.33, [  0, 220, 255]],
        [0.50, [255, 255,   0]],
        [0.67, [255, 160,   0]],
        [0.83, [255,  20,   0]],
        [1.00, [255,   0,   0]]
    ];
    for (let i = 0; i < stops.length - 1; i++) {
        if (t <= stops[i + 1][0]) {
            const f = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0]);
            return stops[i][1].map((v, j) => Math.round(v + f * (stops[i + 1][1][j] - v)));
        }
    }
    return [160, 0, 0];
}

function drawLegend(ctx, DW, legendH, metricLabel, minVal, maxVal, pitchCount) {
    const padX = DW * 0.12;
    const barW = DW * 0.76;
    const barX = padX;
    const barY = legendH * 0.38;
    const barH = 15;

    // Metric label + pitch count
    ctx.fillStyle = '#ddd';
    ctx.font = `bold ${Math.round(legendH * 0.22)}px Inter, Arial, sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText(metricLabel, DW / 2, legendH * 0.26);
    if (pitchCount != null) {
        ctx.fillStyle = '#888';
        ctx.font = `${Math.round(legendH * 0.14)}px Inter, Arial, sans-serif`;
        ctx.textAlign = 'right';
        ctx.fillText(`n = ${pitchCount}`, DW - 8, legendH * 0.28);
    }

    // Gradient bar — matches heatRgb colorscale
    const grad = ctx.createLinearGradient(barX, 0, barX + barW, 0);
    grad.addColorStop(0.00, 'rgb(0,0,160)');
    grad.addColorStop(0.17, 'rgb(0,90,255)');
    grad.addColorStop(0.33, 'rgb(0,220,255)');
    grad.addColorStop(0.50, 'rgb(255,255,0)');
    grad.addColorStop(0.67, 'rgb(255,160,0)');
    grad.addColorStop(0.83, 'rgb(255,20,0)');
    grad.addColorStop(1.00, 'rgb(255,0,0)');
    ctx.fillStyle = grad;
    ctx.fillRect(barX, barY, barW, barH);

    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    ctx.strokeRect(barX, barY, barW, barH);

    // Row 1: raw values
    const midVal = (minVal + maxVal) / 2;
    const valFontSz = Math.round(legendH * 0.17);
    ctx.fillStyle = '#ccc';
    ctx.font = `${valFontSz}px Inter, Arial, sans-serif`;
    ctx.textAlign = 'left';   ctx.fillText(minVal.toFixed(3), barX,            barY + barH + valFontSz + 2);
    ctx.textAlign = 'center'; ctx.fillText(midVal.toFixed(3), barX + barW / 2, barY + barH + valFontSz + 2);
    ctx.textAlign = 'right';  ctx.fillText(maxVal.toFixed(3), barX + barW,     barY + barH + valFontSz + 2);

    // Row 2: D1 percentile labels
    const pctFontSz = Math.round(legendH * 0.14);
    ctx.fillStyle = '#888';
    ctx.font = `${pctFontSz}px Inter, Arial, sans-serif`;
    ctx.textAlign = 'left';   ctx.fillText('0th %ile',   barX,            barY + barH + valFontSz + pctFontSz + 4);
    ctx.textAlign = 'center'; ctx.fillText('D1 Avg',     barX + barW / 2, barY + barH + valFontSz + pctFontSz + 4);
    ctx.textAlign = 'right';  ctx.fillText('100th %ile', barX + barW,     barY + barH + valFontSz + pctFontSz + 4);
}

function drawHomePlate(ctx, toX, toY) {
    const hw = 0.71;
    ctx.beginPath();
    ctx.moveTo(toX(-hw), toY(0.17));
    ctx.lineTo(toX( hw), toY(0.17));
    ctx.lineTo(toX( hw), toY(0));
    ctx.lineTo(toX(0),   toY(-0.22));
    ctx.lineTo(toX(-hw), toY(0));
    ctx.closePath();
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.strokeStyle = 'rgba(255,255,255,0.4)';
    ctx.lineWidth = 1.5; ctx.setLineDash([]);
    ctx.fill(); ctx.stroke();
}

// ─── Rolling chart ────────────────────────────────────────────────────────────

function renderRollingChart(data) {
    let sorted = [...data].sort((a, b) => new Date(a.GameDate || 0) - new Date(b.GameDate || 0));

    let gamesMap = new Map();
    let allDatesSet = new Set();
    let allPitchTypes = new Set();

    sorted.forEach(p => {
        if (!p.GameDate) return;
        const xwoba = getExpectedwOBA(p);
        const pType = p.PitchType || 'Unknown';
        if (xwoba !== null) {
            allDatesSet.add(p.GameDate);
            allPitchTypes.add(pType);
            if (!gamesMap.has(p.GameDate)) gamesMap.set(p.GameDate, {});
            let dayData = gamesMap.get(p.GameDate);
            if (!dayData[pType]) dayData[pType] = [];
            dayData[pType].push(xwoba);
        }
    });

    let dates = Array.from(allDatesSet).sort((a,b) => new Date(a) - new Date(b));
    let pitchTypes = Array.from(allPitchTypes);
    let traces = [];
    let colors = ['#e6194b','#3cb44b','#ffe119','#4363d8','#f58231','#911eb4','#46f0f0','#f032e6','#bcf60c','#fabebe'];
    let colorIdx = 0;

    pitchTypes.forEach(pType => {
        let rollingX = [], rollingY = [];
        for (let i = 0; i < dates.length; i++) {
            let start = Math.max(0, i - 4);
            let sum = 0, count = 0;
            for (let j = start; j <= i; j++) {
                let dayData = gamesMap.get(dates[j]);
                if (dayData && dayData[pType] && dayData[pType].length > 0) {
                    sum += dayData[pType].reduce((a,b)=>a+b, 0) / dayData[pType].length;
                    count++;
                }
            }
            rollingX.push(dates[i]);
            rollingY.push(count > 0 ? sum / count : null);
        }
        traces.push({
            x: rollingX, y: rollingY, name: pType,
            type: 'scatter', mode: 'lines+markers', connectgaps: true,
            line: { width: 3, color: colors[colorIdx % colors.length] },
            marker: { size: 8 }
        });
        colorIdx++;
    });

    Plotly.newPlot('rolling-chart', traces, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor:  'rgba(0,0,0,0)',
        font: { color: '#ccc' },
        xaxis: { title: 'Game Date', gridcolor: 'rgba(255,255,255,0.1)', zeroline: false },
        yaxis: { title: 'Rolling xwOBA', gridcolor: 'rgba(255,255,255,0.1)', zeroline: false },
        margin: { t: 20, l: 50, r: 20, b: 50 },
        legend: { orientation: 'h', y: -0.2, font: { color: 'white' } }
    }, { displayModeBar: false });
}
