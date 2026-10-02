import os, sys, math, random
SMOKE = '--smoke-test' in sys.argv
if SMOKE:
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame

W, H, T, FPS = 960, 540, 40, 60
GRAV, JUMP = 0.6, 11.5
SOLID = set('#=C^V')
KNAMES = ['Sandglass Kingdom', 'Frostpine Kingdom', 'Ember Ridge']
THEMES = [
    dict(sky1=(250, 150, 80), sky2=(255, 215, 150), ground=(200, 150, 90), top=(235, 195, 125), dark=(150, 105, 60), liquid=(80, 140, 200)),
    dict(sky1=(160, 205, 240), sky2=(230, 245, 255), ground=(225, 232, 245), top=(255, 255, 255), dark=(150, 175, 205), liquid=(50, 110, 190)),
    dict(sky1=(50, 8, 12), sky2=(140, 40, 30), ground=(90, 40, 35), top=(150, 70, 50), dark=(50, 20, 20), liquid=(255, 110, 20)),
]
KEYS = {'left': (pygame.K_LEFT, pygame.K_a), 'right': (pygame.K_RIGHT, pygame.K_d),
        'jump': (pygame.K_SPACE, pygame.K_UP, pygame.K_w), 'cap': (pygame.K_x, pygame.K_j),
        'enter': (pygame.K_RETURN, pygame.K_KP_ENTER)}
HINTS = {None: 'Space: jump   X: throw Brim (capture enemies, bounce on him mid-air)',
         'toad': 'SPRINGTOAD  -  hold Space to charge a super jump   X: release',
         'beetle': 'ROCKBEETLE  -  spike-proof   Space: charge (smash cracked blocks)   X: release',
         'kite': 'PUFFKITE  -  glide slowly, ride wind vents upward   X: release'}


# ---------------------------------------------------------------- levels
def blank(w, h): return [['.'] * w for _ in range(h)]


def fill(g, x0, y0, x1, y1, ch):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = ch


def row(x0, x1, y): return [(x, y) for x in range(x0, x1 + 1)]


def k_sand():
    g = blank(80, 14); fill(g, 0, 12, 79, 13, '#'); fill(g, 79, 0, 79, 11, '#')
    fill(g, 20, 6, 23, 6, '#')
    fill(g, 26, 10, 27, 11, '#')
    fill(g, 30, 9, 32, 9, '#'); fill(g, 33, 3, 36, 3, '#')
    fill(g, 37, 10, 38, 10, '#'); fill(g, 39, 9, 52, 9, '#'); fill(g, 40, 12, 51, 12, '^')
    fill(g, 55, 10, 55, 11, 'C')
    fill(g, 64, 8, 66, 8, '#'); fill(g, 68, 3, 70, 3, '#')
    fill(g, 72, 7, 78, 7, '#'); fill(g, 72, 8, 72, 11, 'C')
    coins = (row(10, 13, 11) + row(20, 23, 5) + row(26, 27, 9) + row(30, 32, 8) + row(41, 50, 8) +
             row(57, 62, 11) + row(64, 66, 7) + row(73, 78, 6) + [(17, 8), (18, 7), (19, 8)])
    return dict(g=g, start=(2, 11), ship=(5, 12), coins=coins,
                moons=[(22, 5), (35, 2), (46, 11), (69, 2), (75, 11)],
                enemies=[('toad', 16, 11), ('beetle', 36, 11), ('toad', 61, 11)], plats=[])


def k_frost():
    g = blank(60, 30); fill(g, 0, 28, 59, 29, '#'); fill(g, 59, 0, 59, 27, '#')
    fill(g, 45, 28, 58, 28, '=')
    fill(g, 20, 28, 44, 28, '~')
    for x in (23, 28, 33, 38, 42): fill(g, x, 27, x + 1, 27, '#')
    g[28][14] = 'V'; g[28][55] = 'V'
    for x, y in ((16, 26), (18, 24), (15, 22), (18, 20), (15, 18), (18, 16)): fill(g, x, y, x + 1, y, '#')
    fill(g, 2, 24, 4, 24, '#'); fill(g, 6, 21, 8, 21, '#'); fill(g, 2, 18, 4, 18, '#')
    fill(g, 48, 21, 51, 21, '#')
    fill(g, 51, 25, 54, 25, '#'); fill(g, 51, 26, 51, 27, 'C'); fill(g, 54, 26, 54, 27, '#')
    fill(g, 56, 11, 58, 11, '#')
    coins = (row(2, 4, 23) + row(6, 8, 20) + row(2, 4, 17) + [(x, 26) for x in (23, 24, 28, 29, 33, 34, 38, 39, 42, 43)] +
             row(48, 51, 20) + row(56, 58, 10) + [(14, y) for y in (10, 14, 18, 22)] + row(46, 50, 27))
    return dict(g=g, start=(2, 27), ship=(4, 28), coins=coins,
                moons=[(14, 6), (29, 20), (50, 20), (53, 27), (57, 10)],
                enemies=[('kite', 11, 25), ('kite', 22, 14), ('kite', 57, 25), ('toad', 46, 27), ('beetle', 49, 27)],
                plats=[])


def k_ember():
    g = blank(80, 14); fill(g, 0, 12, 79, 13, '#'); fill(g, 79, 0, 79, 11, '#')
    fill(g, 14, 12, 19, 13, '~')
    fill(g, 21, 5, 23, 5, '#')
    fill(g, 24, 10, 25, 10, '#'); fill(g, 27, 9, 38, 9, '#'); fill(g, 28, 12, 37, 12, '^')
    fill(g, 40, 12, 46, 13, '~')
    fill(g, 51, 10, 53, 10, '#')
    fill(g, 55, 8, 60, 8, '#'); fill(g, 55, 9, 55, 11, 'C'); fill(g, 60, 9, 60, 11, '#')
    fill(g, 67, 5, 68, 11, '#')
    fill(g, 70, 12, 78, 13, '~')
    coins = (row(14, 19, 8) + row(21, 23, 4) + row(29, 36, 8) + row(40, 46, 7) + row(56, 59, 7) +
             row(62, 65, 11) + row(70, 77, 8))
    return dict(g=g, start=(2, 11), ship=(5, 12), coins=coins,
                moons=[(22, 4), (33, 11), (43, 2), (58, 11), (67, 4)],
                enemies=[('toad', 10, 11), ('beetle', 23, 11), ('beetle', 48, 11), ('toad', 63, 11)],
                plats=[(14, 10, 2, 14, 18), (40, 10, 2, 40, 45), (71, 10, 2, 70, 76)])


BUILD = [k_sand, k_frost, k_ember]


class Body:
    def __init__(s, x, y, w, h):
        s.x, s.y, s.w, s.h = float(x), float(y), w, h
        s.vx = s.vy = 0.0
        s.on_ground = False; s.ground_ch = '.'; s.plat = None; s.face = 1
        s.smash = False; s.hitwall = False

    def rect(s): return pygame.Rect(int(s.x), int(s.y), s.w, s.h)


ESIZE = {'toad': (30, 26), 'beetle': (36, 26), 'kite': (32, 28)}


class Enemy(Body):
    def __init__(s, kind, tx, ty):
        w, h = ESIZE[kind]
        super().__init__(tx * T + (T - w) / 2, (ty + 1) * T - h, w, h)
        s.kind = kind; s.sp = (s.x, s.y); s.reset()

    def reset(s):
        s.x, s.y = s.sp; s.vx = s.vy = 0.0; s.stun = 0; s.captured = False
        s.timer = 60; s.charge = 0; s.dash = 0; s.hx, s.hy = s.sp; s.t = 0; s.face = -1; s.smash = False; s.plat = None


class Player(Body):
    def __init__(s):
        super().__init__(0, 0, 24, 34)
        s.hearts = 3; s.inv = 0; s.coy = 0; s.jbuf = 0; s.bounced = False; s.full = False
        s.capture = None; s.cap = None; s.safe = (0, 0); s.anim = 0.0


class Cap:
    def __init__(s, x, y, d): s.x, s.y = x, y; s.vx = d * 10; s.state = 'out'; s.t = 15; s.spin = 0.0

    def rect(s): return pygame.Rect(int(s.x) - 13, int(s.y) - 8, 26, 16)


class Moon:
    def __init__(s, i, x, y): s.i, s.x, s.y = i, x, y

    def rect(s): return pygame.Rect(s.x - 14, s.y - 14, 28, 28)


class Plat:
    def __init__(s, tx, ty, wt, a, b):
        s.x, s.y, s.w, s.h = float(tx * T), ty * T, wt * T, 14
        s.x0, s.x1, s.vx, s.dx = a * T, b * T, 1.5, 0.0

    def update(s):
        s.x += s.vx; s.dx = s.vx
        if s.x < s.x0 or s.x > s.x1: s.vx = -s.vx


class Level:
    def __init__(s, k, got):
        d = BUILD[k]()
        s.g = d['g']; s.h = len(s.g); s.w = len(s.g[0])
        s.start = d['start']; sx, sy = d['ship']
        s.ship = pygame.Rect(sx * T, sy * T - 70, 200, 70)
        s.coins = [pygame.Rect(x * T + 12, y * T + 12, 16, 16) for x, y in d['coins']]
        s.moons = [Moon(i, x * T + 20, y * T + 20) for i, (x, y) in enumerate(d['moons']) if (k, i) not in got]
        s.enemies = [Enemy(*e) for e in d['enemies']]
        s.plats = [Plat(*p) for p in d['plats']]
        s.smashed = []
        s.wind = set()
        for ty in range(s.h):
            for tx in range(s.w):
                if s.g[ty][tx] == 'V':
                    for i in range(1, 23):
                        if ty - i < 0 or s.g[ty - i][tx] in SOLID: break
                        s.wind.add((tx, ty - i))

    def get(s, tx, ty):
        if tx < 0 or tx >= s.w: return '#'
        if ty < 0 or ty >= s.h: return '.'
        return s.g[ty][tx]

    def cells(s, r):
        for ty in range(r.top // T, (r.bottom - 1) // T + 1):
            for tx in range(r.left // T, (r.right - 1) // T + 1):
                yield tx, ty

    def collide(s, b, axis):
        r = b.rect()
        for tx, ty in list(s.cells(r)):
            ch = s.get(tx, ty)
            if ch not in SOLID: continue
            tr = pygame.Rect(tx * T, ty * T, T, T)
            if not r.colliderect(tr): continue
            if axis == 0 and ch == 'C' and b.smash:
                s.g[ty][tx] = '.'; s.smashed.append((tx * T + 20, ty * T + 20)); continue
            # push out on the side the body's centre is on (penetration-based, not velocity-based)
            if axis == 0:
                if r.centerx < tr.centerx:
                    b.x = tr.left - b.w
                    if b.vx > 0: b.vx = 0
                else:
                    b.x = tr.right
                    if b.vx < 0: b.vx = 0
                b.hitwall = True
            else:
                if r.centery < tr.centery:
                    b.y = tr.top - b.h
                    if b.vy >= 0: b.on_ground = True; b.ground_ch = ch
                    if b.vy > 0: b.vy = 0
                else:
                    b.y = tr.bottom
                    if b.vy < 0: b.vy = 0
            r = b.rect()

    def solid_at(s, r):
        return any(s.get(tx, ty) in SOLID for tx, ty in s.cells(r))

    def safe_spot(s, r):
        """Footprint r standing on fully solid, non-spike ground and not inside walls."""
        if r.left < 0 or r.right > s.w * T or s.solid_at(r): return False
        ty = r.bottom // T
        if r.bottom % T: return False
        return all(s.get(tx, ty) in '#=V' for tx in range(r.left // T, (r.right - 1) // T + 1))

    def physics(s, b, grav=GRAV, maxfall=12.0):
        if b.plat: b.x += b.plat.dx
        b.plat = None; b.hitwall = False
        b.vy = min(b.vy + grav, maxfall)
        b.x += b.vx
        if b.x < 0: b.x = 0.0; b.vx = max(0.0, b.vx)
        if b.x > s.w * T - b.w: b.x = float(s.w * T - b.w); b.vx = min(0.0, b.vx)
        s.collide(b, 0)
        prev = b.y + b.h
        b.on_ground = False
        b.y += b.vy; s.collide(b, 1)
        if b.vy >= 0:
            for p in s.plats:
                if b.x + b.w > p.x and b.x < p.x + p.w and prev <= p.y + 2 and b.y + b.h >= p.y:
                    b.y = p.y - b.h; b.vy = 0; b.on_ground = True; b.plat = p; b.ground_ch = 'p'

    def hazard(s, b, immune=False):
        r = b.rect()
        if r.top > s.h * T: return True
        if b.on_ground and b.ground_ch == '^' and not immune: return True
        return any(s.get(tx, ty) == '~' for tx, ty in s.cells(r.inflate(-8, -8)))

    def in_wind(s, b):
        return any(c in s.wind for c in s.cells(b.rect()))


# ---------------------------------------------------------------- drawing helpers
def gradient(c1, c2):
    surf = pygame.Surface((W, H))
    for y in range(H):
        a = y / H
        surf.fill(tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3)), (0, y, W, 1))
    return surf


def draw_brim(sc, cx, cy, f, k=1.0, spin=None):
    cx, cy = int(cx), int(cy)
    sw = 1.0 if spin is None else max(0.25, abs(math.cos(spin)))
    dw, dh = max(4, int(20 * k * sw)), int(14 * k)
    pygame.draw.ellipse(sc, (205, 40, 55), (cx - dw // 2, cy - dh, dw, dh + 4))
    bw = max(6, int(28 * k * sw))
    pygame.draw.rect(sc, (150, 20, 35), (cx - bw // 2 + int(f * 3 * k * sw), cy, bw, max(2, int(4 * k))))
    pygame.draw.rect(sc, (245, 235, 220), (cx - dw // 2 + 1, cy - 2, dw - 2, 2))
    if sw > 0.5:
        for ex in (-4, 4):
            ep = (cx + int((ex + f * 2) * k * sw), cy - int(8 * k))
            pygame.draw.circle(sc, (255, 255, 255), ep, max(2, int(3 * k)))
            pygame.draw.circle(sc, (0, 0, 0), (ep[0] + f, ep[1]), max(1, int(1.6 * k)))


def draw_ship(sc, cx, by, t, k=1.0):
    def P(x, y): return (int(cx + x * k), int(by + y * k))
    br = (*P(-90, -195), int(180 * k), int(95 * k))
    pygame.draw.ellipse(sc, (200, 70, 60), br)
    pygame.draw.ellipse(sc, (240, 190, 80), (*P(-35, -195), int(70 * k), int(95 * k)))
    pygame.draw.ellipse(sc, (110, 35, 35), br, 2)
    for x in (-70, -25, 25, 70):
        pygame.draw.line(sc, (80, 60, 40), P(x * 0.8, -108), P(x, -40), 2)
    pygame.draw.polygon(sc, (130, 80, 45), [P(-100, -40), P(100, -40), P(75, 0), P(-75, 0)])
    pygame.draw.rect(sc, (90, 55, 30), (*P(-104, -46), int(208 * k), int(7 * k)))
    for x in (-50, 0, 50):
        pygame.draw.circle(sc, (60, 40, 25), P(x, -22), int(8 * k))
        pygame.draw.circle(sc, (255, 210, 110), P(x, -22), int(5 * k))
    glow = 6 + int(2 * math.sin(t * 0.15))
    pygame.draw.circle(sc, (255, 230, 140), P(0, -62), int(glow * k))
    pr = abs(math.sin(t * 0.5)) * 26
    pygame.draw.ellipse(sc, (90, 90, 100), (*P(-112, -25 - pr / 2), int(8 * k), max(2, int(pr * k))))


def heart(sc, x, y, col):
    pygame.draw.circle(sc, col, (x - 5, y), 6); pygame.draw.circle(sc, col, (x + 5, y), 6)
    pygame.draw.polygon(sc, col, [(x - 11, y + 2), (x + 11, y + 2), (x, y + 14)])


class Inp:
    def __init__(s): s.h = set(); s.p = set()

    def held(s, a): return a in s.h

    def pressed(s, a): return a in s.p


# ---------------------------------------------------------------- game
class Game:
    def __init__(s, screen):
        s.scr = screen
        s.f = pygame.font.Font(None, 28); s.fb = pygame.font.Font(None, 52); s.fh = pygame.font.Font(None, 110)
        s.grads = [gradient(t['sky1'], t['sky2']) for t in THEMES]
        s.sunset = gradient((90, 40, 120), (255, 140, 70))
        s.moonimg = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(s.moonimg, (255, 215, 60), (16, 16), 14)
        pygame.draw.circle(s.moonimg, (0, 0, 0, 0), (23, 11), 11)
        s.glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        for r in range(30, 0, -3): pygame.draw.circle(s.glow, (255, 240, 150, int(60 * (1 - r / 30))), (30, 30), r)
        s.bar = pygame.Surface((W, 44), pygame.SRCALPHA); s.bar.fill((0, 0, 0, 130))
        s.t = 0; s.msg = ''; s.msgt = 0; s.shake = 0; s.ft = 0
        s.new_game(); s.state = 'title'

    def new_game(s):
        s.got = set(); s.coins = 0; s.bank = 0; s.frames = 0; s.captures = 0
        s.p = Player(); s.k = 0; s.L = None; s.parts = []; s.on_ship = False

    def load(s, k):
        s.k = k; s.L = Level(k, s.got); p = s.p
        sx, sy = s.L.start
        p.x, p.y = sx * T + 8.0, (sy + 1) * T - p.h * 1.0
        p.vx = p.vy = 0.0; p.capture = None; p.cap = None; p.safe = (p.x, p.y); p.inv = 0; p.plat = None
        s.cam = [0.0, 0.0]; s.update_cam(snap=True)
        s.parts = []; s.state = 'play'; s.on_ship = False

    def kmoons(s): return sum(1 for kk, _ in s.got if kk == s.k)

    def say(s, m, t=150): s.msg, s.msgt = m, t

    def burst(s, x, y, col, n=12, sp=3.0):
        for _ in range(n):
            a = random.random() * 6.283; v = random.random() * sp
            s.parts.append([x, y, math.cos(a) * v, math.sin(a) * v - 1, random.randint(20, 40), col])

    # ---------------- update
    def update(s, inp):
        s.t += 1
        if s.msgt > 0: s.msgt -= 1
        if s.state == 'title':
            if inp.pressed('enter'): s.new_game(); s.load(0); s.say('Find Power Moons! 3 fuel the Lanternwing.')
        elif s.state == 'play':
            s.update_play(inp)
        elif s.state == 'flight':
            s.ft += 1
            if s.ft >= 180:
                if s.k < 2: s.load(s.k + 1); s.say('Welcome to ' + KNAMES[s.k] + '!')
                else: s.state = 'win'
        elif s.state == 'gameover':
            if inp.pressed('enter'): s.p.hearts = 3; s.load(s.k)
        elif s.state == 'win':
            if inp.pressed('enter'): s.new_game(); s.state = 'title'

    def update_play(s, inp):
        L, p = s.L, s.p
        s.frames += 1
        for pl in L.plats: pl.update()
        if p.capture: s.control_enemy(p.capture, inp)
        else: s.control_pip(inp)
        for e in L.enemies:
            if not e.captured: s.enemy_ai(e)
        s.update_cap()
        for x, y in L.smashed:
            s.burst(x, y, (190, 150, 100), 18, 5); s.shake = 8
        L.smashed.clear()
        body = p.capture or p
        br = body.rect()
        for c in L.coins[:]:
            if br.colliderect(c): L.coins.remove(c); s.get_coin(c)
        for m in L.moons[:]:
            if br.colliderect(m.rect()): s.get_moon(m)
        if not p.capture and p.inv == 0:
            for e in L.enemies:
                if e.stun == 0 and br.colliderect(e.rect().inflate(-6, -6)):
                    s.hurt(False); break
        immune = p.capture is not None and p.capture.kind == 'beetle'
        if s.state == 'play' and L.hazard(body, immune):
            s.hurt(True)
        elif not p.capture and p.on_ground and p.plat is None and L.safe_spot(p.rect()):
            p.safe = (p.x, p.y)
        if p.inv > 0: p.inv -= 1
        s.on_ship = p.capture is None and br.colliderect(L.ship)
        if s.on_ship and inp.pressed('enter') and s.state == 'play':
            if s.kmoons() >= 3: s.state = 'flight'; s.ft = 0
            else: s.say('The Lanternwing needs 3 Power Moons from this kingdom!')
        s.update_cam()
        for pt in s.parts:
            pt[0] += pt[2]; pt[1] += pt[3]; pt[3] += 0.12; pt[4] -= 1
        s.parts = [pt for pt in s.parts if pt[4] > 0]
        if s.shake: s.shake -= 1

    def update_cam(s, snap=False):
        b = s.p.capture or s.p
        tx = b.x + b.w / 2 - W / 2; ty = b.y + b.h / 2 - H / 2 - 30
        if snap: s.cam = [tx, ty]
        else:
            s.cam[0] += (tx - s.cam[0]) * 0.12; s.cam[1] += (ty - s.cam[1]) * 0.12
        s.cam[0] = max(0, min(s.cam[0], s.L.w * T - W))
        s.cam[1] = max(0, min(s.cam[1], s.L.h * T - H))

    def control_pip(s, inp):
        p, L = s.p, s.L
        d = inp.held('right') - inp.held('left')
        ice = p.on_ground and p.ground_ch == '='
        if d:
            p.face = d
            acc = 0.18 if ice else (0.8 if p.on_ground else 0.5)
            p.vx = max(-5, min(5, p.vx + d * acc))
        else:
            p.vx *= 0.97 if ice else (0.7 if p.on_ground else 0.93)
            if abs(p.vx) < 0.1: p.vx = 0
        if p.on_ground: p.coy = 6; p.bounced = False
        elif p.coy > 0: p.coy -= 1
        p.jbuf = 7 if inp.pressed('jump') else max(0, p.jbuf - 1)
        if p.jbuf and p.coy:
            p.vy = -JUMP; p.jbuf = 0; p.coy = 0; p.full = False
            s.burst(p.x + 12, p.y + 34, (230, 230, 230), 5, 1.5)
        if p.vy >= 0: p.full = False
        if not inp.held('jump') and p.vy < -4 and not p.full: p.vy = -4
        if inp.pressed('cap') and p.cap is None:
            p.cap = Cap(p.x + p.w / 2 + p.face * 10, p.y + 12, p.face)
        L.physics(p)
        p.anim += abs(p.vx) * 0.12

    def update_cap(s):
        p, L = s.p, s.L
        c = p.cap
        if c is None: return
        c.spin += 0.45
        if c.state == 'out':
            c.x += c.vx; c.t -= 1
            if L.get(int(c.x // T), int(c.y // T)) in SOLID or c.t <= 0: c.state, c.t = 'hover', 25
        elif c.state == 'hover':
            c.t -= 1
            if c.t <= 0: c.state = 'back'
        else:
            dx, dy = p.x + p.w / 2 - c.x, p.y + 14 - c.y
            dist = math.hypot(dx, dy)
            if dist < 16: p.cap = None; return
            c.x += dx / dist * 13; c.y += dy / dist * 13
        cr = c.rect()
        for co in L.coins[:]:
            if cr.colliderect(co): L.coins.remove(co); s.get_coin(co)
        if c.state == 'back': return
        for e in L.enemies:
            if e.stun == 0 and cr.colliderect(e.rect()):
                s.do_capture(e); return
        if p.vy > 0 and not p.bounced and p.rect().colliderect(cr) and p.y + p.h < c.y + 12:
            p.vy = -JUMP; p.bounced = True; p.full = True; c.state = 'back'
            s.burst(c.x, c.y, (255, 120, 130), 10)

    def do_capture(s, e):
        p = s.p
        p.capture = e; e.captured = True; e.stun = 0; e.vx = 0; p.cap = None; s.captures += 1
        names = {'toad': 'Springtoad', 'beetle': 'Rockbeetle', 'kite': 'Puffkite'}
        s.say('Captured a ' + names[e.kind] + '!', 90)
        s.burst(e.x + e.w / 2, e.y, (255, 90, 110), 16, 4)

    def release(s, hop=True):
        p = s.p; e = p.capture
        p.capture = None; e.captured = False; e.stun = 120; e.charge = 0; e.dash = 0; e.smash = False
        e.hx, e.hy, e.t = e.x, e.y, 0
        p.x = e.x + e.w / 2 - p.w / 2; p.y = e.y + e.h - p.h
        p.vx = 0; p.vy = -8 if hop else 0; p.face = e.face; p.bounced = False; p.full = True; p.plat = None
        s.burst(p.x + 12, p.y, (255, 255, 255), 10)

    def control_enemy(s, e, inp):
        L = s.L
        if inp.pressed('cap'): s.release(True); return
        d = inp.held('right') - inp.held('left')
        if d: e.face = d
        k = 0.05 if (e.on_ground and e.ground_ch == '=') else 0.3
        if e.kind == 'toad':
            e.vx += (d * (1.5 if e.charge else 3.5) - e.vx) * k
            if e.on_ground and inp.held('jump'):
                e.charge = min(60, e.charge + 1)
            elif e.charge > 0:
                if e.on_ground:
                    e.vy = -JUMP * math.sqrt(1 + 2 * e.charge / 60)
                    s.burst(e.x + e.w / 2, e.y + e.h, (150, 230, 150), 8 + e.charge // 6, 2.5)
                e.charge = 0
            L.physics(e)
        elif e.kind == 'beetle':
            if e.dash > 0:
                e.dash -= 1; e.vx = e.face * 7.5; e.smash = True
                if s.t % 3 == 0: s.burst(e.x + e.w / 2 - e.face * 18, e.y + e.h - 4, (200, 200, 200), 2, 1)
            else:
                e.smash = False; e.vx += (d * 2.2 - e.vx) * k
                if inp.pressed('jump') and e.on_ground: e.dash = 40
            L.physics(e)
            if e.hitwall: e.dash = 0
        else:
            e.vx += (d * 3 - e.vx) * 0.15
            if e.on_ground and inp.pressed('jump'): e.vy = -5
            if L.in_wind(e): e.vy = max(-6, e.vy - 0.9)
            L.physics(e, 0.15, 1.6)

    def enemy_ai(s, e):
        L = s.L
        e.t += 1
        if e.kind == 'kite':
            if e.stun: e.stun -= 1
            nx = e.hx + math.sin(e.t * 0.02) * 50; ny = e.hy + math.sin(e.t * 0.06) * 8
            nx = max(0.0, min(nx, L.w * T - e.w))
            if not L.solid_at(pygame.Rect(int(nx), int(e.y), e.w, e.h)): e.x = nx
            if not L.solid_at(pygame.Rect(int(e.x), int(ny), e.w, e.h)): e.y = ny
            return
        if e.stun > 0:
            e.stun -= 1; e.vx *= 0.85
        elif e.kind == 'toad':
            if e.on_ground:
                e.vx = 0; e.timer -= 1
                if e.timer <= 0: e.vy = -8; e.vx = e.face * 2; e.timer = random.randint(60, 120)
        else:
            e.vx = e.face * 1.0
            ax = e.x + e.w + 2 if e.face > 0 else e.x - 2
            if e.on_ground and L.get(int(ax // T), int((e.y + e.h + 4) // T)) not in SOLID: e.face = -e.face
        L.physics(e)
        if e.hitwall: e.face = -e.face
        if L.hazard(e, e.kind == 'beetle'): e.reset()

    def hurt(s, hazard):
        p = s.p
        dmg = p.inv == 0
        if not dmg and not hazard: return
        if dmg: p.hearts -= 1; p.inv = 100
        if p.capture:
            e = p.capture; s.release(False)
            if hazard: e.reset()
        if hazard: p.x, p.y = p.safe; p.vx = p.vy = 0; p.plat = None
        else: p.vy = -7; p.vx = -p.face * 4
        s.burst(p.x + 12, p.y + 17, (255, 60, 60), 14, 3)
        if p.hearts <= 0: s.state = 'gameover'

    def get_coin(s, c):
        s.coins += 1; s.bank += 1
        s.burst(c.centerx, c.centery, (255, 220, 60), 4, 1.5)
        if s.bank >= 50:
            s.bank -= 50
            if s.p.hearts < 3: s.p.hearts += 1; s.say('50 coins: heart restored!', 90)

    def get_moon(s, m):
        s.L.moons.remove(m); s.got.add((s.k, m.i))
        n = s.kmoons()
        s.say('POWER MOON!  %d/5' % n + ('   - The Lanternwing can fly! Return to it.' if n == 3 else ''), 180)
        s.burst(m.x, m.y, (255, 230, 80), 30, 5)

    # ---------------- drawing
    def txt(s, text, pos, font=None, col=(255, 255, 255), right=False, center=False):
        font = font or s.f
        img = font.render(text, True, col); sh = font.render(text, True, (0, 0, 0))
        r = img.get_rect()
        if center: r.center = pos
        elif right: r.topright = pos
        else: r.topleft = pos
        s.scr.blit(sh, r.move(2, 2)); s.scr.blit(img, r)

    def draw_bg(s, k, cx):
        sc = s.scr; sc.blit(s.grads[k], (0, 0))
        if k == 0:
            pygame.draw.circle(sc, (255, 240, 190), (760, 110), 50)
            for f, col, hh in ((0.15, (225, 165, 105), 170), (0.35, (210, 145, 90), 110)):
                for i in range(-1, 6):
                    x = i * 320 - (cx * f) % 320
                    pygame.draw.ellipse(sc, col, (x - 60, H - hh, 440, 300))
        elif k == 1:
            for f, col, hh in ((0.15, (190, 215, 235), 200), (0.35, (120, 165, 190), 130)):
                for i in range(-1, 14):
                    x = i * 90 - (cx * f) % 90
                    pygame.draw.polygon(sc, col, [(x, H - hh), (x - 40, H), (x + 40, H)])
            for i in range(30):
                sx = (i * 137 + s.t * (1 + i % 3)) % W; sy = (i * 71 + s.t * 2) % H
                pygame.draw.circle(sc, (255, 255, 255), (sx, sy), 2)
        else:
            for f, col, hh in ((0.15, (80, 25, 25), 260), (0.35, (55, 15, 18), 170)):
                for i in range(-1, 8):
                    x = i * 200 - (cx * f) % 200
                    pygame.draw.polygon(sc, col, [(x - 110, H), (x - 30, H - hh), (x + 20, H - hh + 50), (x + 110, H)])
            for i in range(25):
                sx = (i * 151) % W; sy = H - (i * 53 + s.t * (1 + i % 3)) % H
                pygame.draw.circle(sc, (255, 150, 60), (sx, sy), 2)

    def draw_tiles(s, ox, oy):
        sc, L, th = s.scr, s.L, THEMES[s.k]
        for ty in range(max(0, oy // T), min(L.h, (oy + H) // T + 1)):
            for tx in range(max(0, ox // T), min(L.w, (ox + W) // T + 1)):
                ch = L.g[ty][tx]
                if ch == '.': continue
                r = pygame.Rect(tx * T - ox, ty * T - oy, T, T)
                above = L.get(tx, ty - 1)
                if ch == '#':
                    pygame.draw.rect(sc, th['ground'], r)
                    pygame.draw.rect(sc, th['dark'], (r.x + 6, r.y + 18, 6, 4))
                    if above not in SOLID: pygame.draw.rect(sc, th['top'], (r.x, r.y, T, 8))
                elif ch == '=':
                    pygame.draw.rect(sc, (190, 230, 250), r)
                    pygame.draw.line(sc, (255, 255, 255), (r.x + 4, r.y + 4), (r.x + 20, r.y + 4), 2)
                    pygame.draw.rect(sc, (140, 195, 225), r, 1)
                elif ch == 'C':
                    pygame.draw.rect(sc, (175, 135, 95), r); pygame.draw.rect(sc, (110, 80, 50), r, 2)
                    pygame.draw.lines(sc, (90, 60, 40), False, [(r.x + 8, r.y + 4), (r.x + 18, r.y + 16), (r.x + 12, r.y + 26), (r.x + 26, r.y + 36)], 2)
                elif ch == '^':
                    pygame.draw.rect(sc, (90, 90, 100), (r.x, r.y + 24, T, 16))
                    for i in range(3):
                        pygame.draw.polygon(sc, (215, 215, 225), [(r.x + i * 13, r.y + 26), (r.x + i * 13 + 13, r.y + 26), (r.x + i * 13 + 6, r.y + 4)])
                elif ch == '~':
                    if above == '~': pygame.draw.rect(sc, th['liquid'], r)
                    else:
                        wv = int(math.sin(s.t * 0.08 + tx) * 3)
                        pygame.draw.rect(sc, th['liquid'], (r.x, r.y + 8 + wv, T, T - 8 - wv))
                        pygame.draw.line(sc, (255, 230, 160) if s.k == 2 else (200, 230, 255), (r.x, r.y + 8 + wv), (r.right, r.y + 8 + wv), 3)
                elif ch == 'V':
                    pygame.draw.rect(sc, (70, 80, 100), r)
                    for i in range(4): pygame.draw.rect(sc, (30, 35, 45), (r.x + 4 + i * 9, r.y + 4, 5, 14))
        for tx, ty in L.wind:
            if ox - T < tx * T < ox + W and oy - T < ty * T < oy + H:
                yy = ty * T - oy + T - (s.t * 5 + tx * 17 + ty * 29) % T
                for dx in (8, 22, 32):
                    pygame.draw.line(sc, (235, 250, 255), (tx * T - ox + dx, yy), (tx * T - ox + dx, yy + 10), 2)

    def draw_enemy(s, e, ox, oy):
        sc = s.scr; x, y, w, h, f = e.x - ox, e.y - oy, e.w, e.h, e.face
        if e.kind == 'toad':
            sq = e.charge * 0.15 if e.captured else (0 if e.on_ground else -3)
            b = pygame.Rect(int(x - sq / 2), int(y + sq), int(w + sq), int(h - sq))
            pygame.draw.ellipse(sc, (70, 170, 70), b); pygame.draw.ellipse(sc, (35, 105, 40), b, 2)
            pygame.draw.ellipse(sc, (170, 225, 140), (b.x + 6, b.centery, b.w - 12, b.h // 2 - 1))
            for ex in (b.x + 8, b.right - 8):
                pygame.draw.circle(sc, (255, 255, 255), (ex, b.y + 3), 5)
                pygame.draw.circle(sc, (0, 0, 0), (ex + f * 2, b.y + 3), 2)
        elif e.kind == 'beetle':
            pts = [(x + w / 2 + w / 2 * math.cos(a / 10 * math.pi), y + h - 4 - (h - 4) * math.sin(a / 10 * math.pi)) for a in range(11)]
            for i in range(3):
                lx = x + 7 + i * 11
                pygame.draw.line(sc, (50, 50, 60), (lx, y + h - 4), (lx + (3 if (s.t // 6 + i) % 2 else -3), y + h), 3)
            pygame.draw.polygon(sc, (130, 130, 145), pts); pygame.draw.polygon(sc, (70, 70, 80), pts, 2)
            pygame.draw.circle(sc, (100, 100, 115), (int(x + w / 2 - 5), int(y + 10)), 4)
            pygame.draw.circle(sc, (255, 220, 60), (int(x + w / 2 + f * 11), int(y + h - 12)), 3)
            if e.dash:
                for i in range(3): pygame.draw.line(sc, (255, 255, 255), (x + w / 2 - f * (24 + i * 6), y + 6 + i * 6), (x + w / 2 - f * (40 + i * 6), y + 6 + i * 6), 2)
        else:
            pygame.draw.line(sc, (120, 60, 90), (x + w / 2, y + h), (x + w / 2 - f * 8, y + h + 10 + 3 * math.sin(s.t * 0.2)), 2)
            pygame.draw.polygon(sc, (240, 125, 175), [(x + w / 2, y), (x + w, y + h), (x, y + h)])
            pygame.draw.polygon(sc, (170, 60, 110), [(x + w / 2, y), (x + w, y + h), (x, y + h)], 2)
            for ex in (-5, 5):
                pygame.draw.circle(sc, (255, 255, 255), (int(x + w / 2 + ex + f * 2), int(y + h - 10)), 4)
                pygame.draw.circle(sc, (0, 0, 0), (int(x + w / 2 + ex + f * 3), int(y + h - 10)), 2)
        if e.captured: draw_brim(sc, x + w / 2, y - 2, f, 0.8)
        elif e.stun:
            for i in range(3):
                a = s.t * 0.1 + i * 2.1
                pygame.draw.circle(sc, (255, 240, 90), (int(x + w / 2 + math.cos(a) * 13), int(y - 6 + math.sin(a) * 4)), 3)

    def draw_pip(s, ox, oy):
        p, sc = s.p, s.scr
        if p.inv and (s.t // 4) % 2: return
        x, y, f = int(p.x - ox), int(p.y - oy), p.face
        leg = int(math.sin(p.anim) * 4) if p.on_ground and abs(p.vx) > 0.5 else 0
        pygame.draw.rect(sc, (40, 40, 70), (x + 5 + leg, y + 28, 6, 6))
        pygame.draw.rect(sc, (40, 40, 70), (x + 13 - leg, y + 28, 6, 6))
        pygame.draw.rect(sc, (60, 100, 210), (x + 3, y + 15, 18, 15), border_radius=4)
        pygame.draw.rect(sc, (150, 100, 50), (x + 12 - f * 10, y + 18, 6, 8))
        pygame.draw.circle(sc, (250, 215, 180), (x + 12, y + 10), 8)
        pygame.draw.circle(sc, (0, 0, 0), (x + 12 + f * 4, y + 9), 2)
        if p.cap is None: draw_brim(sc, x + 12, y + 4, f)
        else: pygame.draw.ellipse(sc, (90, 60, 40), (x + 5, y + 1, 14, 7))

    def draw_play(s):
        sc, L, p = s.scr, s.L, s.p
        ox, oy = int(s.cam[0]), int(s.cam[1])
        if s.shake: ox += random.randint(-s.shake, s.shake); oy += random.randint(-s.shake, s.shake)
        s.draw_bg(s.k, ox)
        s.draw_tiles(ox, oy)
        th = THEMES[s.k]
        for pl in L.plats:
            pygame.draw.rect(sc, th['top'], (int(pl.x) - ox, pl.y - oy, pl.w, pl.h), border_radius=4)
            pygame.draw.rect(sc, th['dark'], (int(pl.x) - ox, pl.y - oy, pl.w, pl.h), 2, border_radius=4)
        draw_ship(sc, L.ship.centerx - ox, L.ship.bottom - oy + math.sin(s.t * 0.04) * 2, s.t)
        for c in L.coins:
            cw = max(2, int(abs(math.sin(s.t * 0.07 + c.x * 0.01)) * 16))
            pygame.draw.ellipse(sc, (255, 200, 40), (c.centerx - cw // 2 - ox, c.y - oy, cw, 16))
            pygame.draw.ellipse(sc, (255, 240, 150), (c.centerx - cw // 4 - ox, c.y + 4 - oy, max(1, cw // 2), 8))
        for m in L.moons:
            by = int(math.sin(s.t * 0.06 + m.i) * 4)
            sc.blit(s.glow, (m.x - 30 - ox, m.y - 30 - oy + by))
            sc.blit(s.moonimg, (m.x - 16 - ox, m.y - 16 - oy + by))
        for e in L.enemies: s.draw_enemy(e, ox, oy)
        if not p.capture: s.draw_pip(ox, oy)
        if p.cap: draw_brim(sc, p.cap.x - ox, p.cap.y + 4 - oy, 0, 1.0, p.cap.spin)
        for pt in s.parts:
            pygame.draw.circle(sc, pt[5], (int(pt[0] - ox), int(pt[1] - oy)), max(1, pt[4] // 10 + 1))
        s.draw_hud()

    def draw_hud(s):
        sc, p = s.scr, s.p
        for i in range(3): heart(sc, 26 + i * 32, 20, (230, 40, 60) if i < p.hearts else (70, 60, 60))
        pygame.draw.circle(sc, (255, 200, 40), (24, 56), 9)
        s.txt('x %d' % s.coins, (40, 47))
        s.txt(KNAMES[s.k], (W - 14, 12), right=True)
        s.txt('Moons %d/5   total %d/15' % (s.kmoons(), len(s.got)), (W - 14, 44), right=True)
        sc.blit(s.moonimg, (W - 290, 38))
        sc.blit(s.bar, (0, H - 44))
        e = p.capture
        if e:
            s.draw_enemy(e, e.x - 18, e.y - (H - 34))
            if e.kind == 'toad' and e.charge:
                pygame.draw.rect(sc, (255, 230, 80), (70, H - 12, e.charge * 2, 6))
        else:
            draw_brim(sc, 30, H - 16, 1)
        s.txt(HINTS[e.kind if e else None], (70, H - 34))
        if s.on_ship:
            ok = s.kmoons() >= 3
            s.txt('ENTER: board the Lanternwing!' if ok else 'Lanternwing needs 3 moons (%d/3)' % s.kmoons(),
                  (W // 2, 110), s.f, (255, 240, 150) if ok else (255, 200, 200), center=True)
        if s.msgt:
            s.txt(s.msg, (W // 2, 150), s.f, (255, 250, 210), center=True)

    def draw_clouds(s, speed):
        for i in range(3):
            for j in range(7):
                x = (j * 190 - s.t * speed * (i + 1)) % (W + 240) - 120
                y = 60 + i * 140 + (j * 37) % 60
                pygame.draw.ellipse(s.scr, (255, 255, 255), (x, y, 110 + i * 20, 34 + i * 6))

    def draw(s):
        sc = s.scr
        if s.state == 'title':
            sc.blit(s.grads[0], (0, 0)); s.draw_clouds(0.4)
            s.txt('ODYSSEY', (W // 2, 90), s.fh, (255, 240, 200), center=True)
            s.txt('of the Living Cap', (W // 2, 155), s.fb, (255, 220, 160), center=True)
            draw_ship(sc, W // 2, 400 + math.sin(s.t * 0.05) * 10, s.t, 1.1)
            draw_brim(sc, W // 2 + 60, 340 + math.sin(s.t * 0.05) * 10, -1, 1.6)
            if (s.t // 30) % 2: s.txt('Press Enter', (W // 2, 460), s.fb, center=True)
            s.txt('Arrows: run   Space: jump   X: throw Brim / release   Enter: board airship   Esc: quit', (W // 2, 515), center=True)
        elif s.state == 'play':
            s.draw_play()
        elif s.state == 'flight':
            sc.blit(s.grads[min(2, s.k + 1)] if s.k < 2 else s.sunset, (0, 0))
            s.draw_clouds(2.5)
            draw_ship(sc, 150 + s.ft * 3.8, 330 + math.sin(s.t * 0.08) * 12, s.t, 1.0)
            dest = KNAMES[s.k + 1] if s.k < 2 else 'the sunset'
            s.txt('The Lanternwing sets sail for ' + dest + '!', (W // 2, 470), s.fb, center=True)
        elif s.state == 'gameover':
            sc.fill((25, 10, 20))
            s.txt('GAME OVER', (W // 2, 180), s.fh, (240, 80, 80), center=True)
            s.txt('Power Moons collected: %d' % len(s.got), (W // 2, 290), s.fb, center=True)
            s.txt('Press Enter to retry ' + KNAMES[s.k], (W // 2, 380), center=True)
        elif s.state == 'win':
            sc.blit(s.sunset, (0, 0))
            pygame.draw.circle(sc, (255, 210, 120), (W // 2, 330), 90)
            pygame.draw.rect(sc, (60, 50, 110), (0, 340, W, H - 340))
            for i in range(10): pygame.draw.line(sc, (255, 180, 120), (W // 2 - 80 + i * 7, 350 + i * 12), (W // 2 + 80 - i * 7, 350 + i * 12), 2)
            draw_ship(sc, (s.t * 1.2) % (W + 300) - 150, 300 + math.sin(s.t * 0.05) * 6, s.t, 0.7)
            s.txt('THE END', (W // 2, 70), s.fh, (255, 245, 220), center=True)
            sec = s.frames // 60
            s.txt('Moons %d/15    Coins %d    Time %d:%02d' % (len(s.got), s.coins, sec // 60, sec % 60), (W // 2, 150), s.fb, center=True)
            if len(s.got) >= 15: s.txt('Brim tips his hat to you!', (W // 2, 200), s.fb, (255, 230, 120), center=True)
            s.txt('Press Enter', (W // 2, 510), center=True)


# ---------------------------------------------------------------- main / smoke
def smoke():
    screen = pygame.display.set_mode((W, H))
    g = Game(screen); g.load(0)
    phase, t, target, placed, tries = 'run', 0, None, 0, 0
    startx = g.p.x; ran = 0.0; jumped = False; thrown = 0
    for frame in range(1800):
        inp = Inp(); p, L = g.p, g.L
        if phase == 'run':
            inp.h.add('right')
            if t == 25: inp.p.add('jump')
            if 25 <= t < 40: inp.h.add('jump')
            if t > 25 and not p.on_ground: jumped = True
            if t >= 70: ran = p.x - startx; phase, t = 'capture', 0
        elif phase == 'capture':
            if p.capture: phase, t = 'moons', 0
            elif p.cap is None:
                toad = next(e for e in L.enemies if e.kind == 'toad')
                p.x, p.y = toad.x - 70, toad.y + toad.h - p.h; p.vx = p.vy = 0; p.face = 1; p.plat = None
                inp.p.add('cap'); thrown += 1
            if t > 400: raise RuntimeError('capture failed')
        elif phase == 'moons':
            body = p.capture
            if body is None: raise RuntimeError('lost capture')
            if t < 45:
                if t < 35: inp.h.add('jump')
            elif g.kmoons() >= 3:
                phase, t = 'release', 0
            else:
                if target is None or target not in L.moons or t - placed > 60:
                    safe = [m for m in L.moons if L.get(int(m.x // T), int(m.y // T) + 1) != '^']
                    target = min(safe, key=lambda m: m.x)
                    body.x, body.y = target.x - 40 - body.w / 2, target.y - body.h / 2
                    body.vx = body.vy = 0; body.plat = None; placed = t; tries += 1
                    if tries > 15: raise RuntimeError('moon pickup failed')
                inp.h.add('right')
        elif phase == 'release':
            inp.p.add('cap'); phase, t = 'board', 0
        elif phase == 'board':
            if p.capture: raise RuntimeError('release failed')
            p.x, p.y = L.ship.centerx - p.w / 2, L.ship.bottom - p.h; p.vx = p.vy = 0; p.plat = None
            if t >= 2: inp.p.add('enter'); phase, t = 'fly', 0
        elif phase == 'fly':
            if g.state == 'play' and g.k == 1: phase, t = 'k2', 0
            if t > 400: raise RuntimeError('travel failed')
        elif phase == 'k2':
            if t < 40: inp.h.add('right')
            if t == 10: inp.p.add('jump'); inp.h.add('jump')
        g.update(inp); g.draw(); pygame.display.flip()
        t += 1
    if g.k != 1 or len(g.got) < 3 or g.captures < 1 or not jumped or ran <= 100:
        raise RuntimeError('smoke test goals not met: k=%d moons=%d caps=%d' % (g.k, len(g.got), g.captures))
    print('SMOKE TEST OK frames=1800 ran=%dpx jumped=%s cap_throws=%d captures=%d moons=%d coins=%d kingdom=%s hearts=%d'
          % (ran, jumped, thrown, g.captures, len(g.got), g.coins, KNAMES[g.k], g.p.hearts))


def main():
    pygame.init()
    if SMOKE:
        smoke(); pygame.quit(); sys.exit(0)
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption('Odyssey of the Living Cap')
    g = Game(screen); clock = pygame.time.Clock()
    while True:
        inp = Inp()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: pygame.quit(); return
                for a, ks in KEYS.items():
                    if ev.key in ks: inp.p.add(a)
        keys = pygame.key.get_pressed()
        for a, ks in KEYS.items():
            if any(keys[k] for k in ks): inp.h.add(a)
        g.update(inp); g.draw(); pygame.display.flip(); clock.tick(FPS)


if __name__ == '__main__':
    main()
