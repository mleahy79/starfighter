import pygame
import sys
import random

pygame.init()
WIDTH, HEIGHT = 950, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Starfighter")
clock = pygame.time.Clock()


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
        if self.rect.bottom < 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = random.randint(1, 3)

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
        self.image = pygame.Surface((16, 16))
        self.image.fill((255, 0, 255))
        self.rect = self.image.get_rect(center=(player.rect.centerx + offset_x, player.rect.centery - 10))
        self.shoot_cooldown = 300
        self.last_shot = 0
        self.speed = 2

    def update(self):
        target_x = self.player.rect.centerx + self.offset_x
        target_y = self.player.rect.centery - 10
        if self.rect.x < target_x:
            self.rect.x += self.speed
        elif self.rect.x > target_x:
            self.rect.x -= self.speed
        if self.rect.y < target_y:
            self.rect.y += self.speed
        elif self.rect.y > target_y:
            self.rect.y -= self.speed


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((0, 255, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.shoot_cooldown = 200  # milliseconds
        self.last_shot = 0
        self.weapon_mode = "laser"

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
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, 0, -10, "spray"))
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, -3, -10, "spray"))
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, 3, -10, "spray"))


# Setup
player = Player(WIDTH // 2, HEIGHT - 80)
players = pygame.sprite.Group(player)
bullets = pygame.sprite.Group()
enemies = pygame.sprite.Group()
powerups = pygame.sprite.Group()
drones = pygame.sprite.Group()

spawn_interval = 1000  # milliseconds
spawn_timer = pygame.time.get_ticks()

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

    # Update
    keys = pygame.key.get_pressed()
    player.update(keys, bullets)
    bullets.update()
    enemies.update()
    powerups.update()
    drones.update()

    # Bullet vs enemy collisions
    for bullet in list(bullets):
        hits = pygame.sprite.spritecollide(bullet, enemies, True)
        if hits:
            bullet.kill()

    # Player vs powerup collisions
    collected = pygame.sprite.spritecollide(player, powerups, True)
    for powerup in collected:
        if powerup.kind in ("laser", "spray"):
            player.weapon_mode = powerup.kind
        elif powerup.kind == "drone":
            drones.add(Drone(player, -40))
            drones.add(Drone(player, 40))

    # Draw
    screen.fill((0, 0, 0))
    players.draw(screen)
    bullets.draw(screen)
    enemies.draw(screen)
    powerups.draw(screen)
    drones.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
