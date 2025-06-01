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
            window.location.href = "/game?fight=fight_4&rush=true";
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
    constructor(name, damage, speed, x, y, targetX, targetY, sprite, scale = 3, angleOverride = null) {
        this.name = name;
        this.damage = damage;
        this.speed = speed;
        this.x = x;
        this.y = y;
        this.radius = 10;
        this.sprite = sprite;
        this.scale = scale;

        if (angleOverride !== null) {
            this.angle = angleOverride;
            this.vx = Math.cos(this.angle) * speed;
            this.vy = Math.sin(this.angle) * speed;
        } else {
            // Compute angle to player at spawn
            const dx = targetX - x;
            const dy = targetY - y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            this.vx = (dx / distance) * speed;
            this.vy = (dy / distance) * speed;

            // Store angle in radians so it always points at the player
            this.angle = Math.atan2(dy, dx); // Use exact angle without offset
        }
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
        const size = 32 * this.scale; // scale the image
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.angle); // Always point toward player or direction
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

let arrowSprite = null;

function loadSprite(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = src;
    });
}

async function preloadSprites() {
    arrowSprite = await loadSprite('/static/sprites/Arrow.png');
}

preloadSprites();

function spawnBasicArrowFromBorder() {
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

    if (arrowSprite) {
        bullets.push(new ProjectileAttack(
            "arrow_basic",
            1,
            4,
            x,
            y,
            playerX,
            playerY,
            arrowSprite,
            1.5
        ));
    }
}

function spawnCircularArrowAttack(centerX, centerY) {
    if (!arrowSprite) return;
    const numArrows = 12;
    const angleStep = (2 * Math.PI) / numArrows;

    for (let i = 0; i < numArrows; i++) {
        const angle = i * angleStep;
        // Arrows spawn at centerX, centerY and move outward in direction of angle
        bullets.push(new ProjectileAttack(
            "arrow_circular",
            2,
            3,
            centerX,
            centerY,
            0,
            0,
            arrowSprite,
            1.5,
            angle
        ));
    }
}

function spawnGatlingArrowAttack(centerX, centerY) {
    if (!arrowSprite) return;
    const arrowsToSpawn = 10;
    let spawned = 0;

    const gatlingInterval = setInterval(() => {
        if (spawned >= arrowsToSpawn) {
            clearInterval(gatlingInterval);
            return;
        }
        bullets.push(new ProjectileAttack(
            "arrow_gatling",
            3,
            5,
            centerX,
            centerY,
            playerX,
            playerY,
            arrowSprite,
            3
        ));
        spawned++;
    }, 100);
}

let basicArrowIntervalId;
let circularArrowIntervalId;
let gatlingArrowIntervalId;

function setIntervals(diff) {
    if (diff < 1) diff = 1; // safeguard against zero or negative difficulty

    const basicInterval = 600 / diff;
    const circularInterval = 8000 / diff;
    const gatlingInterval = 12000 / diff;

    console.log(`Setting intervals with diff=${diff}, basic=${basicInterval}, circular=${circularInterval}, gatling=${gatlingInterval}`);

    if (basicArrowIntervalId) {
        clearInterval(basicArrowIntervalId);
    }
    if (circularArrowIntervalId) {
        clearInterval(circularArrowIntervalId);
    }
    if (gatlingArrowIntervalId) {
        clearInterval(gatlingArrowIntervalId);
    }

    basicArrowIntervalId = setInterval(spawnBasicArrowFromBorder, basicInterval);

    circularArrowIntervalId = setInterval(() => {
        // Spawn circular arrows at a random border position on canvas
        let x, y;
        const side = Math.floor(Math.random() * 4);
        if (side === 0) { // Top
            x = Math.random() * canvas.width;
            y = 0;
        } else if (side === 1) { // Right
            x = canvas.width;
            y = Math.random() * canvas.height;
        } else if (side === 2) { // Bottom
            x = Math.random() * canvas.width;
            y = canvas.height;
        } else { // Left
            x = 0;
            y = Math.random() * canvas.height;
        }
        spawnCircularArrowAttack(x, y);
    }, circularInterval);

    gatlingArrowIntervalId = setInterval(() => {
        // Spawn gatling arrows at random position on canvas
        const x = Math.random() * canvas.width * 0.8 + canvas.width * 0.1;
        const y = Math.random() * canvas.height * 0.8 + canvas.height * 0.1;
        spawnGatlingArrowAttack(x, y);
    }, gatlingInterval);
}

function updateshuri() {
    shuri.innerText = `Basic Arrow Attack Interval: ${600 / diff}`;
}

function updateweapon() {
    weapon.innerText = `Circular Arrow Attack Interval: ${8000 / diff}, Gatling Arrow Attack Interval: ${12000 / diff}`;
}

function update() {
    bullets.forEach(b => b.move());

    for (let i = bullets.length - 1; i >= 0; i--) {
        const b = bullets[i];
        if (b.isCollidingWith(playerX, playerY, playerRadius)) {
            player.takeDamage(b.damage);
            bullets.splice(i, 1);
        }
    }

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
}

loop();
