let rawPitchData = [];

function initAnalytics() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    if (!user) return;
    
    // Default to the logged-in user, but if it's an analyst, they could theoretically view others.
    // For now, we fetch the current user's data.
    const userId = user.userId;
    document.getElementById('analytics-title').textContent = `${userId}'s Analytics`;

    fetchData(userId);
    
    // Add event listeners
    document.getElementById('pitcherHandFilter').addEventListener('change', updateDash);
    document.getElementById('pitchTypeFilter').addEventListener('change', updateDash);
    document.getElementById('countFilter').addEventListener('change', updateDash);
}

function fetchData(userId) {
    const safeName = userId.replace(/[^a-zA-Z0-9 ]/g, "").trim();
    // Use the repo path
    const url = getBaseUrl() + `data/hitters/${safeName}.json`;

    fetch(url)
        .then(res => {
            if (!res.ok) throw new Error("Data not found for this player. Ensure the Python pipeline has run.");
            return res.json();
        })
        .then(data => {
            rawPitchData = data.pitches;
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

function updateDash() {
    const pHand = document.getElementById('pitcherHandFilter').value;
    const pType = document.getElementById('pitchTypeFilter').value;
    const count = document.getElementById('countFilter').value;

    let filtered = rawPitchData.filter(p => {
        if (pHand !== 'All' && p.PitcherHand !== pHand) return false;
        
        if (pType !== 'All') {
            const t = p.PitchType ? p.PitchType.toLowerCase() : '';
            if (pType === 'Fastball' && !['fastball', 'sinker', 'cutter', 'four-seam', 'two-seam'].some(x => t.includes(x))) return false;
            if (pType === 'Offspeed' && !['changeup', 'splitter'].some(x => t.includes(x))) return false;
            if (pType === 'Breaking' && !['slider', 'curveball', 'sweeper', 'slurve'].some(x => t.includes(x))) return false;
        }

        if (count !== 'All') {
            const b = parseInt(p.Balls) || 0;
            const s = parseInt(p.Strikes) || 0;
            if (count === 'Ahead' && b <= s) return false;
            if (count === 'Behind' && b > s) return false;
            if (count === 'Even' && b !== s) return false;
        }
        
        return true;
    });

    renderHeatmaps(filtered);
}

// 5x5 grid boundaries
const x_edges = [-3.0, -0.83, -0.27, 0.27, 0.83, 3.0];
const y_edges = [0.0, 1.5, 2.16, 2.83, 3.5, 5.0];

function getBases(result) {
    if (!result) return -1; // -1 means no contact/non-bip
    const r = result.toLowerCase();
    if (r.includes('home')) return 4;
    if (r.includes('triple')) return 3;
    if (r.includes('double')) return 2;
    if (r.includes('single')) return 1;
    if (r.includes('out') || r.includes('error') || r.includes('fielderschoice')) return 0;
    return -1;
}

function getExpectedwOBA(p) {
    // If the database has xwOBA directly
    if (p.xwOBA !== undefined && p.xwOBA !== null) return parseFloat(p.xwOBA);
    
    // Fallback estimation (extremely rough mapping for demo)
    const bases = getBases(p.PlayResult);
    if (bases === 4) return 2.0;
    if (bases === 3) return 1.6;
    if (bases === 2) return 1.25;
    if (bases === 1) return 0.9;
    if (bases === 0) return 0.0;
    
    // Non play results
    if (p.KorBB && p.KorBB.toLowerCase().includes('walk')) return 0.7;
    if (p.KorBB && p.KorBB.toLowerCase().includes('strikeout')) return 0.0;
    
    return null; // Ignore pitch for avg calculation
}

function renderHeatmaps(data) {
    // Initialize 5x5 sum and counts
    let slgSums = Array(5).fill(0).map(() => Array(5).fill(0));
    let slgCounts = Array(5).fill(0).map(() => Array(5).fill(0));
    
    let xwobaSums = Array(5).fill(0).map(() => Array(5).fill(0));
    let xwobaCounts = Array(5).fill(0).map(() => Array(5).fill(0));

    data.forEach(p => {
        const x = parseFloat(p.PlateLocSide);
        const y = parseFloat(p.PlateLocHeight);
        if (isNaN(x) || isNaN(y)) return;

        // Find bin
        let x_ix = x_edges.findIndex(edge => x <= edge) - 1;
        let y_ix = y_edges.findIndex(edge => y <= edge) - 1;
        
        // constrain to bounds
        if (x_ix < 0) x_ix = 0; if (x_ix > 4) x_ix = 4;
        if (y_ix < 0) y_ix = 0; if (y_ix > 4) y_ix = 4;

        // SLG
        const bases = getBases(p.PlayResult);
        if (bases >= 0) {
            slgSums[y_ix][x_ix] += bases;
            slgCounts[y_ix][x_ix] += 1;
        }

        // xwOBA
        const xwoba = getExpectedwOBA(p);
        if (xwoba !== null) {
            xwobaSums[y_ix][x_ix] += xwoba;
            xwobaCounts[y_ix][x_ix] += 1;
        }
    });

    let slgZ = Array(5).fill(0).map(() => Array(5).fill(null));
    let xwobaZ = Array(5).fill(0).map(() => Array(5).fill(null));

    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            if (slgCounts[r][c] > 0) slgZ[r][c] = Number((slgSums[r][c] / slgCounts[r][c]).toFixed(3));
            if (xwobaCounts[r][c] > 0) xwobaZ[r][c] = Number((xwobaSums[r][c] / xwobaCounts[r][c]).toFixed(3));
        }
    }

    const layoutTemplate = {
        margin: { t: 20, r: 20, b: 20, l: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false },
        shapes: [
            // Draw strike zone outline (x=1 to 3, y=1 to 3) representing indices 1,2,3
            {
                type: 'rect',
                x0: 0.5, y0: 0.5,
                x1: 3.5, y1: 3.5,
                line: { color: 'white', width: 3 }
            }
        ],
        annotations: []
    };

    // Add text labels inside heatmap bins
    function buildAnnotations(zMatrix) {
        let anns = [];
        for (let r=0; r<5; r++) {
            for (let c=0; c<5; c++) {
                if (zMatrix[r][c] !== null) {
                    let val = zMatrix[r][c].toFixed(3).replace(/^0+/, '');
                    anns.push({
                        x: c, y: r,
                        text: val,
                        showarrow: false,
                        font: { color: 'white', size: 14 }
                    });
                }
            }
        }
        return anns;
    }

    const jetColorscale = [
        [0.0, 'rgb(0,0,255)'],     // Blue
        [0.2, 'rgb(0,255,255)'],   // Cyan
        [0.4, 'rgb(0,255,0)'],     // Green
        [0.6, 'rgb(255,255,0)'],   // Yellow
        [0.8, 'rgb(255,128,0)'],   // Orange
        [1.0, 'rgb(255,0,0)']      // Red
    ];

    // plot Slugging
    Plotly.newPlot('slg-heatmap', [{
        z: slgZ,
        type: 'heatmap',
        colorscale: jetColorscale,
        reversescale: false, 
        showscale: false,
        hoverinfo: 'z'
    }], { ...layoutTemplate, annotations: buildAnnotations(slgZ) }, {displayModeBar: false});

    // plot xwOBA
    Plotly.newPlot('xwoba-heatmap', [{
        z: xwobaZ,
        type: 'heatmap',
        colorscale: jetColorscale,
        reversescale: false,
        showscale: false,
        hoverinfo: 'z'
    }], { ...layoutTemplate, annotations: buildAnnotations(xwobaZ) }, {displayModeBar: false});
}

function renderRollingChart(data) {
    // Sort chronologically (assuming earliest to latest representation, or Date string)
    let sorted = [...data].sort((a, b) => new Date(a.GameDate || 0) - new Date(b.GameDate || 0));
    
    // Group by GameDate and PitchType
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
    let colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe'];
    let colorIdx = 0;

    pitchTypes.forEach(pType => {
        let rollingX = [];
        let rollingY = [];

        // Calculate 5-game rolling
        for (let i = 0; i < dates.length; i++) {
            let start = Math.max(0, i - 4);
            let sum = 0;
            let count = 0;
            for (let j = start; j <= i; j++) {
                let d = dates[j];
                let dayData = gamesMap.get(d);
                if (dayData && dayData[pType] && dayData[pType].length > 0) {
                    sum += dayData[pType].reduce((a,b)=>a+b, 0) / dayData[pType].length;
                    count++;
                }
            }
            
            rollingX.push(dates[i]);
            if (count > 0) {
                rollingY.push(sum / count);
            } else {
                rollingY.push(null);
            }
        }

        traces.push({
            x: rollingX,
            y: rollingY,
            name: pType,
            type: 'scatter',
            mode: 'lines+markers',
            connectgaps: true,
            line: { width: 3, color: colors[colorIdx % colors.length] },
            marker: { size: 8 }
        });
        colorIdx++;
    });

    let layout = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#ccc' },
        xaxis: { 
            title: 'Game Date',
            gridcolor: 'rgba(255,255,255,0.1)',
            zeroline: false
        },
        yaxis: { 
            title: 'Rolling xwOBA',
            gridcolor: 'rgba(255,255,255,0.1)',
            zeroline: false
        },
        margin: { t: 20, l: 50, r: 20, b: 50 },
        legend: {
            orientation: 'h',
            y: -0.2,
            font: { color: 'white' }
        }
    };

    Plotly.newPlot('rolling-chart', traces, layout, {displayModeBar: false});
}
