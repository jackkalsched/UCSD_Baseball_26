const REPO_PATH = '/UCSD_Baseball_26/';

function getBaseUrl() {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return '/';
    }
    return REPO_PATH;
}

function checkAuth() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    // If not logged in and on a protected page
    if (!currentUser && (window.location.pathname.endsWith('index.html') || window.location.pathname === getBaseUrl())) {
        window.location.href = getBaseUrl() + 'login.html';
    }
    // If logged in and on login/set_password pages, redirect to index
    if (currentUser && (window.location.pathname.endsWith('login.html') || window.location.pathname.endsWith('set_password.html'))) {
        window.location.href = getBaseUrl() + 'index.html';
    }
    return currentUser;
}

function login(userId, password) {
    const users = JSON.parse(localStorage.getItem('users')) || {};
    if (users[userId] && users[userId].password === password) {
        localStorage.setItem('currentUser', JSON.stringify({
            userId: userId,
            role: users[userId].role
        }));
        return true;
    }
    return false;
}

function setPassword(token, password) {
    try {
        const payloadStr = atob(token);
        const payload = JSON.parse(payloadStr);
        
        const users = JSON.parse(localStorage.getItem('users')) || {};
        users[payload.userId] = {
            password: password,
            role: payload.role
        };
        localStorage.setItem('users', JSON.stringify(users));
        return true;
    } catch (e) {
        console.error("Invalid token", e);
        return false;
    }
}

function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = getBaseUrl() + 'login.html';
}

function applyView(role, user) {
    const navRoster = document.getElementById('nav-roster');
    const playerHero = document.getElementById('player-hero');
    const coachHero = document.getElementById('coach-hero');
    const recentUpdatesBox = document.getElementById('recent-updates-box');
    const lastGameBox = document.getElementById('last-game-box');
    
    // Set titles using user ID where present
    const welcomeTextPlayer = document.getElementById('welcome-text-player');
    if (welcomeTextPlayer) welcomeTextPlayer.textContent = `Welcome to the Team Portal, ${user.userId}`;

    if (role === 'player') {
        if (navRoster) navRoster.classList.add('hidden');
        if (playerHero) playerHero.classList.remove('hidden');
        if (coachHero) coachHero.classList.add('hidden');
        if (recentUpdatesBox) recentUpdatesBox.classList.add('hidden');
        if (lastGameBox) lastGameBox.classList.remove('hidden');
    } else {
        // coach or analyst default
        if (navRoster) navRoster.classList.remove('hidden');
        if (playerHero) playerHero.classList.add('hidden');
        if (coachHero) coachHero.classList.remove('hidden');
        if (recentUpdatesBox) recentUpdatesBox.classList.remove('hidden');
        if (lastGameBox) lastGameBox.classList.add('hidden');
    }
}

function updateUI() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    if (!user) return;
    
    const toggleContainer = document.getElementById('analyst-toggle-container');
    const toggleBtn = document.getElementById('analyst-toggle-btn');

    if (user.role === 'analyst') {
        if (toggleContainer) toggleContainer.classList.remove('hidden');
        
        let currentView = window.currentAnalystView || 'coach';
        applyView(currentView, user);
        
        if (toggleBtn) {
            toggleBtn.textContent = currentView === 'coach' ? 'Switch to Player View' : 'Switch to Coach View';
            toggleBtn.onclick = function(e) {
                e.preventDefault();
                window.currentAnalystView = currentView === 'coach' ? 'player' : 'coach';
                currentView = window.currentAnalystView;
                applyView(currentView, user);
                toggleBtn.textContent = currentView === 'coach' ? 'Switch to Player View' : 'Switch to Coach View';
            };
        }
    } else {
        if (toggleContainer) toggleContainer.classList.add('hidden');
        applyView(user.role, user);
    }
}
