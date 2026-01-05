import pygame
import math
import random
import heapq
from enum import Enum
from dataclasses import dataclass

pygame.init()

# Screen settings
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# Colors
BACKGROUND = (15, 20, 30)
GRID_COLOR = (30, 40, 60)
PLAYER_COLOR = (0, 200, 255)  # A nuqta - ko'k
TARGET_COLOR = (255, 50, 100)  # B nuqta - qizil
OBSTACLE_COLOR = (255, 200, 50)
PATH_COLOR = (50, 255, 150)
TEXT_COLOR = (240, 240, 240)
BUTTON_COLOR = (70, 130, 200)
BUTTON_HOVER_COLOR = (100, 160, 230)
TRAIL_COLOR = (100, 200, 255, 100)


class GameState(Enum):
    MENU = 1
    PLAYING = 2
    LEVEL_COMPLETE = 3
    GAME_OVER = 4
    EDITOR = 5


@dataclass
class Node:
    x: int
    y: int
    g: float = 0
    h: float = 0
    parent: object = None

    def __lt__(self, other):
        return (self.g + self.h) < (other.g + other.h)

    @property
    def f(self):
        return self.g + self.h


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(2, 5)
        self.speed_x = random.uniform(-0.5, 0.5)
        self.speed_y = random.uniform(-0.5, 0.5)
        self.lifetime = random.randint(20, 40)
        self.max_lifetime = self.lifetime

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.lifetime -= 1
        self.size *= 0.95

    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color = (*self.color[:3], alpha) if len(self.color) == 4 else self.color
        if len(color) == 3:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.size))
        else:
            s = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (int(self.size), int(self.size)), int(self.size))
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))

    def is_alive(self):
        return self.lifetime > 0


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.speed = 5
        self.trail = []
        self.max_trail_length = 50
        self.particles = []
        self.color = PLAYER_COLOR

    def move(self, dx, dy, obstacles):
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        # Check boundaries
        if new_x < self.radius or new_x > SCREEN_WIDTH - self.radius:
            new_x = self.x
        if new_y < self.radius or new_y > SCREEN_HEIGHT - self.radius:
            new_y = self.y

        # Check obstacle collisions
        can_move = True
        for obstacle in obstacles:
            if self.check_collision(obstacle, new_x, new_y):
                can_move = False
                break

        if can_move:
            self.x = new_x
            self.y = new_y

            # Add to trail
            self.trail.append((self.x, self.y))
            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)

            # Create particles
            if abs(dx) > 0 or abs(dy) > 0:
                for _ in range(2):
                    self.particles.append(Particle(
                        self.x + random.uniform(-10, 10),
                        self.y + random.uniform(-10, 10),
                        (100, 200, 255, 150)
                    ))

    def check_collision(self, obstacle, x=None, y=None):
        if x is None:
            x = self.x
        if y is None:
            y = self.y

        if obstacle.type == "rect":
            rect = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)
            player_rect = pygame.Rect(x - self.radius, y - self.radius,
                                      self.radius * 2, self.radius * 2)
            return rect.colliderect(player_rect)
        elif obstacle.type == "circle":
            dx = x - obstacle.x
            dy = y - obstacle.y
            distance = math.sqrt(dx * dx + dy * dy)
            return distance < self.radius + obstacle.radius

        return False

    def update_particles(self):
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)

    def draw(self, screen):
        # Draw trail
        for i, (trail_x, trail_y) in enumerate(self.trail):
            alpha = int(100 * (i / len(self.trail)))
            size = self.radius * (i / len(self.trail))
            if size > 0:
                s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*self.color, alpha), (int(size), int(size)), int(size))
                screen.blit(s, (int(trail_x - size), int(trail_y - size)))

        # Draw particles
        for particle in self.particles:
            particle.draw(screen)

        # Draw player
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)

        # Draw "A" inside
        font = pygame.font.Font(None, 30)
        text = font.render("A", True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)


class Target:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.pulse = 0
        self.pulse_speed = 0.05
        self.color = TARGET_COLOR
        self.particles = []

    def update(self):
        self.pulse = (self.pulse + self.pulse_speed) % (2 * math.pi)

        # Create particles
        if random.random() < 0.1:
            angle = random.uniform(0, 2 * math.pi)
            distance = self.radius + random.uniform(5, 15)
            px = self.x + math.cos(angle) * distance
            py = self.y + math.sin(angle) * distance
            self.particles.append(Particle(px, py, (*self.color, 150)))

        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if not particle.is_alive():
                self.particles.remove(particle)

    def draw(self, screen):
        # Draw particles
        for particle in self.particles:
            particle.draw(screen)

        # Draw pulsing circle
        pulse_size = self.radius + math.sin(self.pulse) * 5
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(pulse_size))
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), int(pulse_size), 2)

        # Draw "B" inside
        font = pygame.font.Font(None, 35)
        text = font.render("B", True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)


class Obstacle:
    def __init__(self, x, y, width, height, obstacle_type="rect"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.radius = width // 2 if obstacle_type == "circle" else 0
        self.color = OBSTACLE_COLOR
        self.rotation = 0
        self.rotating = random.random() > 0.7
        self.rotation_speed = random.uniform(-0.02, 0.02)

    def update(self):
        if self.rotating:
            self.rotation += self.rotation_speed

    def draw(self, screen):
        if self.type == "rect":
            # Draw rectangle with rotation
            points = []
            for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                rx = dx * self.width / 2
                ry = dy * self.height / 2

                # Rotate
                if self.rotation != 0:
                    cos_r = math.cos(self.rotation)
                    sin_r = math.sin(self.rotation)
                    x_rot = rx * cos_r - ry * sin_r
                    y_rot = rx * sin_r + ry * cos_r
                    points.append((self.x + x_rot, self.y + y_rot))
                else:
                    points.append((self.x + rx, self.y + ry))

            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, (255, 200, 100), points, 2)

        elif self.type == "circle":
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 200, 100), (int(self.x), int(self.y)), self.radius, 2)


class PathFinder:
    @staticmethod
    def heuristic(a, b):
        return abs(a.x - b.x) + abs(a.y - b.y)

    @staticmethod
    def a_star(start, goal, obstacles, grid_size=20):
        """A* algorithm for path finding"""
        open_set = []
        closed_set = set()
        start_node = Node(start.x // grid_size, start.y // grid_size)
        goal_node = Node(goal.x // grid_size, goal.y // grid_size)

        heapq.heappush(open_set, start_node)

        while open_set:
            current = heapq.heappop(open_set)

            if (current.x, current.y) == (goal_node.x, goal_node.y):
                path = []
                while current:
                    path.append((current.x * grid_size + grid_size // 2,
                                 current.y * grid_size + grid_size // 2))
                    current = current.parent
                return path[::-1]

            closed_set.add((current.x, current.y))

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
                neighbor_x = current.x + dx
                neighbor_y = current.y + dy

                # Check if neighbor is valid
                if (neighbor_x < 0 or neighbor_y < 0 or
                        neighbor_x * grid_size > SCREEN_WIDTH or
                        neighbor_y * grid_size > SCREEN_HEIGHT):
                    continue

                # Check if neighbor is in obstacle
                in_obstacle = False
                px = neighbor_x * grid_size + grid_size // 2
                py = neighbor_y * grid_size + grid_size // 2
                for obstacle in obstacles:
                    if obstacle.type == "rect":
                        rect = pygame.Rect(obstacle.x - obstacle.width / 2, obstacle.y - obstacle.height / 2,
                                           obstacle.width, obstacle.height)
                        if rect.collidepoint(px, py):
                            in_obstacle = True
                            break
                    elif obstacle.type == "circle":
                        dx_obs = px - obstacle.x
                        dy_obs = py - obstacle.y
                        if math.sqrt(dx_obs * dx_obs + dy_obs * dy_obs) < obstacle.radius:
                            in_obstacle = True
                            break

                if in_obstacle:
                    continue

                if (neighbor_x, neighbor_y) in closed_set:
                    continue

                neighbor = Node(neighbor_x, neighbor_y)
                neighbor.g = current.g + math.sqrt(dx * dx + dy * dy)
                neighbor.h = PathFinder.heuristic(neighbor, goal_node)
                neighbor.parent = current

                # Check if neighbor is in open_set with lower g
                in_open = False
                for node in open_set:
                    if (node.x, node.y) == (neighbor.x, neighbor.y):
                        in_open = True
                        if neighbor.g < node.g:
                            node.g = neighbor.g
                            node.parent = neighbor.parent
                        break

                if not in_open:
                    heapq.heappush(open_set, neighbor)

        return []


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("A dan B ga: Professional Yo'l Topish O'yini")
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)

        self.state = GameState.MENU
        self.levels = []
        self.current_level = 0
        self.score = 0
        self.time_limit = 60  # seconds
        self.time_remaining = self.time_limit
        self.show_path = False
        self.path_points = []
        self.path_finder = PathFinder()

        self.create_levels()
        self.reset_level()

    def create_levels(self):
        # Level 1 - Easy
        self.levels.append({
            "player_pos": Point(100, SCREEN_HEIGHT // 2),
            "target_pos": Point(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2),
            "obstacles": [
                Obstacle(400, 300, 200, 50, "rect"),
                Obstacle(600, 600, 150, 50, "rect"),
                Obstacle(800, 400, 80, 80, "circle"),
            ],
            "time_limit": 60
        })

        # Level 2 - Medium
        self.levels.append({
            "player_pos": Point(SCREEN_WIDTH // 2, 50),
            "target_pos": Point(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50),
            "obstacles": [
                Obstacle(300, 200, 250, 40, "rect"),
                Obstacle(500, 400, 40, 300, "rect"),
                Obstacle(700, 300, 100, 100, "circle"),
                Obstacle(900, 600, 200, 40, "rect"),
                Obstacle(200, 600, 120, 120, "circle"),
            ],
            "time_limit": 75
        })

        # Level 3 - Hard
        self.levels.append({
            "player_pos": Point(100, 100),
            "target_pos": Point(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100),
            "obstacles": [
                Obstacle(300, 150, 200, 40, "rect"),
                Obstacle(500, 300, 100, 100, "circle"),
                Obstacle(700, 150, 40, 300, "rect"),
                Obstacle(300, 500, 300, 40, "rect"),
                Obstacle(800, 600, 120, 120, "circle"),
                Obstacle(1000, 300, 200, 40, "rect"),
                Obstacle(400, 700, 150, 50, "rect"),
            ],
            "time_limit": 90
        })

        # Level 4 - Very Hard
        self.levels.append({
            "player_pos": Point(SCREEN_WIDTH - 100, 100),
            "target_pos": Point(100, SCREEN_HEIGHT - 100),
            "obstacles": [
                Obstacle(200, 200, 150, 150, "circle"),
                Obstacle(400, 100, 40, 400, "rect"),
                Obstacle(600, 300, 200, 40, "rect"),
                Obstacle(800, 500, 100, 100, "circle"),
                Obstacle(1000, 200, 40, 300, "rect"),
                Obstacle(300, 600, 250, 40, "rect"),
                Obstacle(700, 700, 150, 50, "rect"),
                Obstacle(500, 450, 80, 80, "circle"),
            ],
            "time_limit": 120
        })

        # Level 5 - Expert
        self.levels.append({
            "player_pos": Point(SCREEN_WIDTH // 2, 100),
            "target_pos": Point(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100),
            "obstacles": [
                Obstacle(200, 300, 180, 180, "circle"),
                Obstacle(500, 200, 40, 300, "rect"),
                Obstacle(700, 400, 200, 40, "rect"),
                Obstacle(900, 600, 120, 120, "circle"),
                Obstacle(1100, 300, 40, 400, "rect"),
                Obstacle(300, 600, 250, 40, "rect"),
                Obstacle(600, 700, 200, 50, "rect"),
                Obstacle(400, 450, 100, 100, "circle"),
                Obstacle(800, 200, 150, 40, "rect"),
                Obstacle(1000, 500, 40, 200, "rect"),
            ],
            "time_limit": 150
        })

    def reset_level(self):
        level = self.levels[self.current_level]
        self.player = Player(level["player_pos"].x, level["player_pos"].y)
        self.target = Target(level["target_pos"].x, level["target_pos"].y)
        self.obstacles = level["obstacles"][:]
        self.time_limit = level["time_limit"]
        self.time_remaining = self.time_limit
        self.show_path = False
        self.update_path()

    def update_path(self):
        self.path_points = self.path_finder.a_star(
            Point(int(self.player.x), int(self.player.y)),
            Point(int(self.target.x), int(self.target.y)),
            self.obstacles
        )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                    elif self.state == GameState.MENU:
                        return False
                    else:
                        self.state = GameState.MENU

                if event.key == pygame.K_SPACE:
                    if self.state == GameState.MENU:
                        self.state = GameState.PLAYING
                        self.current_level = 0
                        self.score = 0
                        self.reset_level()
                    elif self.state == GameState.LEVEL_COMPLETE:
                        if self.current_level < len(self.levels) - 1:
                            self.current_level += 1
                            self.reset_level()
                            self.state = GameState.PLAYING
                        else:
                            self.state = GameState.MENU
                    elif self.state == GameState.GAME_OVER:
                        self.state = GameState.PLAYING
                        self.reset_level()

                if event.key == pygame.K_p and self.state == GameState.PLAYING:
                    self.show_path = not self.show_path

                if event.key == pygame.K_r and self.state == GameState.PLAYING:
                    self.reset_level()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.MENU:
                    self.state = GameState.PLAYING
                    self.current_level = 0
                    self.score = 0
                    self.reset_level()

        return True

    def update(self):
        if self.state != GameState.PLAYING:
            return

        # Update time
        self.time_remaining -= 1 / FPS
        if self.time_remaining <= 0:
            self.state = GameState.GAME_OVER

        # Handle player movement
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1

        if dx != 0 or dy != 0:
            self.player.move(dx, dy, self.obstacles)
            self.update_path()

        # Update obstacles
        for obstacle in self.obstacles:
            obstacle.update()

        # Update target
        self.target.update()

        # Update player particles
        self.player.update_particles()

        # Check if reached target
        distance = math.sqrt((self.player.x - self.target.x) ** 2 +
                             (self.player.y - self.target.y) ** 2)
        if distance < self.player.radius + self.target.radius:
            # Level complete
            level_score = int(self.time_remaining * 10) + 500
            self.score += level_score
            self.state = GameState.LEVEL_COMPLETE

    def draw_grid(self):
        grid_size = 40
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)

    def draw_menu(self):
        self.screen.fill(BACKGROUND)

        # Title
        title = self.font_large.render("A dan B ga: Yo'l Topish", True, PLAYER_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        subtitle = self.font_medium.render("Professional O'yin", True, TARGET_COLOR)
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

        # Instructions
        instructions = [
            "MAQSAD: Har bir bosqichda A nuqtasidan B nuqtasiga yetib boring",
            "To'siqlarga tegmaslik kerak!",
            "",
            "BOSHQARUV:",
            "W, A, S, D yoki ↑↓←→ - Harakat",
            "P - Eng qisqa yo'lni ko'rsatish/yashirish",
            "R - Bosqichni qayta boshlash",
            "ESC - Menyuga qaytish",
            "",
            "Har bir bosqichda vaqt chegarasi bor",
            "Tezroq yakunlasangiz, ko'proq ball olasiz!",
            "",
            "Boshlash uchun SPACE yoki sichqoncha tugmasini bosing"
        ]

        y = 280
        for line in instructions:
            if line.startswith("MAQSAD") or line.startswith("BOSHQARUV"):
                text = self.font_small.render(line, True, (255, 255, 100))
            elif line == "":
                y += 20
                continue
            else:
                text = self.font_tiny.render(line, True, TEXT_COLOR)

            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 40

        # Draw sample level preview
        pygame.draw.circle(self.screen, PLAYER_COLOR, (SCREEN_WIDTH // 2 - 200, 650), 15)
        pygame.draw.circle(self.screen, TARGET_COLOR, (SCREEN_WIDTH // 2 + 200, 650), 20)

        # Draw "A" and "B"
        font = pygame.font.Font(None, 30)
        text_a = font.render("A", True, (255, 255, 255))
        text_b = font.render("B", True, (255, 255, 255))
        self.screen.blit(text_a, (SCREEN_WIDTH // 2 - 200 - 8, 650 - 12))
        self.screen.blit(text_b, (SCREEN_WIDTH // 2 + 200 - 8, 650 - 12))

    def draw_game(self):
        self.screen.fill(BACKGROUND)

        # Draw grid
        self.draw_grid()

        # Draw path if enabled
        if self.show_path and len(self.path_points) > 1:
            for i in range(len(self.path_points) - 1):
                pygame.draw.line(self.screen, PATH_COLOR,
                                 self.path_points[i], self.path_points[i + 1], 3)

            # Draw path points
            for point in self.path_points:
                pygame.draw.circle(self.screen, PATH_COLOR, point, 5)

        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        # Draw target
        self.target.draw(self.screen)

        # Draw player
        self.player.draw(self.screen)

        # Draw HUD
        level_text = self.font_small.render(f"Bosqich: {self.current_level + 1}/{len(self.levels)}", True, TEXT_COLOR)
        self.screen.blit(level_text, (20, 20))

        score_text = self.font_small.render(f"Ball: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (20, 60))

        time_text = self.font_small.render(f"Vaqt: {max(0, int(self.time_remaining))}s",
                                           True, TEXT_COLOR)
        self.screen.blit(time_text, (SCREEN_WIDTH - 200, 20))

        path_hint = self.font_tiny.render("P - Yo'lni ko'rsatish", True, TEXT_COLOR)
        self.screen.blit(path_hint, (SCREEN_WIDTH - 200, 60))

        restart_hint = self.font_tiny.render("R - Qayta boshlash", True, TEXT_COLOR)
        self.screen.blit(restart_hint, (SCREEN_WIDTH - 200, 90))

        # Draw instructions overlay
        if self.time_remaining > self.time_limit - 3:  # Show for first 3 seconds
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            level_num = self.font_medium.render(f"Bosqich {self.current_level + 1}", True, PLAYER_COLOR)
            self.screen.blit(level_num, (SCREEN_WIDTH // 2 - level_num.get_width() // 2,
                                         SCREEN_HEIGHT // 2 - 50))

            if self.current_level == 0:
                hint = self.font_small.render("W, A, S, D yoki strelkachalar bilan harakatlaning", True, TEXT_COLOR)
                self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                                        SCREEN_HEIGHT // 2 + 20))

    def draw_level_complete(self):
        self.screen.fill(BACKGROUND)

        # Title
        complete_text = self.font_large.render("BOSQICH YAKUNLANDI!", True, TARGET_COLOR)
        self.screen.blit(complete_text, (SCREEN_WIDTH // 2 - complete_text.get_width() // 2, 150))

        # Stats
        level_text = self.font_medium.render(f"Bosqich: {self.current_level + 1}/{len(self.levels)}", True, TEXT_COLOR)
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 280))

        score_gained = int(self.time_remaining * 10) + 500
        score_text = self.font_medium.render(f"Ball: +{score_gained}", True, TEXT_COLOR)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 350))

        total_score_text = self.font_medium.render(f"Umumiy ball: {self.score}", True, TEXT_COLOR)
        self.screen.blit(total_score_text, (SCREEN_WIDTH // 2 - total_score_text.get_width() // 2, 420))

        # Next level or finish
        if self.current_level < len(self.levels) - 1:
            next_text = self.font_small.render("SPACE - Keyingi bosqich", True, TEXT_COLOR)
            self.screen.blit(next_text, (SCREEN_WIDTH // 2 - next_text.get_width() // 2, 550))
        else:
            congrats_text = self.font_medium.render("TABRIKLAYMIZ! Barcha bosqichlarni yakunladingiz!", True,
                                                    PLAYER_COLOR)
            self.screen.blit(congrats_text, (SCREEN_WIDTH // 2 - congrats_text.get_width() // 2, 500))

            finish_text = self.font_small.render("SPACE - Menyuga qaytish", True, TEXT_COLOR)
            self.screen.blit(finish_text, (SCREEN_WIDTH // 2 - finish_text.get_width() // 2, 600))

    def draw_game_over(self):
        self.screen.fill(BACKGROUND)

        # Title
        gameover_text = self.font_large.render("VAQT TUGADI!", True, (255, 50, 50))
        self.screen.blit(gameover_text, (SCREEN_WIDTH // 2 - gameover_text.get_width() // 2, 150))

        # Stats
        level_text = self.font_medium.render(f"Yakunlangan bosqich: {self.current_level + 1}/{len(self.levels)}", True,
                                             TEXT_COLOR)
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 280))

        score_text = self.font_medium.render(f"Umumiy ball: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 350))

        # Restart option
        restart_text = self.font_small.render("SPACE - Qayta boshlash", True, TEXT_COLOR)
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 500))

        menu_text = self.font_small.render("ESC - Menyuga qaytish", True, TEXT_COLOR)
        self.screen.blit(menu_text, (SCREEN_WIDTH // 2 - menu_text.get_width() // 2, 550))

    def draw(self):
        if self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
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