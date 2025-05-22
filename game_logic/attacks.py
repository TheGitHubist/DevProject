from abc import ABC, abstractmethod

class Attack(ABC):
    def __init__(self, name: str, damage: int):
        self.name = name
        self.damage = damage

    def dealDamageTo(self, player):
        player.hp -= self.damage
        if player.hp < 0:
            player.hp = 0
        return player.hp

class ProjectileAttack(Attack):
    def __init__(self, name: str, damage: int, projectile_speed: float):
        super().__init__(name, damage)
        self.projectile_speed = projectile_speed

    def move(self, orientation: float, x, y):
        # Logic to move the projectile in the specified orientation
        pass

class SlashAttack(Attack):
    def __init__(self, name: str, damage: int, range: float):
        super().__init__(name, damage)
        self.range = range

    def slash(self, orientation: float, x, y):
        # Logic to perform a slash attack on the target
        pass

class LaserBeamAttack(Attack):
    def __init__(self, name: str, damage: int, beam_width: float):
        super().__init__(name, damage)
        self.beam_width = beam_width

    def fire(self, orientation: float, x, y):
        # Logic to fire a laser beam in the specified orientation
        pass