const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;
const slashes = [];
const urlParams = new URLSearchParams(window.location.search);
const fightType = urlParams.get('fight') || 'fight_1';

class Player {
    constructor() {
        this.hp = 100;
        this.difficulty = 1; // 1 = easy, 2 = medium, 3 = hard
    }

    takeDamage(amount) {
        sendDamageToServer(amount);
    }

    setDifficulty(level) {
        this.difficulty = level;
    }

    getDifficulty() {
        return this.difficulty;
    }
}

let bossHealth = 1000;
const bossBar = document.getElementById('bossBar');
const difficulty = document.getElementById('difficulty');
const keywordsContainer = document.getElementById('keywordsContainer');
let keywordsData = {};
let wordElements = []; // Store word elements for reuse
let dmg_word = null;

async function fetchBoss() {
    const response = await fetch(`/api/boss?fight=${fightType}`);
    const data = await response.json();
    bossHealth = data.health;
    boss.key_word = data.key_word;
    const groupWords = keywordsData[boss.key_word]?.word || [];
    dmg_word = groupWords[Math.floor(Math.random() * groupWords.length)];
    updateBossBar();
}

function updateBossBar() {
    bossBar.innerHTML = `Boss Health: ${bossHealth} `;
}

function updatedifficulty() {
    difficulty.innerHTML = `Difficulty: ${diff}`;
}

async function fetchDifficulty() {
    const response = await fetch('/api/difficulty');
    const data = await response.json();
    player.setDifficulty(data.difficulty);
    diff = player.getDifficulty();
    updatedifficulty();
    setIntervals(diff);
    updateshuri();
    updateweapon();
}

async function fetchKeywords() {
    const response = await fetch('/static/words.json');
    keywordsData = await response.json();
}

function displayKeywords() {
    keywordsContainer.innerHTML = '';
    const placedRects = [];

    // Use only the current boss key_word
    const group = boss.key_word;
    const words = keywordsData[group]?.word || [];

    words.forEach(word => {
        const wordElem = document.createElement('span');
        wordElem.innerText = word;
        wordElem.style.position = 'absolute';
        wordElem.style.cursor = 'none';
        wordElem.style.userSelect = 'none';
        wordElem.style.padding = '5px 10px';
        wordElem.style.border = 'none';
        wordElem.style.backgroundColor = 'transparent';
        wordElem.style.color = 'white';
        wordElem.style.pointerEvents = 'auto';
        wordElem.style.opacity = '0';
        wordElem.style.transition = 'opacity 0.5s';

        // Start offscreen to get dimensions
        wordElem.style.left = '-9999px';
        wordElem.style.top = '-9999px';
        keywordsContainer.appendChild(wordElem);

        const elemWidth = wordElem.offsetWidth;
        const elemHeight = wordElem.offsetHeight;

        let x, y, collision;
        let attempts = 0;
        do {
            x = Math.random() * (window.innerWidth - elemWidth - 40);
            y = Math.random() * (window.innerHeight - elemHeight - 40);
            collision = placedRects.some(rect => {
                return !(
                    x + elemWidth < rect.x ||
                    x > rect.x + rect.width ||
                    y + elemHeight < rect.y ||
                    y > rect.y + rect.height
                );
            });
            attempts++;
        } while (collision && attempts < 50);

        wordElem.style.left = `${x}px`;
        wordElem.style.top = `${y}px`;

        placedRects.push({ x, y, width: elemWidth, height: elemHeight });

        wordElem.addEventListener('mouseenter', () => {
            wordElem.style.backgroundColor = 'rgba(255,255,255,0.2)';
        });
        wordElem.addEventListener('mouseleave', () => {
            wordElem.style.backgroundColor = 'rgba(0,0,0,0.5)';
        });
        wordElem.addEventListener('click', () => {
            handleKeywordClick(group, word);
        });

        // Trigger fade-in
        requestAnimationFrame(() => {
            wordElem.style.opacity = '1';
        });
    });
}

async function handleKeywordClick(group, word) {
    if (boss.key_word && word === dmg_word) {
        const damageAmount = 50;
        const response = await fetch(`/api/boss/damage?fight=${fightType}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({damage: damageAmount})
        });
        const data = await response.json();
        bossHealth = data.health;
        updateBossBar();
        keywordsContainer.style.display = 'none';
        if (window.isRush && data.defeated) {
            // Store player HP in localStorage before redirecting
            localStorage.setItem('playerHP', player.hp);
            window.location.href = "/game?fight=fight_3&rush=true";
        }
        else if (data.defeated) {
            alert('Boss defeated! Returning to home page.');
            window.location.href = '/home';
        }
    } else {
        keywordsContainer.style.display = 'none';
    }
}

let boss = { key_word: {} };

async function initGameBoss() {
    await fetchBoss();
    await fetchKeywords();
    await fetchDifficulty();
    displayKeywords();
    setInterval(() => {
        displayKeywords();
    }, 10000);

    let visibleCount = 0;
    keywordsContainer.style.display = 'none';
    setInterval(() => {
        visibleCount++;
        if (visibleCount <= 1) {
            keywordsContainer.style.display = 'inline-block';
        } else {
            keywordsContainer.style.display = 'none';
            if (visibleCount === 2) visibleCount = 0;
        }
    }, 5000);
}

initGameBoss();

class ProjectileAttack {
    constructor(name, damage, speed, x, y, targetX, targetY, sprite, scale = 3) {
        this.name = name;
        this.damage = damage;
        this.speed = speed;
        this.x = x;
        this.y = y;
        this.radius = 10;
        this.sprite = sprite;
        this.scale = scale;

        // Compute angle to player at spawn
        const dx = targetX - x;
        const dy = targetY - y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        this.vx = (dx / distance) * speed;
        this.vy = (dy / distance) * speed;

        // 💡 Store angle in radians so it always points at the player
        this.angle = Math.atan2(dy, dx) + 90 * (Math.PI / 180); // Convert 45 degrees to radians
    }

    move() {
        this.x += this.vx;
        this.y += this.vy;
        // No rotation update — direction is fixed
    }

    isCollidingWith(px, py, pr) {
        const dx = this.x - px;
        const dy = this.y - py;
        const dist = Math.sqrt(dx * dx + dy * dy);
        return dist < this.radius + pr;
    }

    draw(ctx) {
        const size = 32 * this.scale; // 🔍 scale the image
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle); // ✅ Always point toward player
        ctx.drawImage(this.sprite, -size / 2, -size / 2, size, size);
        ctx.restore();
    }
}

class SlashAttack {
    constructor(name, damage, x, y, width, height, duration) {
        this.name = name;
        this.damage = damage;
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.duration = duration; // in ms
        this.startTime = performance.now();
    }

    isActive() {
        return performance.now() - this.startTime < this.duration;
    }

    isCollidingWith(px, py, pr) {
        return this.isActive() &&
            px + pr > this.x &&
            px - pr < this.x + this.width &&
            py + pr > this.y &&
            py - pr < this.y + this.height;
    }

    draw(ctx) {
        if (this.isActive()) {
            ctx.fillStyle = 'orange';
            ctx.fillRect(this.x, this.y, this.width, this.height);
        }
    }
}

const player = new Player();
let diff = player.getDifficulty();
let playerX = canvas.width / 2;
let playerY = canvas.height / 2;
const playerRadius = 10;
const bullets = [];

document.addEventListener('mousemove', (e) => {
    playerX = e.clientX;
    playerY = e.clientY;
});

let knifeSprite = null;
let redKnifeSprite = null;

function loadSprite(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
    });
}

async function preloadSprites() {
    knifeSprite = await loadSprite('/static/sprites/knife.png');
    redKnifeSprite = await loadSprite('/static/sprites/red_knife.png');
}

preloadSprites();

function spawnShurikenFromBorder() {
    const side = Math.floor(Math.random() * 4); // 0=top, 1=right, 2=bottom, 3=left
    let x, y;

    if (side === 0) { // Top
        x = Math.random() * canvas.width;
        y = -20;
    } else if (side === 1) { // Right
        x = canvas.width + 20;
        y = Math.random() * canvas.height;
    } else if (side === 2) { // Bottom
        x = Math.random() * canvas.width;
        y = canvas.height + 20;
    } else { // Left
        x = -20;
        y = Math.random() * canvas.height;
    }

    if (knifeSprite) {
        bullets.push(new ProjectileAttack(
            "shuriken",
            1,
            3,
            x,
            y,
            playerX,
            playerY,
            knifeSprite
        ));
    }
}

function updateHPBar(hp) {
    document.getElementById("hpBar").innerText = `HP: ${hp}`;
}

const shuri = document.getElementById('shuri');
const weapon = document.getElementById('weapon');

let shurikenIntervalId;
let weaponIntervalId;
let shurispwanint;
let weaponspwanint;

function setIntervals(diff) {
    shurispwanint = 600 / diff;
    weaponspwanint = 4000 / diff;

    if (shurikenIntervalId) {
        clearInterval(shurikenIntervalId);
    }
    if (weaponIntervalId) {
        clearInterval(weaponIntervalId);
    }

    shurikenIntervalId = setInterval(spawnShurikenFromBorder, shurispwanint);

    weaponIntervalId = setInterval(() => {
        if (Math.random() < 0.5) {
            slashes.push(new SlashAttack("slash", 1, Math.random() * canvas.width, canvas.height - 100, 100, 20, 500));
        } else {
            if (redKnifeSprite) {
                // Spawn red knife projectile dealing 100 damage
                const side = Math.floor(Math.random() * 4); // 0=top, 1=right, 2=bottom, 3=left
                let x, y;

                if (side === 0) { // Top
                    x = Math.random() * canvas.width;
                    y = -20;
                } else if (side === 1) { // Right
                    x = canvas.width + 20;
                    y = Math.random() * canvas.height;
                } else if (side === 2) { // Bottom
                    x = Math.random() * canvas.width;
                    y = canvas.height + 20;
                } else { // Left
                    x = -20;
                    y = Math.random() * canvas.height;
                }

                bullets.push(new ProjectileAttack(
                    "red_knife",
                    100,
                    5,
                    x,
                    y,
                    playerX,
                    playerY,
                    redKnifeSprite
                ));
            }
        }
    }, weaponspwanint);
}

function updateshuri() {
    shuri.innerText = `Shuri: ${shurispwanint}`;
}

function updateweapon() {
    weapon.innerText = `Weapon: ${weaponspwanint}`;
}

// Initialize intervals with default difficulty
setIntervals(player.getDifficulty());

function sendDamageToServer(amount) {
    fetch('/api/player/hp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({damage: amount})
    }).then(res => res.json()).then(data => {
        // Update HP bar only from server response
        updateHPBar(data.hp);
        // Update local player HP to server authoritative HP
        player.hp = data.hp;
        // Redirect to index.html if HP is 0 or less
        if (player.hp <= 0) {
            window.location.href = '/home';
        }
    });
}

function update() {
    bullets.forEach(b => b.move());

    bullets.forEach(b => {
        if (b.isCollidingWith(playerX, playerY, playerRadius)) {
            player.takeDamage(b.damage);
            bullets.splice(bullets.indexOf(b), 1);
        }
    });

    slashes.forEach(s => {
        if (s.isCollidingWith(playerX, playerY, playerRadius)) {
            player.takeDamage(s.damage);
        }
    });
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw player
    ctx.beginPath();
    ctx.arc(playerX, playerY, playerRadius, 0, Math.PI * 2);
    ctx.fillStyle = 'white';
    ctx.fill();

    // Draw bullets
    bullets.forEach(b => b.draw(ctx));

    // Draw slashes
    slashes.forEach(s => s.draw(ctx));
}

function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
    console.log(player.hp)
}

function updatePlayerHPFromRush() {
    if (window.isRush) {
        const storedHP = localStorage.getItem('playerHP');
        if (storedHP !== null) {
            const hp = parseInt(storedHP, 10);
            player.hp = hp;
            updateHPBar(hp);

            // Immediately sync the server-side player object with this HP
            fetch('/api/player/hp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ damage: 100 - hp })  // Simulate damage to bring server HP to same level
            }).then(res => res.json()).then(data => {
                console.log('Server HP synced:', data.hp);
            });
        } else {
            console.warn('No stored HP found');
        }
    }
    localStorage.removeItem('playerHP');
}



updatePlayerHPFromRush();

loop();
