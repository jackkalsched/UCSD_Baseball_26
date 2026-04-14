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

function updateUI() {
    const user = JSON.parse(localStorage.getItem('currentUser'));
    if (user) {
        const welcomeText = document.getElementById('welcome-text');
        if (welcomeText) {
            welcomeText.textContent = `Welcome to the Team Portal, ${user.userId}`;
        }
    }
}
