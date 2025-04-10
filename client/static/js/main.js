// WebSocket Connection
const socket = new WebSocket('ws://localhost:8765');

socket.addEventListener('open', (event) => {
    console.log('WebSocket connected');
});

socket.addEventListener('message', (event) => {
    try {
        const data = JSON.parse(event.data);
        console.log('Message from server:', data);
        // Handle different message types here
    } catch (e) {
        console.error('Error parsing message:', e);
    }
});

function sendWebSocketMessage(type, data) {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type, data }));
    } else {
        console.error('WebSocket not connected');
    }
}

// DOM Elements
const authSection = document.getElementById('auth-section');
const gameSection = document.getElementById('game-section');
const lobbySection = document.getElementById('lobby-section');
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const wordInput = document.getElementById('word-input');
const submitWordBtn = document.getElementById('submit-word');
const startGameBtn = document.getElementById('start-game');
const playersList = document.getElementById('players-list');
const levelName = document.getElementById('level-name');
const timer = document.getElementById('timer');
const entityDisplay = document.getElementById('entity-display');

// Game State
let currentUser = null;
let gameState = null;
let lobbyState = null;

// Initialize UI
showAuthSection();

// Event Listeners
loginBtn.addEventListener('click', handleLogin);
registerBtn.addEventListener('click', handleRegister);
submitWordBtn.addEventListener('click', submitWord);
startGameBtn.addEventListener('click', startGame);

// UI Functions
function showAuthSection() {
    authSection.classList.remove('hidden');
    gameSection.classList.add('hidden');
    lobbySection.classList.add('hidden');
}

function showGameSection() {
    authSection.classList.add('hidden');
    gameSection.classList.remove('hidden');
    lobbySection.classList.add('hidden');
}

function showLobbySection() {
    authSection.classList.add('hidden');
    gameSection.classList.add('hidden');
    lobbySection.classList.remove('hidden');
}

// API Functions
async function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        // TODO: Replace with actual API call
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) throw new Error('Login failed');
        
        currentUser = await response.json();
        loadGameState();
        showGameSection();
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}

async function handleRegister() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        // TODO: Replace with actual API call
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (!response.ok) throw new Error('Registration failed');
        
        currentUser = await response.json();
        loadGameState();
        showGameSection();
    } catch (error) {
        alert('Registration failed: ' + error.message);
    }
}

async function loadGameState() {
    try {
        // TODO: Replace with actual API call
        const response = await fetch(`/api/game-state?user=${currentUser.id}`);
        if (!response.ok) throw new Error('Failed to load game state');
        
        gameState = await response.json();
        updateGameUI();
    } catch (error) {
        alert('Error loading game: ' + error.message);
    }
}

function updateGameUI() {
    levelName.textContent = gameState.currentLevel.name;
    timer.textContent = `Temps restant: ${gameState.currentLevel.timer}s`;
    
    entityDisplay.innerHTML = '';
    gameState.currentLevel.entities.forEach(entity => {
        const entityEl = document.createElement('div');
        entityEl.className = 'entity';
        entityEl.innerHTML = `
            <h3>${entity.name}</h3>
            <p>Temps avant attaque: ${entity.timer}s</p>
            <p>Mot à utiliser: ${entity.word}</p>
        `;
        entityDisplay.appendChild(entityEl);
    });
}

async function submitWord() {
    const word = wordInput.value.trim();
    if (!word) return;
    
    wordInput.value = '';
    
    try {
        // TODO: Replace with actual API call
        const response = await fetch('/api/submit-word', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                userId: currentUser.id,
                word: word,
                levelId: gameState.currentLevel.id
            })
        });
        
        if (!response.ok) throw new Error('Word submission failed');
        
        const result = await response.json();
        if (result.success) {
            loadGameState(); // Refresh game state
        } else {
            alert('Mot incorrect! Essayez encore.');
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
    }
}

// WebSocket for real-time updates
function setupWebSocket() {
    const socket = new WebSocket(`ws://${window.location.host}/ws`);
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'lobby_update') {
            updateLobby(data.players);
        }
        // Add other message types as needed
    };
}

function updateLobby(players) {
    playersList.innerHTML = '';
    players.forEach(player => {
        const playerEl = document.createElement('div');
        playerEl.textContent = player.username;
        playersList.appendChild(playerEl);
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupWebSocket();
});
