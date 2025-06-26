import pygame, random, math, time
from pygame.math import Vector2
from collections import Counter

WIDTH, HEIGHT = 1280, 720
NUM_BOIDS     = 100
MAX_SPEED     = 2.4
MAX_FORCE     = 0.06
NEIGH_DIST    = 55
SEPAR_DIST    = 22
AVOID_RADIUS  = 60   
OBST_BUFFER   = 70   
UI_W, UI_H    = 200, 100
FPS           = 60

BLACK  = (0, 0, 0)
WHITE  = (255, 255, 255)
GRAY   = (80, 80, 80)
GREEN  = (0, 160, 0)
RED    = (160, 0, 0)

CLUSTER_COLORS = [
    (255,  60,  60), ( 60, 255,  60), ( 60,  60, 255),
    (255, 255,  60), ( 60, 255, 255), (255,  60, 255),
    (255, 128,   0), (128,   0, 255), (  0, 128, 128)
]

class Boid:
    """Agent individual (triunghi orientat)"""
    def __init__(self, pos: Vector2):
        self.pos = Vector2(pos)
        ang = random.uniform(0, 2*math.pi)
        self.vel = Vector2(math.cos(ang), math.sin(ang)) * MAX_SPEED
        self.color = WHITE

    @staticmethod
    def _limit(vec: Vector2, lim: float) -> Vector2:
        if vec.length() > lim:
            vec.scale_to_length(lim)
        return vec

    def _separation(self, boids):
        neighbors = [b for b in boids if b is not self and self.pos.distance_to(b.pos) < SEPAR_DIST]
        if not neighbors:
            return Vector2()
        force = Vector2()
        for b in neighbors:
            diff = self.pos - b.pos
            dist = diff.length()
            if dist:
                force += diff.normalize() / dist  # ponderare 1/d
        force /= len(neighbors)
        if not force.length():
            return force
        desired = force.normalize() * MAX_SPEED
        return desired - self.vel

    def _alignment(self, boids):
        neighbors = [b for b in boids if b is not self and self.pos.distance_to(b.pos) < NEIGH_DIST]
        if not neighbors:
            return Vector2()
        avg_vel = sum((b.vel for b in neighbors), Vector2()) / len(neighbors)
        desired = avg_vel.normalize() * MAX_SPEED
        return desired - self.vel

    def _cohesion(self, boids):
        neighbors = [b for b in boids if b is not self and self.pos.distance_to(b.pos) < NEIGH_DIST]
        if not neighbors:
            return Vector2()
        center = sum((b.pos for b in neighbors), Vector2()) / len(neighbors)
        desired = (center - self.pos).normalize() * MAX_SPEED
        return desired - self.vel

    def _avoid_obstacles(self, obstacles):
        steer = Vector2()
        for obs in obstacles:
            diff = self.pos - obs.pos
            dist = diff.length()
            if dist < obs.radius + OBST_BUFFER and dist:
                steer += diff.normalize() / dist
        if not steer.length():
            return steer
        desired = steer.normalize() * MAX_SPEED
        return desired - self.vel

    def update(self, boids, obstacles, rules):
        steering = Vector2()
        if rules["separation"]:
            steering += self._limit(self._separation(boids), MAX_FORCE*1.5)  # pondere ↑
        if rules["alignment"]:
            steering += self._limit(self._alignment(boids), MAX_FORCE)
        if rules["cohesion"]:
            steering += self._limit(self._cohesion(boids), MAX_FORCE)
        steering += self._limit(self._avoid_obstacles(obstacles), MAX_FORCE*2)

        self.vel += steering
        self.vel = self._limit(self.vel, MAX_SPEED)
        self.pos += self.vel
        self.pos.x %= WIDTH
        self.pos.y %= HEIGHT

    def draw(self, surf):
        tip, left, right = Vector2(10,0), Vector2(-6,4), Vector2(-6,-4)
        ang = math.atan2(self.vel.y, self.vel.x)
        c, s = math.cos(ang), math.sin(ang)
        def rot(p):
            return Vector2(p.x*c - p.y*s, p.x*s + p.y*c) + self.pos
        pygame.draw.polygon(surf, self.color, [rot(tip), rot(left), rot(right)])

class Obstacle:
    def __init__(self, pos: Vector2, radius: int = 25):
        self.pos = Vector2(pos)
        self.radius = radius
    def draw(self, surf):
        pygame.draw.circle(surf, GRAY, (int(self.pos.x), int(self.pos.y)), self.radius, 2)


def make_boids(n: int) -> list[Boid]:
    out = []
    for _ in range(n):
        while True:
            x, y = random.uniform(0, WIDTH), random.uniform(0, HEIGHT)
            if x > WIDTH-UI_W and y > HEIGHT-UI_H:
                continue  # nu pune în zona UI
            out.append(Boid((x, y)))
            break
    return out

def make_obstacles() -> list[Obstacle]:
    obs = [
        Obstacle((random.uniform(0, WIDTH-UI_W), random.uniform(0, HEIGHT-UI_H)),
                 random.randint(20, 60))
        for _ in range(5)
    ]
    # obstacol mare pentru panoul UI
    ui_c = Vector2(WIDTH-UI_W/2, HEIGHT-UI_H/2)
    ui_r = int(math.hypot(UI_W, UI_H)/2 + 10)
    obs.append(Obstacle(ui_c, ui_r))
    return obs

def build_buttons(font):
    labels = [
        ("Separare", "separation"),
        ("Aliniere",  "alignment"),
        ("Coeziune",  "cohesion")
    ]
    btns = []
    x0, y0 = WIDTH-UI_W+10, HEIGHT-UI_H+10
    for i, (text, key) in enumerate(labels):
        rect = pygame.Rect(x0, y0 + i*30, 130, 25)
        btns.append((rect, text, key))
    return btns

_color_idx = 0

def _next_color():
    global _color_idx
    col = CLUSTER_COLORS[_color_idx % len(CLUSTER_COLORS)]
    _color_idx += 1
    return col

def color_clusters(boids: list[Boid]):
    thresh = NEIGH_DIST * 1.3
    visited = set()
    clusters = []
    for i in range(len(boids)):
        if i in visited:
            continue
        stack, comp = [i], []
        visited.add(i)
        while stack:
            j = stack.pop(); comp.append(j)
            for k in range(len(boids)):
                if k not in visited and boids[j].pos.distance_to(boids[k].pos) < thresh:
                    visited.add(k); stack.append(k)
        clusters.append(comp)

    for comp in clusters:
        # determină culoarea dominantă & mărimea fiecărei culori
        cnt = Counter(boids[i].color for i in comp)
        # ignoră culoarea WHITE la decizie, dacă există alte culori
        if len(cnt) == 1 and WHITE in cnt:
            # cluster complet nou → alocă o culoare nouă
            new_col = _next_color()
            for idx in comp:
                boids[idx].color = new_col
        else:
            # alege culoarea cu număr maxim de boids
            dominant = max(cnt.items(), key=lambda x: x[1])[0]
            for idx in comp:
                boids[idx].color = dominant


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Boids")
    clock  = pygame.time.Clock()
    font   = pygame.font.Font(None, 24)

    boids      = make_boids(NUM_BOIDS)
    obstacles  = make_obstacles()         
    rules      = {"separation": True,
                  "alignment":  True,
                  "cohesion":   True}
    buttons    = build_buttons(font)
    start_time = time.time()

    running = True
    while running:
        # ­­­­­­­­­­­­­­­­­­­­ evenimente ­­­­­­­­­­­­­­­­­­­­
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                for rect, _, key in buttons:
                    if rect.collidepoint(mx, my):
                        rules[key] = not rules[key]
                        break

        # ­­­­­­­­­­­­­­­­­­­­ logică ­­­­­­­­­­­­­­­­­­­­
        for b in boids:
            b.update(boids, obstacles, rules)
        color_clusters(boids)

        # ­­­­­­­­­­­­­­­­­­­­ desen ­­­­­­­­­­­­­­­­­­­­
        screen.fill(BLACK)

        for b in boids:
            b.draw(screen)

        for obs in obstacles[:-1]:        # fără obstacolul-UI
            obs.draw(screen)

        # panou UI
        ui_rect = pygame.Rect(WIDTH-UI_W, HEIGHT-UI_H, UI_W, UI_H)
        pygame.draw.rect(screen, GRAY, ui_rect)
        for rect, text, key in buttons:
            col = GREEN if rules[key] else RED
            pygame.draw.rect(screen, col, rect)
            screen.blit(font.render(text, True, WHITE),
                        (rect.x + 5, rect.y + 4))

        # text informativ
        sec     = int(time.time() - start_time)
        active  = ', '.join(k.capitalize() for k, v in rules.items() if v) or "Niciuna"
        info    = f"Boids: {len(boids)} | Reguli: {active} | Timp: {sec}s"
        screen.blit(font.render(info, True, WHITE), (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()