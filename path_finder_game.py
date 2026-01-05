import pygame
import math
import random
from enum import Enum
from dataclasses import dataclass

pygame.init()

# Screen settings
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 50)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (150, 0, 255)
DARK_PURPLE = (75, 0, 100)
NEON_GREEN = (0, 255, 100)
DARK_BLUE = (0, 20, 50)
GRAY = (150, 150, 150)


class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4
    LEVEL_COMPLETE = 5


@dataclass
class Vector:
    x: float
    y: float

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)

    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalize(self):
        l = self.length()
        if l > 0:
            return Vector(self.x / l, self.y / l)
        return Vector(0, 0)

    def distance_to(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Star:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def update(self, speed):
        self.z -= speed
        if self.z <= 0:
            self.z = 200
            self.x = random.uniform(0, SCREEN_WIDTH)
            self.y = random.uniform(0, SCREEN_HEIGHT)

    def draw(self, screen):
        if self.z <= 0:
            return

        scale = 1 - self.z / 200
        size = max(1, int(2 * scale))
        brightness = int(255 * scale)

        sx = int((self.x - SCREEN_WIDTH / 2) * scale + SCREEN_WIDTH / 2)
        sy = int((self.y - SCREEN_HEIGHT / 2) * scale + SCREEN_HEIGHT / 2)

        if 0 <= sx < SCREEN_WIDTH and 0 <= sy < SCREEN_HEIGHT:
            pygame.draw.circle(screen, (brightness, brightness, brightness), (sx, sy), size)


class Explosion:
    def __init__(self, x, y, size=20, color=ORANGE):
        self.x = x
        self.y = y
        self.size = size
        self.max_size = size
        self.lifetime = 20
        self.max_lifetime = 20
        self.color = color

    def update(self):
        self.lifetime -= 1
        self.size = self.max_size * (self.lifetime / self.max_lifetime)

    def draw(self, screen):
        if self.size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

    def is_alive(self):
        return self.lifetime > 0


class Projectile:
    def __init__(self, x, y, vx, vy, owner_type="player"):
        self.pos = Vector(x, y)
        self.vel = Vector(vx, vy)
        self.owner_type = owner_type
        self.lifetime = 300
        self.radius = 5 if owner_type == "player" else 3

    def update(self):
        self.pos = self.pos + self.vel
        self.lifetime -= 1

    def draw(self, screen):
        color = CYAN if self.owner_type == "player" else MAGENTA
        pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.pos.x), int(self.pos.y)), self.radius, 1)

    def is_alive(self):
        return (self.lifetime > 0 and
                -50 < self.pos.x < SCREEN_WIDTH + 50 and
                -50 < self.pos.y < SCREEN_HEIGHT + 50)


class Enemy:
    def __init__(self, x, y, enemy_type="basic"):
        self.pos = Vector(x, y)
        self.vel = Vector(random.uniform(-2, 2), random.uniform(-2, 2))
        self.enemy_type = enemy_type
        self.radius = 20 if enemy_type == "basic" else 30
        self.health = 50 if enemy_type == "basic" else 150
        self.max_health = self.health
        self.shoot_timer = 0
        self.shoot_cooldown = 60 if enemy_type == "basic" else 40
        self.rotation = 0
        self.score_value = 100 if enemy_type == "basic" else 300

    def update(self, player_pos):
        # Move towards player
        direction = (player_pos - self.pos).normalize()
        self.vel = direction * (1.5 if self.enemy_type == "basic" else 1.2)
        self.pos = self.pos + self.vel

        # Keep in bounds
        self.pos.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.pos.y))

        # Look at player
        dx = player_pos.x - self.pos.x
        dy = player_pos.y - self.pos.y
        self.rotation = math.atan2(dy, dx)

        self.shoot_timer += 1

    def draw(self, screen):
        # Enemy body
        if self.enemy_type == "basic":
            pygame.draw.circle(screen, RED, (int(self.pos.x), int(self.pos.y)), self.radius)
            pygame.draw.circle(screen, ORANGE, (int(self.pos.x), int(self.pos.y)), self.radius, 2)
        else:
            # Boss enemy
            for i in range(8):
                angle = (i / 8) * 2 * math.pi
                px = self.pos.x + self.radius * math.cos(angle)
                py = self.pos.y + self.radius * math.sin(angle)
                pygame.draw.line(screen, PURPLE, (int(self.pos.x), int(self.pos.y)), (int(px), int(py)), 3)
            pygame.draw.circle(screen, PURPLE, (int(self.pos.x), int(self.pos.y)), self.radius, 3)

        # Health bar
        bar_width = self.radius * 2
        bar_height = 5
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK,
                         (self.pos.x - bar_width / 2, self.pos.y - self.radius - 15, bar_width, bar_height))
        pygame.draw.rect(screen, RED,
                         (self.pos.x - bar_width / 2, self.pos.y - self.radius - 15, bar_width * health_ratio,
                          bar_height))

    def can_shoot(self):
        return self.shoot_timer >= self.shoot_cooldown

    def shoot(self):
        if self.can_shoot():
            self.shoot_timer = 0
            speed = 3
            vx = math.cos(self.rotation) * speed
            vy = math.sin(self.rotation) * speed
            return Projectile(self.pos.x, self.pos.y, vx, vy, "enemy")
        return None

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

    def is_alive(self):
        return self.health > 0


class Player:
    def __init__(self, x, y):
        self.pos = Vector(x, y)
        self.vel = Vector(0, 0)
        self.radius = 15
        self.max_speed = 5
        self.health = 100
        self.max_health = 100
        self.score = 0
        self.level = 1
        self.rotation = 0
        self.shoot_timer = 0
        self.shoot_cooldown = 10
        self.shield = 100
        self.max_shield = 100
        self.weapon_level = 1
        self.invincible_timer = 0

    def handle_input(self, keys):
        acceleration = 0.3

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.vel.y = max(self.vel.y - acceleration, -self.max_speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.vel.y = min(self.vel.y + acceleration, self.max_speed)
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel.x = max(self.vel.x - acceleration, -self.max_speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel.x = min(self.vel.x + acceleration, self.max_speed)

        # Friction
        self.vel.x *= 0.95
        self.vel.y *= 0.95

    def update(self, mouse_pos):
        self.pos = self.pos + self.vel

        # Keep in bounds
        self.pos.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.pos.x))
        self.pos.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.pos.y))

        # Look at mouse
        dx = mouse_pos[0] - self.pos.x
        dy = mouse_pos[1] - self.pos.y
        self.rotation = math.atan2(dy, dx)

        self.shoot_timer += 1
        self.invincible_timer = max(0, self.invincible_timer - 1)

    def draw(self, screen):
        # Draw shield if active
        if self.shield > 0:
            pygame.draw.circle(screen, CYAN, (int(self.pos.x), int(self.pos.y)), self.radius + 10, 2)

        # Draw player ship
        if self.invincible_timer % 10 < 5:
            angle1 = self.rotation
            angle2 = self.rotation + (2 * math.pi / 3)
            angle3 = self.rotation + (4 * math.pi / 3)

            points = [
                (self.pos.x + self.radius * math.cos(angle1),
                 self.pos.y + self.radius * math.sin(angle1)),
                (self.pos.x + self.radius * math.cos(angle2),
                 self.pos.y + self.radius * math.sin(angle2)),
                (self.pos.x + self.radius * math.cos(angle3),
                 self.pos.y + self.radius * math.sin(angle3))
            ]
            pygame.draw.polygon(screen, GREEN, points)
            pygame.draw.polygon(screen, NEON_GREEN, points, 2)

        # Health bar
        bar_width = 60
        bar_height = 8
        pygame.draw.rect(screen, BLACK,
                         (self.pos.x - bar_width / 2, self.pos.y - self.radius - 30, bar_width, bar_height))
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, GREEN,
                         (self.pos.x - bar_width / 2, self.pos.y - self.radius - 30, bar_width * health_ratio,
                          bar_height))

        # Shield bar
        pygame.draw.rect(screen, BLACK,
                         (self.pos.x - bar_width / 2, self.pos.y - self.radius - 18, bar_width, bar_height))
        shield_ratio = self.shield / self.max_shield
        pygame.draw.rect(screen, CYAN,
                         (self.pos.x - bar_width / 2, self.pos.y - self.radius - 18, bar_width * shield_ratio,
                          bar_height))

    def shoot(self):
        if self.shoot_timer >= self.shoot_cooldown:
            self.shoot_timer = 0
            speed = 7

            projectiles = []

            if self.weapon_level == 1:
                vx = math.cos(self.rotation) * speed
                vy = math.sin(self.rotation) * speed
                projectiles.append(Projectile(self.pos.x, self.pos.y, vx, vy, "player"))

            elif self.weapon_level == 2:
                for angle_offset in [-0.2, 0.2]:
                    angle = self.rotation + angle_offset
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    projectiles.append(Projectile(self.pos.x, self.pos.y, vx, vy, "player"))

            else:  # weapon_level >= 3
                for angle_offset in [-0.3, 0, 0.3]:
                    angle = self.rotation + angle_offset
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    projectiles.append(Projectile(self.pos.x, self.pos.y, vx, vy, "player"))

            return projectiles
        return []

    def take_damage(self, damage):
        if self.shield > 0:
            shield_damage = min(damage, self.shield)
            self.shield -= shield_damage
            remaining_damage = damage - shield_damage
        else:
            remaining_damage = damage

        if remaining_damage > 0:
            self.health -= remaining_damage
            self.invincible_timer = 30

        return self.health <= 0

    def heal(self, amount):
        self.health = min(self.health + amount, self.max_health)

    def recharge_shield(self, amount):
        self.shield = min(self.shield + amount, self.max_shield)

    def upgrade_weapon(self):
        if self.weapon_level < 3:
            self.weapon_level += 1


class PowerUp:
    def __init__(self, x, y, power_type):
        self.pos = Vector(x, y)
        self.power_type = power_type
        self.rotation = 0
        self.size = 10

    def update(self):
        self.rotation += 0.05

    def draw(self, screen):
        colors = {
            "health": GREEN,
            "shield": CYAN,
            "weapon": YELLOW
        }
        color = colors.get(self.power_type, WHITE)

        points = []
        for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
            x = self.pos.x + self.size * math.cos(angle + self.rotation)
            y = self.pos.y + self.size * math.sin(angle + self.rotation)
            points.append((x, y))

        pygame.draw.polygon(screen, color, points)
        pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), self.size, 2)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("⭐ SPACE WARRIOR ⭐ | Epic Space Battle")
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)

        self.state = GameState.MENU

        self.stars = [Star(random.uniform(0, SCREEN_WIDTH),
                           random.uniform(0, SCREEN_HEIGHT),
                           random.uniform(0, 200)) for _ in range(100)]

        self.reset_game()

    def reset_game(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.enemies = []
        self.projectiles = []
        self.explosions = []
        self.powerups = []
        self.waves_completed = 0
        self.enemy_spawn_timer = 0
        self.current_wave = 1
        self.wave_enemy_count = 0
        self.max_enemies_in_wave = 5 + self.current_wave * 2
        self.spawn_next_wave()

    def spawn_next_wave(self):
        self.current_wave += 1
        self.waves_completed = self.current_wave - 1
        self.player.level = self.current_wave

        if self.current_wave % 2 == 0:
            self.player.upgrade_weapon()
            self.player.health = self.player.max_health
            self.player.shield = self.player.max_shield

        self.max_enemies_in_wave = 5 + self.current_wave * 2
        self.wave_enemy_count = 0

    def spawn_enemy(self):
        edge = random.choice(['top', 'bottom', 'left', 'right'])

        if edge == 'top':
            x = random.uniform(0, SCREEN_WIDTH)
            y = -30
        elif edge == 'bottom':
            x = random.uniform(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT + 30
        elif edge == 'left':
            x = -30
            y = random.uniform(0, SCREEN_HEIGHT)
        else:
            x = SCREEN_WIDTH + 30
            y = random.uniform(0, SCREEN_HEIGHT)

        enemy_type = "basic" if random.random() > 0.15 else "boss"
        enemy = Enemy(x, y, enemy_type)
        self.enemies.append(enemy)
        self.wave_enemy_count += 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING

                if event.key == pygame.K_SPACE:
                    if self.state == GameState.MENU:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.GAME_OVER or self.state == GameState.LEVEL_COMPLETE:
                        self.reset_game()
                        self.state = GameState.PLAYING

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MENU:
                    self.state = GameState.PLAYING

        return True

    def update(self):
        if self.state == GameState.MENU:
            for star in self.stars:
                star.update(1)
            return

        if self.state != GameState.PLAYING:
            return

        for star in self.stars:
            star.update(0.5)

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(pygame.mouse.get_pos())

        if keys[pygame.K_LCTRL] or keys[pygame.K_SPACE]:
            projectiles = self.player.shoot()
            self.projectiles.extend(projectiles)

        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer > 40 and self.wave_enemy_count < self.max_enemies_in_wave:
            self.spawn_enemy()
            self.enemy_spawn_timer = 0

        for enemy in self.enemies[:]:
            enemy.update(self.player.pos)

            # Dushmanlar o'q otmaydi - faqat to'qnashish bilan zarar beradi

            distance = self.player.pos.distance_to(enemy.pos)
            if distance < self.player.radius + enemy.radius:
                self.player.take_damage(15)
                self.explosions.append(Explosion(int(self.player.pos.x), int(self.player.pos.y), 30, ORANGE))

        for projectile in self.projectiles[:]:
            projectile.update()

            if not projectile.is_alive():
                self.projectiles.remove(projectile)
                continue

            if projectile.owner_type == "player":
                for enemy in self.enemies[:]:
                    distance = projectile.pos.distance_to(enemy.pos)
                    if distance < projectile.radius + enemy.radius:
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)

                        if enemy.take_damage(25):
                            self.enemies.remove(enemy)
                            self.player.score += enemy.score_value
                            self.explosions.append(Explosion(int(enemy.pos.x), int(enemy.pos.y), 40, ORANGE))

                            if random.random() < 0.3:
                                power_type = random.choice(["health", "shield", "weapon"])
                                self.powerups.append(PowerUp(enemy.pos.x, enemy.pos.y, power_type))
                        break

        for powerup in self.powerups[:]:
            powerup.update()

            distance = self.player.pos.distance_to(powerup.pos)
            if distance < self.player.radius + powerup.size:
                if powerup.power_type == "health":
                    self.player.heal(50)
                elif powerup.power_type == "shield":
                    self.player.recharge_shield(50)
                elif powerup.power_type == "weapon":
                    self.player.upgrade_weapon()

                self.powerups.remove(powerup)
                self.explosions.append(Explosion(int(powerup.pos.x), int(powerup.pos.y), 20, YELLOW))

        for explosion in self.explosions[:]:
            explosion.update()
            if not explosion.is_alive():
                self.explosions.remove(explosion)

        if len(self.enemies) == 0 and self.wave_enemy_count >= self.max_enemies_in_wave:
            self.state = GameState.LEVEL_COMPLETE

        if self.player.health <= 0:
            self.state = GameState.GAME_OVER

    def draw_menu(self):
        self.screen.fill(DARK_BLUE)

        for star in self.stars:
            star.draw(self.screen)

        title = self.font_large.render("⭐ SPACE WARRIOR ⭐", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        subtitle = self.font_medium.render("Epic Space Battle", True, MAGENTA)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 170))

        instructions = [
            "BOSHQARUV:",
            "↑↓←→ yoki WASD - Harakatlanish",
            "SICHQONCHA - Nishonga olish",
            "CTRL yoki SPACE - O'q otish",
            "ESC - Pauza",
            "",
            "DUSHMAN NAVLARI:",
            "🔴 Asosiy dushmanlar",
            "🟣 Boss dushmanlar (kuchli)",
            "",
            "BOSHLASH UCHUN SPACE BOSING"
        ]

        y = 280
        for line in instructions:
            if line.startswith("BOSHQARUV") or line.startswith("DUSHMAN"):
                text = self.font_small.render(line, True, YELLOW)
            elif line == "":
                y += 20
                continue
            else:
                text = self.font_tiny.render(line, True, WHITE)

            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 40

    def draw_game(self):
        self.screen.fill(DARK_BLUE)

        for star in self.stars:
            star.draw(self.screen)

        for explosion in self.explosions:
            explosion.draw(self.screen)

        for powerup in self.powerups:
            powerup.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for projectile in self.projectiles:
            projectile.draw(self.screen)

        self.player.draw(self.screen)

        score_text = self.font_small.render(f"Ball: {self.player.score}", True, YELLOW)
        self.screen.blit(score_text, (20, 20))

        level_text = self.font_small.render(f"Davrasi: {self.player.level}", True, CYAN)
        self.screen.blit(level_text, (20, 70))

        enemies_text = self.font_small.render(f"Dushmanlar: {len(self.enemies)}/{self.max_enemies_in_wave}", True, RED)
        self.screen.blit(enemies_text, (SCREEN_WIDTH - 350, 20))

        weapon_text = self.font_small.render(f"Qurol Darajasi: {self.player.weapon_level}", True, MAGENTA)
        self.screen.blit(weapon_text, (SCREEN_WIDTH - 350, 70))

        pause_text = self.font_tiny.render("ESC - Pauza", True, GRAY)
        self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 20))

    def draw_paused(self):
        self.draw_game()

        pause_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pause_surface.set_alpha(150)
        pause_surface.fill(BLACK)
        self.screen.blit(pause_surface, (0, 0))

        paused_text = self.font_large.render("PAUZA", True, YELLOW)
        self.screen.blit(paused_text, (SCREEN_WIDTH // 2 - paused_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

        continue_text = self.font_small.render("ESC - Davom etish", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    def draw_level_complete(self):
        self.screen.fill(DARK_BLUE)

        for star in self.stars:
            star.draw(self.screen)

        complete_text = self.font_large.render("DAVRASI TO'LDIRDI!", True, GREEN)
        self.screen.blit(complete_text, (SCREEN_WIDTH // 2 - complete_text.get_width() // 2, 150))

        next_level_text = self.font_medium.render(f"Keyingi Davrasi: {self.current_wave + 1}", True, CYAN)
        self.screen.blit(next_level_text, (SCREEN_WIDTH // 2 - next_level_text.get_width() // 2, 280))

        score_text = self.font_small.render(f"Ball: {self.player.score}", True, YELLOW)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 380))

        continue_text = self.font_small.render("SPACE - Davom etish", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, 500))

    def draw_game_over(self):
        self.screen.fill(DARK_BLUE)

        for star in self.stars:
            star.draw(self.screen)

        gameover_text = self.font_large.render("O'YIN TUGADI", True, RED)
        self.screen.blit(gameover_text, (SCREEN_WIDTH // 2 - gameover_text.get_width() // 2, 150))

        final_score_text = self.font_medium.render(f"Akhirgi Ball: {self.player.score}", True, YELLOW)
        self.screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, 280))

        level_reached_text = self.font_small.render(f"Erisgan Davrasi: {self.player.level}", True, CYAN)
        self.screen.blit(level_reached_text, (SCREEN_WIDTH // 2 - level_reached_text.get_width() // 2, 380))

        restart_text = self.font_small.render("SPACE - Qayta o'ynash", True, WHITE)
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 500))

    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.PAUSED:
            self.draw_paused()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
