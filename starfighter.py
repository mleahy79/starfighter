import pygame
import sys
import random

pygame.init()
WIDTH, HEIGHT = 850, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Starfighter")
clock = pygame.time.Clock()
star_color = (200, 200, 200)

stars = []
for _ in range(150):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    stars.append([x, y])

def update_stars():
    for star in stars:
        star[1] += 1
        if star[1] > HEIGHT:
            star[0] = random.randint(0, WIDTH)
            star[1] = 0


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, kind):
        super().__init__()
        self.kind = kind
        w = 4 if kind == "laser" else 3
        h = 16
        self.image = pygame.Surface((w, h))
        color = (0, 255, 0) if kind == "laser" else (255, 255, 0)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image = pygame.image.load("spawnr1.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (95, 95))
        except FileNotFoundError:
            self.image = pygame.Surface((95, 95))
            self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = random.randint(3, 10)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        self.image = pygame.Surface((16, 16))
        colors = {
            "laser": (0, 255, 0),
            "spray": (255, 255, 0),
            "drone": (255, 0, 255),
            "health": (255, 255, 255),
        }
        self.image.fill(colors.get(kind, (255, 255, 255)))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 1

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()


class Drone(pygame.sprite.Sprite):
    def __init__(self, player, offset_x):
        super().__init__()
        self.player = player
        self.offset_x = offset_x
        try:
            self.image = pygame.image.load("stardrone.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (20, 20))
        except FileNotFoundError:
            self.image = pygame.Surface((20, 20))
            self.image.fill((255, 0, 255))
        self.rect = self.image.get_rect(
            center=(player.rect.centerx + offset_x, player.rect.centery - 10)
        )
        self.shoot_cooldown = 300
        self.last_shot = 0
        self.speed = 4

    def update(self, bullet_group):
        # Snap to player position
        target_x = self.player.rect.centerx + self.offset_x
        target_y = self.player.rect.centery - 10

        if self.rect.centerx < target_x:
            self.rect.centerx = min(self.rect.centerx + self.speed, target_x)
        elif self.rect.centerx > target_x:
            self.rect.centerx = max(self.rect.centerx - self.speed, target_x)

        if self.rect.centery < target_y:
            self.rect.centery = min(self.rect.centery + self.speed, target_y)
        elif self.rect.centery > target_y:
            self.rect.centery = max(self.rect.centery - self.speed, target_y)

        # Drone shoots automatically
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot >= self.shoot_cooldown:
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, 0, -10, "laser"))
            self.last_shot = current_time


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Fallback to a colored rectangle if image not found
        try:
            self.image = pygame.image.load("starfighter1.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (64, 64))
        except FileNotFoundError:
            self.image = pygame.Surface((64, 64))
            self.image.fill((0, 150, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.shoot_cooldown = 200
        self.last_shot = 0
        self.weapon_mode = "laser"
        self.health = 3

    def update(self, keys, bullet_group):
        dx = dy = 0
        if keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_DOWN]:
            dy += self.speed

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        if keys[pygame.K_SPACE]:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot >= self.shoot_cooldown:
                self.shoot(bullet_group)
                self.last_shot = current_time

    def shoot(self, bullet_group):
        if self.weapon_mode == "laser":
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, 0, -10, "laser"))
        elif self.weapon_mode == "spray":
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top,  0, -10, "spray"))
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, -3, -10, "spray"))
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top,  3, -10, "spray"))


# ── Setup ──────────────────────────────────────────────────────────────────
player = Player(WIDTH // 2, HEIGHT - 80)
players = pygame.sprite.Group(player)
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
powerups = pygame.sprite.Group()
drones = pygame.sprite.Group()

spawn_interval = 1000
spawn_timer = pygame.time.get_ticks()

# Spawn a powerup every 8 seconds for testing
powerup_interval = 8000
powerup_timer = pygame.time.get_ticks()
powerup_kinds = ["laser", "spray", "drone", "health"]

font = pygame.font.SysFont(None, 36)

# ── Game Loop ──────────────────────────────────────────────────────────────
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = pygame.time.get_ticks()

    # Spawn enemies
    if current_time - spawn_timer >= spawn_interval:
        spawn_timer = current_time
        enemies.add(Enemy(random.randint(20, WIDTH - 20), -20))

    # Spawn powerups (cycles through kinds for testing)
    if current_time - powerup_timer >= powerup_interval:
        powerup_timer = current_time
        kind = random.choice(powerup_kinds)
        powerups.add(PowerUp(random.randint(40, WIDTH - 40), -16, kind))

    # Update
    keys = pygame.key.get_pressed()
    player.update(keys, bullets)
    bullets.update()
    enemies.update()
    powerups.update()
    drones.update(bullets)  # Drones now receive bullet_group correctly

    # Player vs enemy collisions
    hits = pygame.sprite.spritecollide(player, enemies, True)
    if hits:
        player.health -= len(hits)
        print(f"Player hit! Health: {player.health}")
        if player.health <= 0:
            running = False

    # Bullet vs enemy collisions
    for bullet in list(bullets):
        hit_enemies = pygame.sprite.spritecollide(bullet, enemies, True)
        if hit_enemies:
            bullet.kill()

    # Player vs powerup collisions
    collected = pygame.sprite.spritecollide(player, powerups, True)
    for powerup in collected:
        if powerup.kind in ("laser", "spray"):
            player.weapon_mode = powerup.kind
        elif powerup.kind == "drone":
            # Clear existing drones first to avoid stacking
            drones.empty()
            drones.add(Drone(player, -40))
            drones.add(Drone(player, 40))
        elif powerup.kind == "health":
            player.health = min(player.health + 1, 5)

    # ── Draw ───────────────────────────────────────────────────────────────
    screen.fill((0, 0, 0))
    update_stars()
    for star in stars:
        pygame.draw.circle(screen, star_color, (star[0], star[1]), 1)

    enemies.draw(screen)
    powerups.draw(screen)
    drones.draw(screen)
    players.draw(screen)
    bullets.draw(screen)

    # HUD
    health_text = font.render(f"HP: {player.health}", True, (255, 255, 255))
    weapon_text = font.render(f"Weapon: {player.weapon_mode}", True, (200, 200, 0))
    screen.blit(health_text, (10, 10))
    screen.blit(weapon_text, (10, 40))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
