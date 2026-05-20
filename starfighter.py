import pygame
import sys
import random
import math

pygame.init()
MUSIC_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_END)

WIDTH, HEIGHT = 850, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Starfighter")
clock = pygame.time.Clock()
star_color = (200, 200, 200)
font       = pygame.font.SysFont(None, 36)
font_med   = pygame.font.SysFont(None, 52)
font_large = pygame.font.SysFont(None, 90)
# TODO: make additional soundtracks, make hook for boss fight and underbosses, maybe different music for each underboss as well

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


# ── Player Bullet ─────────────────────────────────────────────────────────────
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, kind):
        super().__init__()
        self.kind = kind
        w = 4 if kind == "laser" else 3
        self.image = pygame.Surface((w, 16))
        self.image.fill((0, 255, 0) if kind == "laser" else (255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.bottom < 0 or self.rect.top > HEIGHT:
            self.kill()


# ── Enemy Bullet ──────────────────────────────────────────────────────────────
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy):
        super().__init__()
        self.image = pygame.Surface((5, 12))
        self.image.fill((255, 80, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.top > HEIGHT or self.rect.bottom < 0
                or self.rect.right < 0 or self.rect.left > WIDTH):
            self.kill()


# ── Spawn Ranks ───────────────────────────────────────────────────────────────
# (image file, size, speed range, allowed behaviors)
# TODO: tune sizes, speeds, and behaviors for each rank once sprites are finalized
ENEMY_KINDS = {
    "r1": ("spawnr1.png", (60,  60),  (4, 7), ["straight"]),
    "r2": ("spawnr2.png", (70,  70),  (3, 5), ["straight", "shuffle"]),           # TODO: finalize r2 motion
    "r3": ("spawnr3.png", (80,  80),  (2, 4), ["straight", "shuffle"]),           # TODO: finalize r3 motion
    "r4": ("spawnr4.png", (90,  90),  (2, 3), ["straight", "shuffle", "charger"]),
    "r5": ("spawnr5.png", (100, 100), (1, 2), ["straight", "shuffle", "charger", "shooter"]),  # TODO: finalize r5
}

ENEMY_POINTS = {"r1": 10, "r2": 20, "r3": 30, "r4": 40, "r5": 50}

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, player, enemy_bullets, kind=None):
        super().__init__()
        if kind is None:
            kind = random.choice(list(ENEMY_KINDS.keys()))
        self.kind = kind
        img_file, size, speed_range, behaviors = ENEMY_KINDS[kind]
        try:
            self.image = pygame.image.load(img_file).convert_alpha()
            self.image = pygame.transform.scale(self.image, size)
        except FileNotFoundError:
            self.image = pygame.Surface(size)
            self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = random.randint(*speed_range)
        self.player = player
        self.enemy_bullets = enemy_bullets
        self.behavior = random.choice(behaviors)
        self.tick = random.uniform(0, 6.28)
        self.shoot_cooldown = 2000
        self.last_shot = 0

    def update(self):
        if self.behavior == "straight":
            self.rect.y += self.speed

        elif self.behavior == "shuffle":
            self.tick += 0.05
            self.rect.x += int(math.sin(self.tick) * 2)
            self.rect.y += self.speed

        elif self.behavior == "charger":
            if self.rect.y < HEIGHT * 0.30:
                self.rect.y += self.speed
            else:
                dx = self.player.rect.centerx - self.rect.centerx
                dy = self.player.rect.centery - self.rect.centery
                dist = max(1, math.hypot(dx, dy))
                self.rect.x += int((dx / dist) * self.speed * 2)
                self.rect.y += int((dy / dist) * self.speed * 2)

        elif self.behavior == "shooter":
            self.rect.y += self.speed
            now = pygame.time.get_ticks()
            if now - self.last_shot >= self.shoot_cooldown:
                self.last_shot = now
                dx = self.player.rect.centerx - self.rect.centerx
                dy = self.player.rect.centery - self.rect.centery
                dist = max(1, math.hypot(dx, dy))
                self.enemy_bullets.add(EnemyBullet(
                    self.rect.centerx, self.rect.bottom,
                    int(dx / dist * 4), int(dy / dist * 4)
                ))

        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


# ── Underbosses ───────────────────────────────────────────────────────────────
# TODO: give each underboss a distinct attack pattern and movement style
_UNDERBOSS_DATA = {
    1: ("underboss1.png", (140, 140), (200, 100,   0), 10),   # (image, size, fallback color, health)
    2: ("underboss2.png", (150, 150), (180,   0, 200), 15),   # TODO: tune health values
    3: ("underboss3.png", (160, 160), (  0, 180, 200), 20),
}

class Underboss(pygame.sprite.Sprite):
    def __init__(self, x, y, player, enemy_bullets, kind=1):
        super().__init__()
        img_file, size, fallback_color, health = _UNDERBOSS_DATA[kind]
        try:
            self.image = pygame.image.load(img_file).convert_alpha()
            self.image = pygame.transform.scale(self.image, size)
        except FileNotFoundError:
            self.image = pygame.Surface(size)
            self.image.fill(fallback_color)
        self.rect = self.image.get_rect(center=(x, y))
        self.health = health
        self.max_health = health
        self.player = player
        self.enemy_bullets = enemy_bullets
        self.speed = 2
        self.tick = 0
        self.shoot_cooldown = 1200   # TODO: tune per kind
        self.last_shot = 0
        self.kind = kind

    def update(self):
        # TODO: customize movement per underboss kind — currently all patrol side-to-side
        self.tick += 0.02
        self.rect.x = int(WIDTH / 2 + math.sin(self.tick) * (WIDTH / 2 - 90))
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.kill()
            return
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_cooldown:
            self.last_shot = now
            self._shoot()

    def _shoot(self):
        # TODO: customize shoot pattern per underboss kind
        cx, cy = self.rect.centerx, self.rect.bottom
        dx = self.player.rect.centerx - cx
        dy = self.player.rect.centery - cy
        dist = max(1, math.hypot(dx, dy))
        self.enemy_bullets.add(EnemyBullet(cx, cy, int(dx / dist * 5), int(dy / dist * 5)))

    def hit(self):
        self.health -= 1
        return self.health <= 0

    def draw_health_bar(self, surface):
        bw = self.rect.width
        x, y = self.rect.left, self.rect.top - 10
        pygame.draw.rect(surface, (80, 0, 0),    (x, y, bw, 6))
        pygame.draw.rect(surface, (220, 50, 50), (x, y, int(bw * self.health / self.max_health), 6))


# ── Main Boss ──────────────────────────────────────────────────────────────────
# TODO: finalize phases, attack patterns, and image
class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, player, enemy_bullets):
        super().__init__()
        try:
            self.image = pygame.image.load("mainboss.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (220, 220))
        except FileNotFoundError:
            self.image = pygame.Surface((220, 220))
            self.image.fill((180, 0, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 80          # TODO: tune
        self.max_health = 80
        self.player = player
        self.enemy_bullets = enemy_bullets
        self.tick = 0
        self.phase = 1            # advances as health drops (1 → 2 → 3)
        self.shoot_cooldown = 800
        self.last_shot = 0

    def update(self):
        self.tick += 0.015
        self.rect.x = int(WIDTH / 2 + math.sin(self.tick) * (WIDTH / 2 - 130))

        if self.health <= self.max_health * 0.33:
            self.phase = 3
        elif self.health <= self.max_health * 0.66:
            self.phase = 2

        now = pygame.time.get_ticks()
        cooldown = max(300, self.shoot_cooldown - (self.phase - 1) * 200)
        if now - self.last_shot >= cooldown:
            self.last_shot = now
            self._shoot()

    def _shoot(self):
        # TODO: design full attack patterns per phase
        cx, cy = self.rect.centerx, self.rect.bottom
        if self.phase == 1:
            dx = self.player.rect.centerx - cx
            dy = self.player.rect.centery - cy
            dist = max(1, math.hypot(dx, dy))
            self.enemy_bullets.add(EnemyBullet(cx, cy, int(dx / dist * 5), int(dy / dist * 5)))
        elif self.phase == 2:
            # TODO: refine spread pattern
            for offset in [-15, 0, 15]:
                rad = math.radians(90 + offset)
                self.enemy_bullets.add(EnemyBullet(cx, cy, int(math.cos(rad) * 5), int(math.sin(rad) * 5)))
        elif self.phase == 3:
            # TODO: refine full barrage
            for offset in [-30, -15, 0, 15, 30]:
                rad = math.radians(90 + offset)
                self.enemy_bullets.add(EnemyBullet(cx, cy, int(math.cos(rad) * 6), int(math.sin(rad) * 6)))

    def hit(self):
        self.health -= 1
        return self.health <= 0

    def draw_health_bar(self, surface):
        bw, bh = 400, 18
        x = (WIDTH - bw) // 2
        y = HEIGHT - 36
        pygame.draw.rect(surface, (80, 0, 0),    (x, y, bw, bh))
        pygame.draw.rect(surface, (220, 30, 30), (x, y, int(bw * self.health / self.max_health), bh))
        surface.blit(font.render("BOSS", True, (255, 200, 200)), (x - 60, y))


# ── PowerUp ───────────────────────────────────────────────────────────────────
class PowerUp(pygame.sprite.Sprite):
    SPRITES = {
        "laser":  "weapons-laser.png",
        "spray":  "weapons-spray.png",
        "drone":  "weapon_upgrade.png",
        "health": "health.png",
    }
    FALLBACK_COLORS = {
        "laser": (0, 255, 0), "spray": (255, 255, 0),
        "drone": (255, 0, 255), "health": (255, 255, 255),
    }

    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind
        try:
            self.image = pygame.image.load(self.SPRITES[kind]).convert_alpha()
            self.image = pygame.transform.scale(self.image, (40, 40))
        except (FileNotFoundError, KeyError):
            self.image = pygame.Surface((32, 32))
            self.image.fill(self.FALLBACK_COLORS.get(kind, (255, 255, 255)))
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y += 1
        if self.rect.top > HEIGHT:
            self.kill()


# ── Drone ─────────────────────────────────────────────────────────────────────
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
            center=(player.rect.centerx + offset_x, player.rect.centery - 10))
        self.shoot_cooldown = 300
        self.last_shot = 0
        self.speed = 4

    def update(self, bullet_group):
        tx = self.player.rect.centerx + self.offset_x
        ty = self.player.rect.centery - 10
        self.rect.centerx += max(-self.speed, min(self.speed, tx - self.rect.centerx))
        self.rect.centery += max(-self.speed, min(self.speed, ty - self.rect.centery))
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.shoot_cooldown:
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, 0, -10, "laser"))
            self.last_shot = now


# ── Player ────────────────────────────────────────────────────────────────────
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
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
        self.max_health = 10
        self.health = self.max_health

    def update(self, keys, bullet_group):
        dx = dy = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += self.speed
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= self.speed
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += self.speed
        if dx and dy:
            dx = int(dx * 0.707)
            dy = int(dy * 0.707)
        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        if keys[pygame.K_SPACE]:
            now = pygame.time.get_ticks()
            if now - self.last_shot >= self.shoot_cooldown:
                self.shoot(bullet_group)
                self.last_shot = now

    def shoot(self, bullet_group):
        if self.weapon_mode == "laser":
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, 0, -10, "laser"))
        elif self.weapon_mode == "spray":
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top,  0, -10, "spray"))
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top, -3, -10, "spray"))
            bullet_group.add(Bullet(self.rect.centerx, self.rect.top,  3, -10, "spray"))


# ── Game States ───────────────────────────────────────────────────────────────
STATE_START    = "start"
STATE_PLAYING  = "playing"
STATE_GAMEOVER = "gameover"

spawn_interval   = 1000
powerup_interval = 8000
powerup_kinds    = ["laser", "spray", "drone", "health"]

def go_to_gameover():
    global game_state
    game_state = STATE_GAMEOVER
    pygame.mixer.music.load("deathmarch - 5-19-26, 1.35 PM_1.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)

score      = 0
music_track = 1

def reset_game():
    global player, players, bullets, enemy_bullets, enemies, underbosses
    global boss_group, powerups, drones, spawn_timer, powerup_timer, score, music_track
    player        = Player(WIDTH // 2, HEIGHT - 80)
    players       = pygame.sprite.Group(player)
    bullets       = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    enemies       = pygame.sprite.Group()
    underbosses   = pygame.sprite.Group()
    boss_group    = pygame.sprite.Group()
    powerups      = pygame.sprite.Group()
    drones        = pygame.sprite.Group()
    spawn_timer   = pygame.time.get_ticks()
    powerup_timer = pygame.time.get_ticks()
    score         = 0
    music_track   = 1
    global paused
    paused        = False
    pygame.mixer.music.load("starfighter-2- 4-25-26, 7.49 PM.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play()

reset_game()
game_state = STATE_START
paused     = False

# ── Game Loop ──────────────────────────────────────────────────────────────────
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == STATE_START:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                game_state = STATE_PLAYING

        elif game_state == STATE_PLAYING:
            if event.type == pygame.ACTIVEEVENT and not event.gain:
                paused = True
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                paused = not paused
            if event.type == MUSIC_END and music_track == 1:
                pygame.mixer.music.load("starfight.mp3")
                pygame.mixer.music.play(-1)
                music_track = 2
            # TODO: replace with proper wave trigger; B key spawns boss for testing
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b and not boss_group:
                    boss_group.add(Boss(WIDTH // 2, 130, player, enemy_bullets))
                if event.key == pygame.K_u:
                    kind = random.randint(1, 3)
                    underbosses.add(Underboss(WIDTH // 2, -80, player, enemy_bullets, kind))

        elif game_state == STATE_GAMEOVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    game_state = STATE_PLAYING
                elif event.key == pygame.K_q:
                    running = False

    # Stars draw on every state
    screen.fill((0, 0, 0))
    update_stars()
    for star in stars:
        pygame.draw.circle(screen, star_color, (star[0], star[1]), 1)

    # ── Start Screen ──────────────────────────────────────────────────────────
    if game_state == STATE_START:
        title = font_large.render("STARFIGHTER", True, (0, 200, 255))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        prompt = font_med.render("Press SPACE or ENTER to play", True, (200, 200, 200))
        screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        controls = font.render("WASD / Arrow Keys  •  SPACE to shoot", True, (140, 140, 140))
        screen.blit(controls, controls.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))

    # ── Playing ───────────────────────────────────────────────────────────────
    elif game_state == STATE_PLAYING:
        if not paused:
            current_time = pygame.time.get_ticks()

            if current_time - spawn_timer >= spawn_interval:
                spawn_timer = current_time
                count = random.randint(2, 4)
                xs = [int(WIDTH * (i + 1) / (count + 1)) for i in range(count)]
                for x in xs:
                    enemies.add(Enemy(x + random.randint(-20, 20), -20, player, enemy_bullets))

            if current_time - powerup_timer >= powerup_interval:
                powerup_timer = current_time
                if player.health > 1:
                    available = [k for k in powerup_kinds if not (
                        k == "laser" and player.weapon_mode == "laser" or
                        k == "spray" and player.weapon_mode == "spray" or
                        k == "drone" and len(drones) > 0 or
                        k == "health" and player.health >= player.max_health
                    )]
                else:
                    available = ["health"]
                if available:
                    powerups.add(PowerUp(random.randint(40, WIDTH - 40), -16, random.choice(available)))

            keys = pygame.key.get_pressed()
            player.update(keys, bullets)
            bullets.update()
            enemy_bullets.update()
            enemies.update()
            underbosses.update()
            boss_group.update()
            powerups.update()
            drones.update(bullets)

            # Player hit by enemy ships — takes 1 health
            if pygame.sprite.spritecollide(player, enemies, True):
                player.health -= 1
                if player.health <= 0:
                    go_to_gameover()

            # Player hit by enemy bullets — takes weapon upgrade first, then health
            if pygame.sprite.spritecollide(player, enemy_bullets, True):
                if player.weapon_mode != "laser" or len(drones) > 0:
                    player.weapon_mode = "laser"
                    drones.empty()
                else:
                    player.health -= 1
                    if player.health <= 0:
                        go_to_gameover()

            # Player bullets vs rank enemies (1 hit kill)
            for bullet in list(bullets):
                if pygame.sprite.spritecollide(bullet, enemies, True):
                    bullet.kill()
                    score += ENEMY_POINTS.get(bullet.kind, 10)

            # Player bullets vs underbosses (health-based)
            for bullet in list(bullets):
                for ub in pygame.sprite.spritecollide(bullet, underbosses, False):
                    bullet.kill()
                    if ub.hit():
                        ub.kill()
                        score += 200

            # Player bullets vs boss (health-based)
            for bullet in list(bullets):
                for b in pygame.sprite.spritecollide(bullet, boss_group, False):
                    bullet.kill()
                    if b.hit():
                        b.kill()
                        score += 1000

            # Player powerup collection
            for powerup in pygame.sprite.spritecollide(player, powerups, True):
                if powerup.kind in ("laser", "spray"):
                    player.weapon_mode = powerup.kind
                elif powerup.kind == "drone":
                    drones.empty()
                    drones.add(Drone(player, -40))
                    drones.add(Drone(player,  40))
                elif powerup.kind == "health":
                    player.health = min(player.health + 1, player.max_health)

        enemies.draw(screen)
        underbosses.draw(screen)
        boss_group.draw(screen)
        powerups.draw(screen)
        drones.draw(screen)
        players.draw(screen)
        bullets.draw(screen)
        enemy_bullets.draw(screen)

        for ub in underbosses:
            ub.draw_health_bar(screen)
        for b in boss_group:
            b.draw_health_bar(screen)

        screen.blit(font.render(f"HP: {player.health}", True, (255, 255, 255)), (10, 10))
        screen.blit(font.render(f"Weapon: {player.weapon_mode}", True, (200, 200, 0)), (10, 40))
        screen.blit(font.render(f"Score: {score}", True, (100, 220, 255)), (10, 70))

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 130))
            screen.blit(overlay, (0, 0))
            p_surf = font_large.render("PAUSED", True, (255, 255, 255))
            screen.blit(p_surf, p_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
            hint = font.render("Escape — Resume", True, (170, 170, 170))
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

    # ── Game Over ─────────────────────────────────────────────────────────────
    elif game_state == STATE_GAMEOVER:
        enemies.draw(screen)
        underbosses.draw(screen)
        boss_group.draw(screen)
        players.draw(screen)

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        go_surf = font_large.render("GAME OVER", True, (220, 40, 40))
        screen.blit(go_surf, go_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        score_surf = font_med.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        hint_surf = font.render("R — Restart    Q — Quit", True, (170, 170, 170))
        screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
