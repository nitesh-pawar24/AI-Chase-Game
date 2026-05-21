import pygame
import random
import time
import os
import math
from settings import *
from pathfinding import a_star, best_first_search, heuristic

# ─── Sound Manager ─────────────────────────────────────────────────────────────

class SoundManager:
    """Loads and plays all game sounds. Gracefully degrades if files are missing."""

    SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sounds")

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.mixer.init()
        self._sfx = {}
        self._load()
        self._footstep_timer = 0.0
        self._footstep_delay = 0.28   # seconds between footstep sounds

    def _load(self):
        files = {
            "menu_music":     "menu_music.wav",
            "player_won":     "player_won.wav",
            "player_caught":  "player_caught.wav",
            "time_up":        "time_up.wav",
            "footstep":       "footstep.wav",
            "countdown_tick": "countdown_tick.wav",
            "countdown_go":   "countdown_go.wav",
        }
        for key, fname in files.items():
            path = os.path.join(self.SOUNDS_DIR, fname)
            try:
                self._sfx[key] = pygame.mixer.Sound(path)
            except Exception:
                self._sfx[key] = None

    def play_menu_music(self):
        if self._sfx.get("menu_music"):
            pygame.mixer.stop()
            self._sfx["menu_music"].play(loops=-1)   # infinite loop

    def stop_music(self):
        pygame.mixer.stop()

    def play(self, key):
        snd = self._sfx.get(key)
        if snd:
            snd.play()

    def try_footstep(self, moved: bool):
        """Call every frame. Plays a footstep if the player just moved."""
        now = time.time()
        if moved and now - self._footstep_timer > self._footstep_delay:
            self.play("footstep")
            self._footstep_timer = now


# Global sound manager (created once)
_sound = SoundManager()

# ─── Animated Particle Background ──────────────────────────────────────────────

def draw_menu_background(surface, bg_image=None):
    """Minimal dark background with a subtle maze-grid pattern."""
    w, h = surface.get_size()
    surface.fill((8, 8, 14))

    # Subtle grid lines to hint at maze structure
    grid_spacing = 28
    line_color = (16, 16, 26)
    for x in range(0, w, grid_spacing):
        pygame.draw.line(surface, line_color, (x, 0), (x, h))
    for y in range(0, h, grid_spacing):
        pygame.draw.line(surface, line_color, (0, y), (w, y))

    # Thin border frame
    pygame.draw.rect(surface, (30, 30, 50), (0, 0, w, h), 2)


# ─── Animated Menu Background ──────────────────────────────────────────────────

class MenuBackground:
    """
    Generates a real maze (recursive back-tracker) and draws it as dim
    glowing walls on a dark background.  A green dot (player) wanders
    toward random goals while a red dot (AI) chases it through the actual
    carved passages — thematic and clearly maze-game without copying the
    gameplay UI.
    """
    CELL     = 35
    P_SPEED  = 0.30   # seconds per step — player
    AI_SPEED = 0.22   # seconds per step — AI (faster = threatening)

    def __init__(self, w, h):
        self.w    = w
        self.h    = h
        self.cols = w // self.CELL
        self.rows = h // self.CELL
        self._gen_maze()
        self._reset_dots()
        self.t = 0.0

    # ── maze generation (iterative back-tracker) ──────────────────────────────

    def _gen_maze(self):
        rows, cols = self.rows, self.cols
        # h_walls[r][c] = wall exists BELOW cell (r,c)
        # v_walls[r][c] = wall exists to the RIGHT of cell (r,c)
        self.h_walls = [[True] * cols for _ in range(rows)]
        self.v_walls = [[True] * cols for _ in range(rows)]

        visited = [[False] * cols for _ in range(rows)]
        stack   = [(0, 0)]
        visited[0][0] = True

        while stack:
            r, c = stack[-1]
            dirs = [(dr, dc) for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]
                    if 0 <= r+dr < rows and 0 <= c+dc < cols
                    and not visited[r+dr][c+dc]]
            if not dirs:
                stack.pop()
                continue
            dr, dc = random.choice(dirs)
            nr, nc = r + dr, c + dc
            # Remove the wall between (r,c) and (nr,nc)
            if dr ==  1: self.h_walls[r][c]   = False   # wall below (r,c)
            if dr == -1: self.h_walls[nr][nc]  = False   # wall below (nr,nc)
            if dc ==  1: self.v_walls[r][c]   = False   # wall right of (r,c)
            if dc == -1: self.v_walls[r][nc]   = False   # wall right of (nr,nc)
            visited[nr][nc] = True
            stack.append((nr, nc))

    # ── pathfinding through carved passages ───────────────────────────────────

    def _passages(self, r, c):
        """Adjacent cells reachable through removed walls."""
        out = []
        if r+1 < self.rows  and not self.h_walls[r][c]:      out.append((r+1, c))
        if r-1 >= 0         and not self.h_walls[r-1][c]:    out.append((r-1, c))
        if c+1 < self.cols  and not self.v_walls[r][c]:      out.append((r, c+1))
        if c-1 >= 0         and not self.v_walls[r][c-1]:    out.append((r, c-1))
        return out

    def _bfs(self, start, goal):
        from collections import deque
        q = deque([(start, [start])])
        seen = {start}
        while q:
            cur, path = q.popleft()
            if cur == goal:
                return path
            for nb in self._passages(*cur):
                if nb not in seen:
                    seen.add(nb)
                    q.append((nb, path + [nb]))
        return [start]

    # ── dot placement & reset ─────────────────────────────────────────────────

    def _reset_dots(self):
        self.player = (0, 0)
        self.ai     = (self.rows - 1, self.cols - 1)
        self._new_player_goal()
        self.p_timer  = 0.0
        self.ai_timer = 0.0

    def _new_player_goal(self):
        self.goal = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
        self.p_path = self._bfs(self.player, self.goal)[1:]

    # ── update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        self.t += dt

        # Player follows BFS path to its goal
        self.p_timer += dt
        if self.p_timer >= self.P_SPEED:
            self.p_timer = 0.0
            if self.p_path:
                self.player = self.p_path.pop(0)
            if not self.p_path:
                self._new_player_goal()

        # AI chases player via BFS
        self.ai_timer += dt
        if self.ai_timer >= self.AI_SPEED:
            self.ai_timer = 0.0
            path = self._bfs(self.ai, self.player)
            if len(path) > 1:
                self.ai = path[1]
            if self.ai == self.player:
                # Caught — teleport AI to far corner, pick new goal
                self.ai = (self.rows-1-self.player[0], self.cols-1-self.player[1])
                self._new_player_goal()

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface):
        cell = self.CELL
        rows, cols = self.rows, self.cols
        w, h = self.w, self.h

        surface.fill((5, 5, 10))

        # ── maze walls (dim blue glow) ────────────────────────────────────────
        WALL      = (30,  50, 110)
        WALL_GLOW = (15,  25,  55)

        # Outer border glow then sharp line
        pygame.draw.rect(surface, WALL_GLOW, (0, 0, cols*cell, rows*cell), 4)
        pygame.draw.rect(surface, WALL,      (0, 0, cols*cell, rows*cell), 1)

        # Interior horizontal walls (between row r and r+1)
        for r in range(rows - 1):
            for c in range(cols):
                if self.h_walls[r][c]:
                    x1, y = c * cell, (r + 1) * cell
                    pygame.draw.line(surface, WALL_GLOW, (x1, y), (x1+cell, y), 3)
                    pygame.draw.line(surface, WALL,      (x1, y), (x1+cell, y), 1)

        # Interior vertical walls (between col c and c+1)
        for r in range(rows):
            for c in range(cols - 1):
                if self.v_walls[r][c]:
                    x, y1 = (c + 1) * cell, r * cell
                    pygame.draw.line(surface, WALL_GLOW, (x, y1), (x, y1+cell), 3)
                    pygame.draw.line(surface, WALL,      (x, y1), (x, y1+cell), 1)

        # ── goal (dim yellow pulse) ───────────────────────────────────────────
        gr, gc = self.goal
        gx = gc * cell + cell // 2
        gy = gr * cell + cell // 2
        pulse = int(3 + 2 * math.sin(self.t * 4))
        pygame.draw.circle(surface, (160, 130, 0), (gx, gy), pulse + 3)
        pygame.draw.circle(surface, (220, 190, 40), (gx, gy), pulse)

        # ── player dot (green) ────────────────────────────────────────────────
        pr, pc = self.player
        px = pc * cell + cell // 2
        py = pr * cell + cell // 2
        pygame.draw.circle(surface, (20, 120, 40),  (px, py), 8)
        pygame.draw.circle(surface, (60, 230, 100), (px, py), 5)

        # ── AI dot (red) ──────────────────────────────────────────────────────
        ar, ac = self.ai
        ax = ac * cell + cell // 2
        ay = ar * cell + cell // 2
        pygame.draw.circle(surface, (120, 20, 20),  (ax, ay), 8)
        pygame.draw.circle(surface, (230, 60, 60),  (ax, ay), 5)

        # ── dark overlay so menu text stays readable ──────────────────────────
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, (35, 55, 130), (0, 0, w, h), 2)


# ─── Menu ──────────────────────────────────────────────────────────────────────

def draw_glowing_text(surface, font, text, color, pos, glow_color=None, glow_radius=3):
    """Render text with a simple drop shadow."""
    cx, cy = pos
    shadow = font.render(text, True, (0, 0, 0))
    surface.blit(shadow, shadow.get_rect(center=(cx + 2, cy + 2)))
    main_s = font.render(text, True, color)
    surface.blit(main_s, main_s.get_rect(center=(cx, cy)))


def draw_button(surface, rect, text, font, text_color, border_color, hover=False, t=0):
    """Draw a clean minimal button — flat fill, sharp border, centered label."""
    x, y, w, h = rect
    fill = (28, 28, 42) if not hover else (40, 40, 60)
    pygame.draw.rect(surface, fill, rect)
    border_w = 2 if not hover else 2
    pygame.draw.rect(surface, border_color, rect, border_w)
    txt = font.render(text, True, text_color)
    surface.blit(txt, txt.get_rect(center=(x + w // 2, y + h // 2)))


def show_menu():
    pygame.init()
    W, H = 560, 500
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("AI Chase Game - Menu")

    f_title  = pygame.font.SysFont("Verdana", 28, bold=True)
    f_sub    = pygame.font.SysFont("Verdana", 16, bold=True)
    f_small  = pygame.font.SysFont("Verdana", 13)
    clock    = pygame.time.Clock()

    # Animated background
    bg = MenuBackground(W, H)

    # Start menu music
    _sound.play_menu_music()

    # ── Difficulty selection ──────────────────────────────────────────────────
    diff = None
    prev_time = time.time()
    while not diff:
        now = time.time()
        dt = now - prev_time
        prev_time = now
        t = now

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: diff = "Easy"
                if event.key == pygame.K_2: diff = "Hard"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if easy_rect.collidepoint(mx, my):  diff = "Easy"
                if hard_rect.collidepoint(mx, my):  diff = "Hard"

        mx, my = pygame.mouse.get_pos()

        # Button rects
        btn_w, btn_h = 420, 58
        bx = (W - btn_w) // 2
        easy_rect = pygame.Rect(bx, 210, btn_w, btn_h)
        hard_rect = pygame.Rect(bx, 295, btn_w, btn_h)

        # Draw
        bg.update(dt)
        bg.draw(screen)

        # Title
        draw_glowing_text(screen, f_title, "AI CHASE GAME",
                          (230, 230, 240), (W // 2, 90))

        # Thin divider
        pygame.draw.line(screen, (50, 50, 80), (60, 120), (W - 60, 120), 1)

        # Section label
        draw_glowing_text(screen, f_sub, "SELECT DIFFICULTY",
                          (140, 180, 220), (W // 2, 155))

        # Easy button
        hover_easy = easy_rect.collidepoint(mx, my)
        draw_button(screen, easy_rect, "1.  Easy", f_sub,
                    (180, 240, 180), (60, 180, 90), hover_easy, t)

        # Hard button
        hover_hard = hard_rect.collidepoint(mx, my)
        draw_button(screen, hard_rect, "2.  Hard", f_sub,
                    (240, 160, 160), (200, 70, 70), hover_hard, t)

        # Hint
        hint = f_small.render("press  1 / 2  or  click", True, (70, 80, 110))
        screen.blit(hint, hint.get_rect(center=(W // 2, 400)))

        pygame.display.flip()
        clock.tick(60)

    # ── Sector selection ──────────────────────────────────────────────────────
    size = None
    prev_time = time.time()
    while not size:
        now = time.time()
        dt = now - prev_time
        prev_time = now
        t = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return None, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: size = 10
                if event.key == pygame.K_2: size = 15
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if s1_rect.collidepoint(mx, my): size = 10
                if s2_rect.collidepoint(mx, my): size = 15

        mx, my = pygame.mouse.get_pos()

        btn_w, btn_h = 420, 58
        bx = (W - btn_w) // 2
        s1_rect = pygame.Rect(bx, 220, btn_w, btn_h)
        s2_rect = pygame.Rect(bx, 305, btn_w, btn_h)

        bg.update(dt)
        bg.draw(screen)

        # Difficulty badge
        diff_color = (100, 210, 120) if diff == "Easy" else (210, 90, 90)
        badge_text = f"[ {diff.upper()} ]"
        badge_surf = f_sub.render(badge_text, True, diff_color)
        bw, bh = badge_surf.get_size()
        badge_rect = pygame.Rect(0, 0, bw + 24, bh + 12)
        badge_rect.center = (W // 2, 88)
        pygame.draw.rect(screen, (20, 20, 32), badge_rect)
        pygame.draw.rect(screen, diff_color, badge_rect, 1)
        screen.blit(badge_surf, badge_surf.get_rect(center=badge_rect.center))

        # Thin divider
        pygame.draw.line(screen, (50, 50, 80), (60, 118), (W - 60, 118), 1)

        # Section label
        draw_glowing_text(screen, f_sub, "SELECT SECTOR",
                          (140, 180, 220), (W // 2, 150))

        hover_s1 = s1_rect.collidepoint(mx, my)
        draw_button(screen, s1_rect, "1.  Sector 1  ( 10 × 10 )", f_sub,
                    (190, 215, 245), (80, 140, 210), hover_s1, t)

        hover_s2 = s2_rect.collidepoint(mx, my)
        draw_button(screen, s2_rect, "2.  Sector 2  ( 15 × 15 )", f_sub,
                    (210, 190, 245), (140, 90, 210), hover_s2, t)

        hint = f_small.render("press  1 / 2  or  click", True, (70, 80, 110))
        screen.blit(hint, hint.get_rect(center=(W // 2, 410)))

        pygame.display.flip()
        clock.tick(60)

    _sound.stop_music()
    return diff, size


# ─── Game ──────────────────────────────────────────────────────────────────────

class Game:
    def __init__(self, difficulty, grid_size):
        pygame.init()
        stats = DIFFICULTY_DATA[difficulty][grid_size]

        self.difficulty = difficulty
        self.grid_size  = grid_size
        self.obs_count  = stats["obs"]
        self.ai_interval = stats["speed"]
        self.time_limit  = stats["time"]

        self.screen_dim = self.grid_size * CELL_SIZE
        self.screen = pygame.display.set_mode((self.screen_dim, self.screen_dim + 70))
        pygame.display.set_caption(f"AI Chase Game: {difficulty} – Sector {grid_size}×{grid_size}")

        # Scale fonts so they fit on small (10x10=400px) and large (15x15=600px) screens
        hud_size = 14 if self.screen_dim <= 400 else 18
        msg_size = 18 if self.screen_dim <= 400 else 24
        self.font     = pygame.font.SysFont("Verdana", hud_size, bold=True)
        self.big_font = pygame.font.SysFont("Verdana", msg_size, bold=True)
        self.clock    = pygame.time.Clock()

        self.running     = True
        self.game_over   = False
        self.result_text  = ""
        self.result_color = WHITE

        # Sound flags to avoid repeated triggers
        self._end_sound_played = False

        self.load_assets()
        self.reset_game()

    # ── Asset loading ─────────────────────────────────────────────────────────

    def load_assets(self):
        self.use_assets = True
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
            self.img_player = pygame.image.load(os.path.join(path, "player.jpg")).convert_alpha()
            self.img_player = pygame.transform.scale(self.img_player, (CELL_SIZE - 8, CELL_SIZE - 8))
            self.img_ai     = pygame.image.load(os.path.join(path, "ai.jpg")).convert_alpha()
            self.img_ai     = pygame.transform.scale(self.img_ai, (CELL_SIZE - 8, CELL_SIZE - 8))
            self.img_goal   = pygame.image.load(os.path.join(path, "goal.jpg")).convert_alpha()
            self.img_goal   = pygame.transform.scale(self.img_goal, (CELL_SIZE - 8, CELL_SIZE - 8))
        except Exception:
            self.use_assets = False

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset_game(self):
        now = time.time()
        self.reset_time       = now
        self.start_time       = now + 3.99  # 3s countdown + 1s for "GO!"
        self.last_ai_move     = self.start_time
        self.last_player_move = self.start_time
        self.player_delay     = 0.12
        self.game_over        = False
        self.result_text      = ""
        self._end_sound_played = False
        self._prev_player_pos  = None
        self._time_warning_played = False
        self.time_left         = self.time_limit
        self._last_countdown_sec = 4 # Track seconds to play beep once per sec
        self.generate_valid_map()

    def generate_valid_map(self):
        # Choose pathfinding algorithm based on difficulty
        path_fn = a_star if self.difficulty == "Hard" else best_first_search
        while True:
            all_cells = [(r, c) for r in range(self.grid_size) for c in range(self.grid_size)]
            self.player_pos = random.choice(all_cells)
            self.goal_pos   = random.choice([c for c in all_cells if heuristic(c, self.player_pos) > 4])
            self.ai_pos     = random.choice([c for c in all_cells
                                             if heuristic(c, self.player_pos) > 5 and c != self.goal_pos])
            occupied  = {self.player_pos, self.goal_pos, self.ai_pos}
            available = [c for c in all_cells if c not in occupied]
            self.obstacles = set(random.sample(available, self.obs_count))
            if (path_fn(self.grid_size, self.ai_pos, self.player_pos, self.obstacles) and
                    a_star(self.grid_size, self.player_pos, self.goal_pos, self.obstacles)):
                break

    # ── Update logic ──────────────────────────────────────────────────────────

    def update(self, player_moved: bool):
        if self.game_over:
            return

        now = time.time()
        if now < self.start_time:
            return  # Freeze game during countdown

        # Footstep sound
        _sound.try_footstep(player_moved)

        elapsed = now - self.start_time
        self.time_left = max(0, self.time_limit - int(elapsed))

        if self.time_left <= 0:
            self.end("Time Up! (LOST)", RED, "time_up")

        if time.time() - self.last_ai_move > self.ai_interval:
            # Easy → Greedy Best First Search  |  Hard → A*
            if self.difficulty == "Hard":
                path = a_star(self.grid_size, self.ai_pos, self.player_pos, self.obstacles)
            else:
                path = best_first_search(self.grid_size, self.ai_pos, self.player_pos, self.obstacles)
            if path:
                self.ai_pos = path[0]
            self.last_ai_move = time.time()

        if self.player_pos == self.ai_pos:
            self.end("AI Caught You! (LOST)", RED, "player_caught")
        elif self.player_pos == self.goal_pos:
            score = self.time_left * 10
            self.end(f"You Won! Score: {score}", (0, 220, 80), "player_won")

    def end(self, msg, color, sound_key):
        self.game_over    = True
        self.result_text  = msg
        self.result_color = color
        if not self._end_sound_played:
            _sound.play(sound_key)
            self._end_sound_played = True

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw_grid(self):
        self.screen.fill((255, 255, 255))   # white game background
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (200, 200, 210), rect, 1)   # light grid lines
                if (r, c) in self.obstacles:
                    pygame.draw.rect(self.screen, (100, 100, 120), rect)  # dark obstacles
                    pygame.draw.rect(self.screen, (70, 70, 90), rect, 1)

    def draw_hud(self):
        ui_y   = self.screen_dim
        ui_rect = pygame.Rect(0, ui_y, self.screen_dim, 70)
        pygame.draw.rect(self.screen, (20, 20, 35), ui_rect)
        pygame.draw.line(self.screen, (60, 80, 180), (0, ui_y), (self.screen_dim, ui_y), 2)

        time_color = (255, 80, 80) if self.time_left <= 5 else (200, 220, 255)
        # Short label for narrow screens (10x10 = 400px), full label for wider ones
        if self.screen_dim <= 400:
            label = f"TIME: {self.time_left}s  |  {self.difficulty}"
        else:
            label = f"TIME: {self.time_left}s   |   MODE: {self.difficulty}"
        status = self.font.render(label, True, time_color)
        self.screen.blit(status, (14, ui_y + 24))

    def draw_message_box(self):
        overlay = pygame.Surface((self.screen_dim, self.screen_dim), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        # Auto-shrink message font until it fits within the screen width
        font_size = 18 if self.screen_dim <= 400 else 24
        while font_size >= 10:
            mf = pygame.font.SysFont("Verdana", font_size, bold=True)
            msg_surf = mf.render(self.result_text, True, self.result_color)
            if msg_surf.get_width() <= self.screen_dim - 20:
                break
            font_size -= 1

        sf = pygame.font.SysFont("Verdana", max(10, font_size - 4), bold=True)
        sub_text = "R: Restart  |  M: Menu" if self.screen_dim <= 400 else "R: Restart  |  M: Back to Menu"
        sub_surf = sf.render(sub_text, True, (200, 200, 220))

        # Clamp box width to screen
        box_w = min(max(msg_surf.get_width(), sub_surf.get_width()) + 40, self.screen_dim - 10)
        box_rect = pygame.Rect(0, 0, box_w, 110)
        box_rect.center = (self.screen_dim // 2, self.screen_dim // 2)

        box_surf = pygame.Surface((box_w, 110), pygame.SRCALPHA)
        box_surf.fill((20, 20, 40, 220))
        self.screen.blit(box_surf, box_rect.topleft)
        pygame.draw.rect(self.screen, self.result_color, box_rect, 2, border_radius=12)

        msg_rect = msg_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2 - 18))
        sub_rect = sub_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2 + 28))
        self.screen.blit(msg_surf, msg_rect)
        self.screen.blit(sub_surf, sub_rect)

    def draw_countdown(self):
        now = time.time()
        if now >= self.start_time: return
        
        rem = self.start_time - now
        current_sec = int(math.ceil(rem))
        
        # Play sound once per countdown step
        if current_sec != self._last_countdown_sec:
            if current_sec > 0:
                _sound.play("countdown_tick")
            else:
                _sound.play("countdown_go")
            self._last_countdown_sec = current_sec

        if rem > 1.0:
            text = str(int(rem))
            color = (255, 200, 50)
            scale = 1.0 + (rem % 1.0) * 0.5  # Pop effect on each second
        else:
            text = "GO!"
            color = (50, 255, 100)
            scale = 1.0 + (rem % 1.0) * 1.5  # Fast zoom for GO!
            
        overlay = pygame.Surface((self.screen_dim, self.screen_dim), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        # Render and scale text
        surf = self.big_font.render(text, True, color)
        w, h = surf.get_size()
        scaled_surf = pygame.transform.scale(surf, (int(w * scale), int(h * scale)))
        rect = scaled_surf.get_rect(center=(self.screen_dim // 2, self.screen_dim // 2))
        
        # Glow
        for ox, oy in [(-2,0),(2,0),(0,-2),(0,2)]:
            sh = self.big_font.render(text, True, (0, 0, 0))
            sh = pygame.transform.scale(sh, (int(w * scale), int(h * scale)))
            self.screen.blit(sh, sh.get_rect(center=(self.screen_dim // 2 + ox, self.screen_dim // 2 + oy)))
            
        self.screen.blit(scaled_surf, rect)

    def draw_danger_zone(self):
        dist = heuristic(self.player_pos, self.ai_pos)
        if dist <= 3 and not self.game_over and time.time() >= self.start_time:
            # Pulse intensity based on how close AI is
            intensity = int((4 - dist) * 20 + 20 * math.sin(time.time() * 10))
            intensity = max(0, min(120, intensity))
            
            overlay = pygame.Surface((self.screen_dim, self.screen_dim), pygame.SRCALPHA)
            # Red vignette around screen edges
            pygame.draw.rect(overlay, (255, 0, 0, intensity), overlay.get_rect(), width=15)
            self.screen.blit(overlay, (0, 0))

    def draw(self):
        self.draw_grid()
        if self.use_assets:
            self.screen.blit(self.img_goal,   (self.goal_pos[1]   * CELL_SIZE + 4, self.goal_pos[0]   * CELL_SIZE + 4))
            self.screen.blit(self.img_player, (self.player_pos[1] * CELL_SIZE + 4, self.player_pos[0] * CELL_SIZE + 4))
            self.screen.blit(self.img_ai,     (self.ai_pos[1]     * CELL_SIZE + 4, self.ai_pos[0]     * CELL_SIZE + 4))
        else:
            pygame.draw.rect(self.screen, (255, 215, 0), (self.goal_pos[1]   * CELL_SIZE + 4, self.goal_pos[0]   * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8))
            pygame.draw.rect(self.screen, GREEN,         (self.player_pos[1] * CELL_SIZE + 4, self.player_pos[0] * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8))
            pygame.draw.rect(self.screen, RED,           (self.ai_pos[1]     * CELL_SIZE + 4, self.ai_pos[0]     * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8))
        
        self.draw_danger_zone()
        self.draw_hud()
        
        if time.time() < self.start_time:
            self.draw_countdown()
        elif self.game_over:
            self.draw_message_box()
            
        pygame.display.flip()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while self.running:
            player_moved = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_m:
                        return "MENU"

            if not self.game_over and time.time() >= self.start_time:
                keys = pygame.key.get_pressed()
                if time.time() - self.last_player_move > self.player_delay:
                    nr, nc = self.player_pos
                    if   keys[pygame.K_UP]    or keys[pygame.K_w]: nr -= 1
                    elif keys[pygame.K_DOWN]  or keys[pygame.K_s]: nr += 1
                    elif keys[pygame.K_LEFT]  or keys[pygame.K_a]: nc -= 1
                    elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: nc += 1

                    if (nr, nc) != self.player_pos:
                        if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                            if (nr, nc) not in self.obstacles:
                                self.player_pos = (nr, nc)
                                self.last_player_move = time.time()
                                player_moved = True

            self.update(player_moved)
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    while True:
        d, s = show_menu()
        if d and s:
            game = Game(d, s)
            result = game.run()
            if result != "MENU":
                break
        else:
            break