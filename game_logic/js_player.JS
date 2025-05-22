class Player {
    constructor() {
        this.hp = 100;
    }

    takeDamage(amount) {
        this.hp -= amount;
        if (this.hp < 0) this.hp = 0;
    }
}

class ProjectileAttack {
    constructor(name, damage, speed, x, y) {
        this.name = name;
        this.damage = damage;
        this.speed = speed;
        this.x = x;
        this.y = y;
        this.radius = 5;
    }

    move() {
        this.y += this.speed;
    }

    isCollidingWith(playerX, playerY, playerRadius) {
        const dx = this.x - playerX;
        const dy = this.y - playerY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        return distance < this.radius + playerRadius;
    }
}
