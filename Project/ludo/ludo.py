import tkinter as tk
import random
import os


# ==========================================
# LUDO GAME
# ==========================================

CELL = 36
BOARD = 15 * CELL

BG = "#0F172A"
PANEL = "#1E293B"
CELL_BG = "#E2E8F0"
LINE = "#94A3B8"

PLAYERS = ["red", "green", "yellow", "blue"]

COLORS = {
    "red":    {"main": "#E53935", "light": "#F4C7C5", "dark": "#7A1E1C"},
    "green":  {"main": "#43A047", "light": "#BFDFC1", "dark": "#1E5E22"},
    "yellow": {"main": "#FB8C00", "light": "#FCDDB4", "dark": "#8A4A00"},
    "blue":   {"main": "#1E88E5", "light": "#BCDBF4", "dark": "#0D4775"},
}

START_IDX = {"red": 0, "green": 13, "yellow": 26, "blue": 39}

# 52 cells of the main track, clockwise from red's start
PATH = [
    (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6),
    (0, 7),
    (0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8),
    (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14),
    (7, 14),
    (8, 14), (8, 13), (8, 12), (8, 11), (8, 10), (8, 9),
    (9, 8), (10, 8), (11, 8), (12, 8), (13, 8), (14, 8),
    (14, 7),
    (14, 6), (13, 6), (12, 6), (11, 6), (10, 6), (9, 6),
    (8, 5), (8, 4), (8, 3), (8, 2), (8, 1), (8, 0),
    (7, 0),
    (6, 0),
]

# 5-cell home column leading to the center, per player
HOME_COL = {
    "red":    [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5)],
    "green":  [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7)],
    "yellow": [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9)],
    "blue":   [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7)],
}

# safe squares (starts + starred cells)
SAFE = {0, 8, 13, 21, 26, 34, 39, 47}

# parking spots inside each home base
BASE_PARK = {
    "red":    [(1, 1), (1, 4), (4, 1), (4, 4)],
    "green":  [(1, 10), (1, 13), (4, 10), (4, 13)],
    "yellow": [(10, 10), (10, 13), (13, 10), (13, 13)],
    "blue":   [(10, 1), (10, 4), (13, 1), (13, 4)],
}

BASE_ORIGIN = {"red": (0, 0), "green": (0, 9), "yellow": (9, 9), "blue": (9, 0)}

# ---- state ----
# step meaning: 0 = in base, 1..51 = main track, 52..56 = home column, 57 = finished
tokens = {p: [0, 0, 0, 0] for p in PLAYERS}
current = 0
dice = 0
sixes = 0
waiting = False
movable = []
busy = False
winner = None
humans = {"red"}

root = None
canvas = None
dice_canvas = None
turn_label = None
status_label = None
token_items = []
highlight_items = []


# ==========================================
# POSITION HELPERS
# ==========================================

def cell_center(row, col):
    return (col * CELL + CELL // 2, row * CELL + CELL // 2)


def token_cell(player, step):
    if step == 0 or step == 57:
        return None
    if step <= 51:
        return PATH[(START_IDX[player] + step - 1) % 52]
    return HOME_COL[player][step - 52]


def abs_index(player, step):
    return (START_IDX[player] + step - 1) % 52


def stack_offset(n, k):
    if n == 1:
        return (0, 0)
    d = 6
    if n == 2:
        return [(-d, 0), (d, 0)][k]
    if n == 3:
        return [(-d, -d), (d, -d), (0, d)][k]
    return [(-d, -d), (d, -d), (-d, d), (d, d)][k]


def compute_positions():
    pos = {}
    on_board = {}
    for player in PLAYERS:
        for i in range(4):
            s = tokens[player][i]
            if s == 0:
                r, c = BASE_PARK[player][i]
                pos[(player, i)] = cell_center(r, c)
            elif s == 57:
                pos[(player, i)] = cell_center(7, 7)
            else:
                on_board.setdefault(token_cell(player, s), []).append((player, i))
    for cell, toks in on_board.items():
        r, c = cell
        cx, cy = cell_center(r, c)
        n = len(toks)
        for k, (p, i) in enumerate(toks):
            ox, oy = stack_offset(n, k)
            pos[(p, i)] = (cx + ox, cy + oy)
    return pos


# ==========================================
# RULES
# ==========================================

def can_move(player, idx, roll):
    s = tokens[player][idx]
    if s == 0:
        return roll == 6
    return s + roll <= 57


def movable_tokens(player, roll):
    return [i for i in range(4) if can_move(player, i, roll)]


def do_capture(player, new_s):
    if not (1 <= new_s <= 51):
        return False
    ai = abs_index(player, new_s)
    if ai in SAFE:
        return False
    captured = False
    for other in PLAYERS:
        if other == player:
            continue
        for j in range(4):
            o = tokens[other][j]
            if 1 <= o <= 51 and abs_index(other, o) == ai:
                tokens[other][j] = 0
                captured = True
    return captured


def move_token(player, idx, roll):
    global winner
    s = tokens[player][idx]
    tokens[player][idx] = 1 if s == 0 else s + roll
    captured = do_capture(player, tokens[player][idx])
    if all(t == 57 for t in tokens[player]):
        winner = player
    return captured


# ==========================================
# TURNS
# ==========================================

def ai_choose(player, options):
    # prefer a capturing move
    for i in options:
        s = tokens[player][i]
        ns = 1 if s == 0 else s + dice
        if 1 <= ns <= 51:
            ai = abs_index(player, ns)
            if ai not in SAFE:
                for other in PLAYERS:
                    if other == player:
                        continue
                    for j in range(4):
                        o = tokens[other][j]
                        if 1 <= o <= 51 and abs_index(other, o) == ai:
                            return i
    # prefer finishing a token
    for i in options:
        s = tokens[player][i]
        if s > 0 and s + dice == 57:
            return i
    # prefer bringing a token out on a six
    if dice == 6:
        for i in options:
            if tokens[player][i] == 0:
                return i
    # otherwise advance the furthest token
    return max(options, key=lambda i: tokens[player][i])


def do_roll():
    global dice, busy
    busy = True
    dice = random.randint(1, 6)
    draw_dice()
    msg(f"{PLAYERS[current].upper()} rolled a {dice}.")
    root.after(350, handle_roll)


def handle_roll():
    global waiting, movable, busy
    player = PLAYERS[current]
    movable = movable_tokens(player, dice)

    if not movable:
        msg(f"{player.upper()} has no valid moves.")
        root.after(800, end_turn)
        return

    if player in humans:
        if len(movable) == 1:
            apply_move(movable[0])
        else:
            waiting = True
            busy = False
            msg("Pick a token to move.")
            render_tokens()
    else:
        choice = ai_choose(player, movable)
        root.after(500, lambda: apply_move(choice))


def apply_move(idx):
    global waiting, sixes, busy
    waiting = False
    player = PLAYERS[current]
    captured = move_token(player, idx, dice)
    finished = tokens[player][idx] == 57
    render_tokens()

    if winner:
        msg(f"{player.upper()} wins the game!")
        busy = False
        return

    if dice == 6:
        sixes += 1
    else:
        sixes = 0

    if sixes >= 3:
        sixes = 0
        msg("Three sixes! Turn forfeited.")
        end_turn()
        return

    extra = (dice == 6) or captured or finished
    if extra:
        if player in humans:
            busy = False
            msg("Bonus roll! Click ROLL DICE.")
        else:
            root.after(700, do_roll)
    else:
        end_turn()


def end_turn():
    global current, dice, sixes, waiting, movable, busy
    current = (current + 1) % 4
    dice = 0
    sixes = 0
    waiting = False
    movable = []
    busy = PLAYERS[current] not in humans
    draw_dice()
    update_panel()
    render_tokens()
    if winner is None and busy:
        root.after(800, do_roll)


def on_roll():
    if winner is not None or waiting or busy:
        return
    if PLAYERS[current] not in humans:
        return
    do_roll()


def on_canvas_click(event):
    if not waiting or PLAYERS[current] not in humans:
        return
    pos = compute_positions()
    player = PLAYERS[current]
    best = None
    best_d = (CELL * 0.7) ** 2
    for i in movable:
        cx, cy = pos[(player, i)]
        d = (cx - event.x) ** 2 + (cy - event.y) ** 2
        if d < best_d:
            best_d = d
            best = i
    if best is not None:
        apply_move(best)


# ==========================================
# RENDERING
# ==========================================

def draw_board():
    canvas.delete("all")
    canvas.create_rectangle(0, 0, BOARD, BOARD, fill=BG, outline="")

    # home bases
    for player, (r0, c0) in BASE_ORIGIN.items():
        x1, y1 = c0 * CELL, r0 * CELL
        x2, y2 = (c0 + 6) * CELL, (r0 + 6) * CELL
        canvas.create_rectangle(x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                                fill=COLORS[player]["dark"], outline=LINE, width=2)
        canvas.create_rectangle(x1 + CELL, y1 + CELL, x2 - CELL, y2 - CELL,
                                fill=COLORS[player]["light"], outline="")
        for (pr, pc) in BASE_PARK[player]:
            cx, cy = cell_center(pr, pc)
            canvas.create_oval(cx - 15, cy - 15, cx + 15, cy + 15,
                               fill="white", outline=COLORS[player]["main"], width=2)

    # main track cells
    for idx, (r, c) in enumerate(PATH):
        x1, y1 = c * CELL, r * CELL
        x2, y2 = x1 + CELL, y1 + CELL
        fill = CELL_BG
        if idx in START_IDX.values():
            for p, si in START_IDX.items():
                if si == idx:
                    fill = COLORS[p]["light"]
        canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                                fill=fill, outline=LINE)
        if idx in SAFE:
            cx, cy = cell_center(r, c)
            canvas.create_text(cx, cy, text="\u2605", fill="#475569",
                               font=("Arial", 14))

    # home column cells
    for player, cells in HOME_COL.items():
        for (r, c) in cells:
            x1, y1 = c * CELL, r * CELL
            x2, y2 = x1 + CELL, y1 + CELL
            canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                                    fill=COLORS[player]["light"], outline=LINE)

    # center finish area (4 triangles)
    cx, cy = cell_center(7, 7)
    h = CELL * 3 // 2
    x1, y1, x2, y2 = cx - h, cy - h, cx + h, cy + h
    canvas.create_polygon(x1, y1, x2, y1, cx, cy, fill=COLORS["green"]["main"], outline=LINE)
    canvas.create_polygon(x2, y1, x2, y2, cx, cy, fill=COLORS["yellow"]["main"], outline=LINE)
    canvas.create_polygon(x2, y2, x1, y2, cx, cy, fill=COLORS["blue"]["main"], outline=LINE)
    canvas.create_polygon(x1, y2, x1, y1, cx, cy, fill=COLORS["red"]["main"], outline=LINE)


def render_tokens():
    global token_items
    for it in token_items:
        canvas.delete(it)
    token_items = []
    pos = compute_positions()
    for player in PLAYERS:
        for i in range(4):
            cx, cy = pos[(player, i)]
            r = 11
            outline = "#FFFFFF"
            ow = 2
            if waiting and PLAYERS[current] == player and i in movable:
                outline = "#FACC15"
                ow = 3
            item = canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                      fill=COLORS[player]["main"],
                                      outline=outline, width=ow)
            token_items.append(item)


def draw_dice():
    dice_canvas.delete("all")
    dice_canvas.create_rectangle(2, 2, 78, 78, fill="white", outline=LINE, width=2)
    if dice == 0:
        return
    pips = {
        1: [(40, 40)],
        2: [(26, 26), (54, 54)],
        3: [(26, 26), (40, 40), (54, 54)],
        4: [(26, 26), (54, 26), (26, 54), (54, 54)],
        5: [(26, 26), (54, 26), (40, 40), (26, 54), (54, 54)],
        6: [(26, 24), (54, 24), (26, 40), (54, 40), (26, 56), (54, 56)],
    }
    for (px, py) in pips.get(dice, []):
        dice_canvas.create_oval(px - 6, py - 6, px + 6, py + 6, fill=PANEL)


def highlight_base():
    global highlight_items
    for it in highlight_items:
        canvas.delete(it)
    highlight_items = []
    player = PLAYERS[current]
    r0, c0 = BASE_ORIGIN[player]
    x1, y1 = c0 * CELL, r0 * CELL
    x2, y2 = (c0 + 6) * CELL, (r0 + 6) * CELL
    highlight_items.append(canvas.create_rectangle(
        x1 + 2, y1 + 2, x2 - 2, y2 - 2,
        outline=COLORS[player]["main"], width=4))
    highlight_items.append(canvas.create_rectangle(
        x1 + 6, y1 + 6, x2 - 6, y2 - 6,
        outline=COLORS[player]["light"], width=2))


def update_panel():
    player = PLAYERS[current]
    turn_label.config(text=f"{player.upper()}'s Turn", fg=COLORS[player]["main"])
    highlight_base()


def msg(text):
    status_label.config(text=text)


# ==========================================
# NEW GAME
# ==========================================

def new_game():
    global tokens, current, dice, sixes, waiting, movable, busy, winner
    tokens = {p: [0, 0, 0, 0] for p in PLAYERS}
    current = 0
    dice = 0
    sixes = 0
    waiting = False
    movable = []
    busy = False
    winner = None
    draw_dice()
    update_panel()
    render_tokens()
    msg("Click ROLL DICE to start.")


# ==========================================
# MAIN WINDOW
# ==========================================

def init_game(human_set):
    global root, canvas, dice_canvas, turn_label, status_label, humans
    humans = human_set
    root = tk.Tk()
    root.title("Ludo")
    root.configure(bg=BG)
    root.resizable(False, False)

    main = tk.Frame(root, bg=BG)
    main.pack(padx=14, pady=14)

    canvas = tk.Canvas(main, width=BOARD, height=BOARD, bg=BG, highlightthickness=0)
    canvas.grid(row=0, column=0, padx=(0, 14))
    canvas.bind("<Button-1>", on_canvas_click)

    side = tk.Frame(main, bg=BG, width=190)
    side.grid(row=0, column=1, sticky="n")

    tk.Label(side, text="LUDO", font=("Arial", 28, "bold"),
             bg=BG, fg="white").pack(pady=(0, 18))

    turn_label = tk.Label(side, text="RED's Turn", font=("Arial", 15, "bold"),
                          bg=BG, fg=COLORS["red"]["main"])
    turn_label.pack(pady=(0, 18))

    dice_canvas = tk.Canvas(side, width=80, height=80, bg=PANEL, highlightthickness=0)
    dice_canvas.pack(pady=(0, 12))
    draw_dice()

    tk.Button(side, text="ROLL DICE", font=("Arial", 13, "bold"),
              bg="#2563EB", fg="white", activebackground="#3B82F6",
              relief="flat", cursor="hand2", width=14,
              command=on_roll).pack(pady=4)

    tk.Button(side, text="NEW GAME", font=("Arial", 11, "bold"),
              bg="#475569", fg="white", activebackground="#64748B",
              relief="flat", cursor="hand2", width=14,
              command=new_game).pack(pady=4)

    status_label = tk.Label(side, text="Click ROLL DICE to start.",
                            font=("Arial", 10), bg=BG, fg="#94A3B8", wraplength=180)
    status_label.pack(pady=(14, 0))

    leg = tk.Frame(side, bg=BG)
    leg.pack(pady=(22, 0))
    for p in PLAYERS:
        row = tk.Frame(leg, bg=BG)
        row.pack(anchor="w", pady=3)
        dot = tk.Canvas(row, width=14, height=14, bg=BG, highlightthickness=0)
        dot.pack(side="left")
        dot.create_oval(1, 1, 13, 13, fill=COLORS[p]["main"], outline="")
        label = p.upper() + ("  (You)" if p in humans else "  (AI)")
        tk.Label(row, text=label, font=("Arial", 9, "bold"),
                 bg=BG, fg="white").pack(side="left")

    draw_board()
    render_tokens()
    update_panel()


# ==========================================
# START MENU
# ==========================================

def launch(menu, human_set):
    menu.destroy()
    init_game(human_set)
    root.mainloop()


def start_menu():
    menu = tk.Tk()
    menu.title("Ludo")
    menu.configure(bg=BG)
    menu.resizable(False, False)

    tk.Label(menu, text="LUDO", font=("Arial", 38, "bold"),
             bg=BG, fg="white").pack(pady=(34, 8))
    tk.Label(menu, text="Select number of players", font=("Arial", 13),
             bg=BG, fg="#94A3B8").pack(pady=(0, 26))

    modes = [
        ("Single Player", "1 human  +  3 AI", {"red"}),
        ("Double Player", "2 humans  +  2 AI", {"red", "green"}),
        ("Triple Player", "3 humans  +  1 AI", {"red", "green", "yellow"}),
        ("Four Player",  "4 humans  (manual)", {"red", "green", "yellow", "blue"}),
    ]
    for title, desc, hset in modes:
        tk.Button(menu, text=f"{title}\n{desc}", font=("Arial", 12, "bold"),
                  bg=PANEL, fg="white", activebackground="#33445D",
                  relief="flat", cursor="hand2", width=22, pady=10,
                  command=lambda h=hset: launch(menu, h)).pack(pady=6, padx=44)

    tk.Label(menu, text="", bg=BG).pack(pady=(6, 14))
    return menu


if __name__ == "__main__":
    if os.environ.get("LUDO_SMOKE"):
        init_game({"red"})
        root.update()
        root.destroy()
    else:
        menu = start_menu()
        menu.mainloop()