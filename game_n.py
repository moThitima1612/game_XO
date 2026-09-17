import pygame, sys, math, random

pygame.init()
pygame.display.set_caption("OX — Tic Tac Toe")

W, H = 560, 770
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

# ---------------- ธีมสี ----------------
BG      = (20, 24, 34)
BG2     = (28, 33, 48)
CARD    = (34, 40, 57)
CARD_HL = (48, 56, 79)
LINE    = (58, 68, 92)
X_COL   = (78, 205, 196)
O_COL   = (255, 107, 107)
GOLD    = (255, 202, 87)
TEXT    = (233, 237, 245)
MUTED   = (135, 146, 168)

BOARD_X, BOARD_Y, CELL = 52, 196, 152
BOARD_SIZE = CELL * 3
WIN_LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]


def load_font(size, bold=True):
    for n in ("Leelawadee UI", "Tahoma", "Noto Sans Thai", "Sarabun", "Arial"):
        p = pygame.font.match_font(n, bold)
        if p:
            return pygame.font.Font(p, size)
    return pygame.font.SysFont(None, size, bold)

F_TITLE, F_BIG, F_MID, F_SM = load_font(42), load_font(26), load_font(20), load_font(15)

# ---------------- คีย์ลัดเลือกช่อง 1-9 ----------------
KEY_CELL = {}
for n in range(9):
    KEY_CELL[getattr(pygame, f"K_{n+1}")] = n
for name, idx in zip(("KP7","KP8","KP9","KP4","KP5","KP6","KP1","KP2","KP3"), range(9)):
    k = getattr(pygame, "K_" + name, None) or getattr(pygame, "K_KP_" + name[2:], None)
    if k:
        KEY_CELL[k] = idx


def text(surf, s, f, color, center):
    img = f.render(s, True, color)
    surf.blit(img, img.get_rect(center=center))

def text_left(surf, s, f, color, pos):
    surf.blit(f.render(s, True, color), pos)

def lerp(a, b, t): return a + (b - a) * t
def lerp_pt(a, b, t): return (lerp(a[0], b[0], t), lerp(a[1], b[1], t))
def ease(t): return 1 - (1 - t) ** 3


class Button:
    def __init__(self, rect, label, f=F_MID, accent=GOLD, radius=14):
        self.rect, self.label, self.f, self.accent, self.radius = pygame.Rect(rect), label, f, accent, radius
        self.selected = False

    def draw(self, surf, mouse):
        hover = self.rect.collidepoint(mouse)
        pygame.draw.rect(surf, CARD_HL if (hover or self.selected) else CARD, self.rect, border_radius=self.radius)
        if self.selected:
            pygame.draw.rect(surf, self.accent, self.rect, 3, border_radius=self.radius)
        text(surf, self.label, self.f, self.accent if self.selected else TEXT, self.rect.center)

    def hit(self, pos): return self.rect.collidepoint(pos)


# ---------------- ตรรกะเกม ----------------
def check(b):
    for a, c, d in WIN_LINES:
        if b[a] != " " and b[a] == b[c] == b[d]:
            return b[a], (a, c, d)
    return ("D", None) if " " not in b else (None, None)

def minimax(b, maxing, ai_m, hu_m, depth, alpha, beta):
    w, _ = check(b)
    if w == ai_m: return 10 - depth
    if w == hu_m: return depth - 10
    if w == "D": return 0

    if maxing:
        best = -99
        for i in range(9):
            if b[i] == " ":
                b[i] = ai_m
                best = max(best, minimax(b, False, ai_m, hu_m, depth+1, alpha, beta))
                b[i] = " "
                alpha = max(alpha, best)
                if beta <= alpha: break
        return best
    best = 99
    for i in range(9):
        if b[i] == " ":
            b[i] = hu_m
            best = min(best, minimax(b, True, ai_m, hu_m, depth+1, alpha, beta))
            b[i] = " "
            beta = min(beta, best)
            if beta <= alpha: break
    return best

def ai_pick(b, ai_m, hu_m, d):
    empty = [i for i in range(9) if b[i] == " "]
    noise = {0: 0.7, 1: 0.3, 2: 0.0}[d]
    if random.random() < noise:
        return random.choice(empty)
    best, move = -99, empty[0]
    for i in random.sample(empty, len(empty)):
        b[i] = ai_m
        s = minimax(b, False, ai_m, hu_m, 0, -99, 99)
        b[i] = " "
        if s > best:
            best, move = s, i
    return move


# ---------------- วาดสัญลักษณ์ ----------------
def cell_rect(i):
    return pygame.Rect(BOARD_X + (i % 3) * CELL, BOARD_Y + (i // 3) * CELL, CELL, CELL)

def draw_x(surf, r, p, color, thick=13):
    pad = r.width * 0.28
    strokes = [((r.left+pad, r.top+pad), (r.right-pad, r.bottom-pad)),
               ((r.right-pad, r.top+pad), (r.left+pad, r.bottom-pad))]
    for idx, (a, b) in enumerate(strokes):
        seg = min(1, p / 0.5) if idx == 0 else max(0, (p - 0.5) / 0.5)
        if seg <= 0: continue
        end = lerp_pt(a, b, ease(seg))
        pygame.draw.line(surf, color, a, end, thick)
        pygame.draw.circle(surf, color, (int(a[0]), int(a[1])), thick // 2)
        pygame.draw.circle(surf, color, (int(end[0]), int(end[1])), thick // 2)

def draw_o(surf, r, p, color, thick=13):
    cx, cy = r.center
    rad = r.width * 0.27
    steps = max(2, int(80 * p))
    for i in range(steps + 1):
        ang = -math.pi/2 + 2*math.pi * (p * i / steps)
        pygame.draw.circle(surf, color, (int(cx + rad*math.cos(ang)), int(cy + rad*math.sin(ang))), thick // 2)

def draw_mark(surf, i, mark, p, color):
    if p <= 0: return
    (draw_x if mark == "X" else draw_o)(surf, cell_rect(i), min(1.0, p), color)

def mark_color(m): return X_COL if m == "X" else O_COL


# ---------------- สถานะ ----------------
state, mode, human, ai, diff = "menu", "ai", "X", "O", 2
board, anim = [" "]*9, [0.0]*9
turn, winner, win_line, win_anim = "X", None, None, 0.0
ai_at, scores, particles = 0, [0, 0, 0], []

def is_my_turn():
    return mode == "pvp" or turn == human

def reset():
    global board, anim, turn, winner, win_line, win_anim, ai_at, particles
    board, anim = [" "]*9, [0.0]*9
    turn, winner, win_line, win_anim, particles = "X", None, None, 0.0, []
    ai_at = pygame.time.get_ticks() + 450 if (mode == "ai" and turn == ai) else 0

def burst(color):
    for _ in range(90):
        a, s = random.uniform(0, 6.28), random.uniform(2, 8)
        particles.append([W/2, BOARD_Y + BOARD_SIZE/2, math.cos(a)*s, math.sin(a)*s - 3,
                          random.choice([color, GOLD, TEXT]), random.randint(30, 70)])

def place(i, mark):
    global turn, winner, win_line, ai_at
    board[i] = mark
    anim[i] = 0.01
    w, line = check(board)
    if w:
        winner, win_line = w, line
        if w == "D":
            scores[1] += 1
        elif mode == "pvp":
            scores[0 if w == "X" else 2] += 1
            burst(mark_color(w))
        elif w == human:
            scores[0] += 1; burst(mark_color(human))
        else:
            scores[2] += 1
    else:
        turn = "O" if mark == "X" else "X"
        if mode == "ai" and turn == ai:
            ai_at = pygame.time.get_ticks() + 420


# ---------------- ปุ่ม ----------------
b_ai   = Button((60, 232, 200, 64), "เล่นกับ AI")
b_pvp  = Button((300, 232, 200, 64), "เล่น 2 คน")
b_x    = Button((150, 362, 110, 80), "X", F_BIG, X_COL)
b_o    = Button((300, 362, 110, 80), "O", F_BIG, O_COL)
b_e    = Button((60, 500, 140, 54), "ง่าย")
b_n    = Button((210, 500, 140, 54), "ปกติ")
b_h    = Button((360, 500, 140, 54), "เทพ")
b_go   = Button((140, 590, 280, 66), "เริ่มเกม", F_BIG)
b_new  = Button((52, 676, 220, 58), "เล่นใหม่", F_MID)
b_menu = Button((288, 676, 220, 58), "เมนู", F_MID)
b_ai.selected = b_x.selected = b_h.selected = True


def bg_gradient():
    for y in range(H):
        t = y / H
        screen.fill((int(lerp(BG[0], BG2[0], t)), int(lerp(BG[1], BG2[1], t)), int(lerp(BG[2], BG2[2], t))),
                    (0, y, W, 1))


def draw_menu(mouse):
    bg_gradient()
    text(screen, "TIC  TAC  TOE", F_TITLE, TEXT, (W//2, 110))
    text(screen, "เกม OX สู้กับ AI หรือดวลกับเพื่อน", F_MID, MUTED, (W//2, 152))

    text(screen, "โหมดการเล่น", F_MID, MUTED, (W//2, 205))
    b_ai.draw(screen, mouse); b_pvp.draw(screen, mouse)

    if mode == "ai":
        text(screen, "เลือกฝั่งของคุณ", F_MID, MUTED, (W//2, 336))
        b_x.draw(screen, mouse); b_o.draw(screen, mouse)
        text(screen, "ระดับความยาก", F_MID, MUTED, (W//2, 474))
        for b in (b_e, b_n, b_h): b.draw(screen, mouse)
        hint = "เทพ = Minimax เอาชนะไม่ได้ ดีที่สุดคือเสมอ"
    else:
        card = pygame.Rect(60, 326, 440, 228)
        pygame.draw.rect(screen, CARD, card, border_radius=18)
        text(screen, "โหมดผลัดกันเดิน", F_BIG, GOLD, (card.centerx, card.top + 40))
        r1 = pygame.Rect(card.centerx - 150, card.top + 84, 130, 70)
        r2 = pygame.Rect(card.centerx + 20, card.top + 84, 130, 70)
        for r, m in ((r1, "X"), (r2, "O")):
            pygame.draw.rect(screen, CARD_HL, r, border_radius=14)
            draw_mark(screen, 0, m, 0, TEXT)
            (draw_x if m == "X" else draw_o)(screen, r, 1.0, mark_color(m), 9)
        text(screen, "ผู้เล่น 1", F_SM, MUTED, (r1.centerx, r1.bottom + 20))
        text(screen, "ผู้เล่น 2", F_SM, MUTED, (r2.centerx, r2.bottom + 20))
        text(screen, "X เริ่มก่อนเสมอ · สลับกันเดินบนเครื่องเดียว", F_SM, MUTED, (card.centerx, card.bottom - 26))
        hint = "คลิกช่อง หรือกดปุ่มเลข 1-9 เพื่อเดิน"

    b_go.draw(screen, mouse)
    text(screen, hint, F_SM, MUTED, (W//2, 700))


def status_text():
    if winner is None:
        if mode == "pvp":
            return f"ตาผู้เล่น {turn}", mark_color(turn)
        return ("ตาคุณแล้ว", mark_color(turn)) if turn == human else ("AI กำลังคิด...", mark_color(turn))
    if winner == "D":
        return "เสมอกัน!", MUTED
    if mode == "pvp":
        return f"ผู้เล่น {winner} ชนะ!", GOLD
    return ("คุณชนะ!", GOLD) if winner == human else ("AI ชนะ!", O_COL)


def draw_game(mouse, t):
    bg_gradient()
    text(screen, "TIC  TAC  TOE", F_BIG, TEXT, (W//2, 42))

    label, col = status_text()
    pygame.draw.circle(screen, col, (W//2 - F_MID.size(label)[0]//2 - 18, 82), 7)
    text(screen, label, F_MID, col, (W//2 + 8, 82))

    if mode == "pvp":
        panels = [("ผู้เล่น X", scores[0], X_COL), ("เสมอ", scores[1], MUTED), ("ผู้เล่น O", scores[2], O_COL)]
    else:
        panels = [("คุณ", scores[0], mark_color(human)), ("เสมอ", scores[1], MUTED), ("AI", scores[2], mark_color(ai))]
    for idx, (name, val, c) in enumerate(panels):
        r = pygame.Rect(52 + idx * 156, 112, 144, 62)
        pygame.draw.rect(screen, CARD, r, border_radius=14)
        if winner is None and ((mode == "pvp" and idx == (0 if turn == "X" else 2)) or
                               (mode == "ai" and idx == (0 if turn == human else 2))):
            pygame.draw.rect(screen, c, r, 2, border_radius=14)
        text(screen, name, F_SM, MUTED, (r.centerx, r.top + 20))
        text(screen, str(val), F_BIG, c, (r.centerx, r.top + 43))

    pygame.draw.rect(screen, CARD, (BOARD_X-10, BOARD_Y-10, BOARD_SIZE+20, BOARD_SIZE+20), border_radius=22)
    for k in (1, 2):
        pygame.draw.rect(screen, LINE, (BOARD_X + k*CELL - 3, BOARD_Y + 14, 6, BOARD_SIZE - 28), border_radius=3)
        pygame.draw.rect(screen, LINE, (BOARD_X + 14, BOARD_Y + k*CELL - 3, BOARD_SIZE - 28, 6), border_radius=3)

    glow = (math.sin(t * 5) + 1) / 2
    for i in range(9):
        r = cell_rect(i)
        if win_line and i in win_line:
            g = int(30 + 45 * glow)
            pygame.draw.rect(screen, (CARD_HL[0]+g//3, CARD_HL[1]+g//3, CARD_HL[2]), r.inflate(-16, -16), border_radius=16)
        elif board[i] == " " and winner is None and is_my_turn() and r.collidepoint(mouse):
            pygame.draw.rect(screen, CARD_HL, r.inflate(-16, -16), border_radius=16)
            base = mark_color(turn)
            ghost = tuple(int(lerp(base[j], CARD_HL[j], 0.7)) for j in range(3))
            draw_mark(screen, i, turn, 1.0, ghost)
        elif board[i] == " " and winner is None:
            text(screen, str(i + 1), F_SM, (LINE[0]+6, LINE[1]+6, LINE[2]+6), r.center)
        if board[i] != " ":
            draw_mark(screen, i, board[i], anim[i], mark_color(board[i]))

    if win_line and win_anim > 0:
        a, b = cell_rect(win_line[0]).center, cell_rect(win_line[2]).center
        d = (b[0]-a[0], b[1]-a[1])
        n = math.hypot(*d) or 1
        off = (d[0]/n*34, d[1]/n*34)
        s, e = (a[0]-off[0], a[1]-off[1]), (b[0]+off[0], b[1]+off[1])
        end = lerp_pt(s, e, ease(min(1, win_anim)))
        pygame.draw.line(screen, GOLD, s, end, 10)
        pygame.draw.circle(screen, GOLD, (int(s[0]), int(s[1])), 5)
        pygame.draw.circle(screen, GOLD, (int(end[0]), int(end[1])), 5)

    for p in particles:
        pygame.draw.circle(screen, p[4], (int(p[0]), int(p[1])), max(1, p[5] // 18))

    b_new.draw(screen, mouse)
    b_menu.draw(screen, mouse)


# ---------------- ลูปหลัก ----------------
while True:
    dt = clock.tick(60) / 1000
    t = pygame.time.get_ticks() / 1000
    mouse = pygame.mouse.get_pos()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                state = "menu"
            elif e.key == pygame.K_r and state == "game":
                reset()
            elif state == "game" and winner is None and is_my_turn() and e.key in KEY_CELL:
                i = KEY_CELL[e.key]
                if board[i] == " ":
                    place(i, turn)

        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if state == "menu":
                if b_ai.hit(e.pos):
                    mode = "ai"; b_ai.selected, b_pvp.selected = True, False
                if b_pvp.hit(e.pos):
                    mode = "pvp"; b_ai.selected, b_pvp.selected = False, True
                if mode == "ai":
                    if b_x.hit(e.pos): b_x.selected, b_o.selected = True, False
                    if b_o.hit(e.pos): b_x.selected, b_o.selected = False, True
                    for b, d in ((b_e, 0), (b_n, 1), (b_h, 2)):
                        if b.hit(e.pos):
                            diff = d
                            b_e.selected, b_n.selected, b_h.selected = d == 0, d == 1, d == 2
                if b_go.hit(e.pos):
                    human = "X" if b_x.selected else "O"
                    ai = "O" if human == "X" else "X"
                    scores = [0, 0, 0]
                    reset(); state = "game"
            else:
                if b_new.hit(e.pos):
                    reset()
                elif b_menu.hit(e.pos):
                    state = "menu"
                elif winner is None and is_my_turn():
                    for i in range(9):
                        if board[i] == " " and cell_rect(i).collidepoint(e.pos):
                            place(i, turn); break

    if state == "game":
        for i in range(9):
            if 0 < anim[i] < 1:
                anim[i] = min(1.0, anim[i] + dt * 3.6)
        if win_line and all(anim[i] >= 1 for i in win_line):
            win_anim = min(1.2, win_anim + dt * 2.2)
        for p in particles[:]:
            p[0] += p[2]; p[1] += p[3]; p[3] += 0.25; p[5] -= 1
            if p[5] <= 0:
                particles.remove(p)
        if mode == "ai" and winner is None and turn == ai and pygame.time.get_ticks() >= ai_at:
            place(ai_pick(board[:], ai, human, diff), ai)

    draw_menu(mouse) if state == "menu" else draw_game(mouse, t)
    pygame.display.flip()