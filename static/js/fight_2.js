const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;
const slashes = [];
const lasers = [];

class Player {
    constructor() {
        this.hp = 100;
    }

    takeDamage(amount) {
        sendDamageToServer(amount);
    }
}

let bossHealth = 1000;
const bossBar = document.getElementById('bossBar');
const keywordsContainer = document.getElementById('keywordsContainer');
let keywordsData = {};

async function fetchBoss() {
    const response = await fetch('/api/boss');
    const data = await response.json();
    bossHealth = data.health;
    boss.key_word = data.key_word;
    updateBossBar();
}

async function fetchKeywords() {
    const response = await fetch('/static/words.json');
    keywordsData = await response.json();
}

function updateBossBar() {
    bossBar.innerText = `Boss HP: ${bossHealth}`;
}

function displayKeywords() {
    keywordsContainer.innerHTML = '';
    const placedRects = [];

    for (const group in keywordsData) {
        const words = keywordsData[group].word;
        words.forEach(word => {
            const wordElem = document.createElement('span');
            wordElem.innerText = word;
            wordElem.style.position = 'absolute';
            wordElem.style.cursor = 'pointer';
            wordElem.style.userSelect = 'none';
            wordElem.style.padding = '5px 10px';
            wordElem.style.border = '1px solid black';
            wordElem.style.borderRadius = '5px';
            wordElem.style.backgroundColor = 'rgba(0,0,0,0.5)';
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
                x = Math.random() * (window.innerWidth - elemWidth);
                y = Math.random() * (window.innerHeight - elemHeight);
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
}


async function handleKeywordClick(group, word) {
    if (boss.key_word && word === boss.key_word) {
        const damageAmount = 50;
        const response = await fetch('/api/boss/damage', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({damage: damageAmount})
        });
        const data = await response.json();
        bossHealth = data.health;
        updateBossBar();
        if (data.defeated) {
            alert('Boss defeated! Returning to home page.');
            window.location.href = '/home';
        }
    }
}

let boss = { key_word: {} };

async function initGameBoss() {
    await fetchBoss();
    await fetchKeywords();
    displayKeywords();
    setInterval(() => {
        displayKeywords();
    }, 10000);

    let visibleCount = 0;
    keywordsContainer.style.display = 'none';
    setInterval(() => {
        visibleCount++;
        if (visibleCount <= 2) {
            keywordsContainer.style.display = 'inline-block';
        } else {
            keywordsContainer.style.display = 'none';
            if (visibleCount === 3) visibleCount = 0;
        }
    }, 5000);
}

initGameBoss();

class ProjectileAttack {
    constructor(name, damage, speed, x, y, targetX, targetY, sprite) {
        this.name = name;
        this.damage = damage;
        this.speed = speed;
        this.x = x;
        this.y = y;
        this.radius = 10; // for collision
        this.sprite = sprite;
        this.rotation = 0;

        // Compute angle to player at time of spawn
        const dx = targetX - x;
        const dy = targetY - y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        this.vx = (dx / distance) * speed;
        this.vy = (dy / distance) * speed;
    }

    move() {
        this.x += this.vx;
        this.y += this.vy;
        this.rotation += 0.2; // Rotate every frame
    }

    isCollidingWith(px, py, pr) {
        const dx = this.x - px;
        const dy = this.y - py;
        const dist = Math.sqrt(dx * dx + dy * dy);
        return dist < this.radius + pr;
    }

    draw(ctx) {
        const size = 30;
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate(this.rotation);
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

class LaserBeamAttack {
    constructor(name, damage, x, width, duration) {
        this.name = name;
        this.damage = damage;
        this.x = x;
        this.width = width;
        this.y = 0;
        this.height = canvas.height;
        this.duration = duration;
        this.startTime = performance.now();
    }

    isActive() {
        return performance.now() - this.startTime < this.duration;
    }

    isCollidingWith(px, py, pr) {
        return this.isActive() &&
            px + pr > this.x &&
            px - pr < this.x + this.width;
    }

    draw(ctx) {
        if (this.isActive()) {
            ctx.fillStyle = 'cyan';
            ctx.fillRect(this.x, this.y, this.width, this.height);
        }
    }
}


const player = new Player();
let playerX = canvas.width / 2;
let playerY = canvas.height / 2;
const playerRadius = 10;
const bullets = [];

document.addEventListener('mousemove', (e) => {
    playerX = e.clientX;
    playerY = e.clientY;
});

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

    bullets.push(new ProjectileAttack(
        "shuriken",
        1,
        3,
        x,
        y,
        playerX,
        playerY,
        document.getElementById("shurikenSprite")
    ));
}


function updateHPBar(hp) {
    document.getElementById("hpBar").innerText = `HP: ${hp}`;
}

setInterval(spawnShurikenFromBorder, 600);

setInterval(() => {
if (Math.random() < 0.5) {
    slashes.push(new SlashAttack("slash", 1, Math.random() * canvas.width, canvas.height - 100, 100, 20, 500));
} else {
    lasers.push(new LaserBeamAttack("laser", 1, Math.random() * canvas.width, 20, 800));
}
}, 4000);


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

    lasers.forEach(l => {
        if (l.isCollidingWith(playerX, playerY, playerRadius)) {
            player.takeDamage(l.damage);
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

    // Draw slashes and lasers
    slashes.forEach(s => s.draw(ctx));
    lasers.forEach(l => l.draw(ctx));
}



function loop() {
    update();
    draw();
    requestAnimationFrame(loop);
    console.log(player.hp)
}
loop();