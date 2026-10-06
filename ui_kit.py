"""
ui_kit.py
=========
Reusable look-and-feel for the Hangman game: colours, fonts and small custom
widgets (rounded buttons, cards, hangman drawing, letter tiles, icons...).

Only the standard library (tkinter) is used, so nothing needs to be installed.
Everything is drawn on Canvas widgets - that is how we get rounded corners,
soft shadows and icons that look the same on Windows, macOS and Linux
(emoji fonts are NOT used because they render differently on every system).
"""

import math
import tkinter as tk
from tkinter import font as tkfont

# --------------------------------------------------------------------------
# Colour palette: "Explorer's parchment" - warm paper, deep ink, teal + coral
# --------------------------------------------------------------------------
BG = "#F4ECD8"            # parchment background
CARD = "#FFFBF0"          # card surface
CARD_BORDER = "#E6D9B8"
SHADOW = "#DCCFAB"        # soft card shadow
INK = "#2B2D42"           # main text
INK_SOFT = "#7A7C8E"      # secondary text
TILE_EMPTY = "#F2E9CF"

TEAL = "#2A9D8F"
TEAL_DARK = "#1F7A6F"
TEAL_LIGHT = "#D3EDE8"

CORAL = "#E4572E"
CORAL_DARK = "#B9411F"
CORAL_LIGHT = "#F9D9CE"

GOLD = "#E9B44C"
GOLD_DARK = "#C48F2A"
GOLD_LIGHT = "#F8E6B8"

WOOD = "#8A5A3B"
WHITE = "#FFFFFF"

# Accent colour + soft tint for each category (used by cards and chips)
CATEGORY_STYLE = {
    "animals":   ("#C77D3A", "#F6E3CF"),
    "flowers":   ("#D9628B", "#F9DCE6"),
    "fruits":    ("#D64545", "#F9D8D4"),
    "countries": ("#2F7FBF", "#D6E8F6"),
}
# Word shown above the letter tiles ("SECRET ANIMAL")
CATEGORY_SINGULAR = {"animals": "animal", "flowers": "flower",
                     "fruits": "fruit", "countries": "country"}

# --------------------------------------------------------------------------
# Fonts - pick the nicest font that is installed on this computer
# --------------------------------------------------------------------------
_FAMILY = {"ui": "Helvetica", "display": "Helvetica"}


def init_fonts(root):
    """Call once after creating the Tk window."""
    available = set(tkfont.families(root))

    def pick(candidates, fallback):
        for name in candidates:
            if name in available:
                return name
        return fallback

    _FAMILY["ui"] = pick(["Nunito", "Segoe UI", "SF Pro Text", "Helvetica Neue",
                          "Verdana", "DejaVu Sans", "Arial"], "Helvetica")
    _FAMILY["display"] = pick(["Nunito", "Trebuchet MS", "Avenir Next", "Segoe UI",
                               "Helvetica Neue", "DejaVu Sans", "Arial"], "Helvetica")


def font(size, weight="normal", display=False):
    """size > 0 = points (for Labels), size < 0 = pixels (for canvas drawing)."""
    return (_FAMILY["display" if display else "ui"], size, weight)


# --------------------------------------------------------------------------
# Small drawing helpers
# --------------------------------------------------------------------------
def lerp_color(c1, c2, t):
    """Blend two '#RRGGBB' colours (t=0 -> c1, t=1 -> c2)."""
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Rounded rectangle on a canvas."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def heart_points(cx, cy, size):
    pts = []
    for i in range(64):
        t = i / 64 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts += [cx + x * size / 34, cy - y * size / 34 + size * 0.04]
    return pts


def draw_category_icon(c, key, cx, cy, size, tag="icon"):
    """Vector icons for the four categories (no emoji fonts needed)."""
    accent, tint = CATEGORY_STYLE[key]
    s = size
    if key == "animals":                                     # paw print
        c.create_oval(cx - .27*s, cy - .02*s, cx + .27*s, cy + .36*s, fill=accent, outline="", tags=tag)
        for dx, dy in ((-.36, -.14), (-.13, -.33), (.13, -.33), (.36, -.14)):
            c.create_oval(cx + dx*s - .11*s, cy + dy*s - .14*s,
                          cx + dx*s + .11*s, cy + dy*s + .14*s, fill=accent, outline="", tags=tag)
    elif key == "flowers":                                   # five-petal flower
        for k in range(5):
            a = math.radians(-90 + k * 72)
            px, py = cx + math.cos(a) * .21*s, cy + math.sin(a) * .21*s
            c.create_oval(px - .17*s, py - .17*s, px + .17*s, py + .17*s,
                          fill=accent, outline="", tags=tag)
        c.create_oval(cx - .13*s, cy - .13*s, cx + .13*s, cy + .13*s, fill=GOLD, outline="", tags=tag)
    elif key == "fruits":                                    # apple
        c.create_oval(cx - .40*s, cy - .22*s, cx + .02*s, cy + .36*s, fill=accent, outline="", tags=tag)
        c.create_oval(cx - .02*s, cy - .22*s, cx + .40*s, cy + .36*s, fill=accent, outline="", tags=tag)
        c.create_line(cx, cy - .16*s, cx + .04*s, cy - .38*s, fill=WOOD, width=max(2, s*.06),
                      capstyle="round", tags=tag)
        c.create_polygon(cx + .06*s, cy - .26*s, cx + .22*s, cy - .42*s, cx + .36*s, cy - .30*s,
                         cx + .18*s, cy - .22*s, fill="#4C9A5B", outline="", smooth=True, tags=tag)
    elif key == "countries":                                 # globe
        r = .40 * s
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=accent, outline="", tags=tag)
        lw = max(1.5, s * .035)
        c.create_oval(cx - r*.45, cy - r, cx + r*.45, cy + r, outline=WHITE, width=lw, tags=tag)
        c.create_line(cx - r, cy, cx + r, cy, fill=WHITE, width=lw, tags=tag)
        c.create_line(cx, cy - r, cx, cy + r, fill=WHITE, width=lw, tags=tag)
        for dy in (-.5, .5):
            half = math.sqrt(1 - dy * dy) * r
            c.create_line(cx - half, cy + dy*r, cx + half, cy + dy*r, fill=WHITE, width=lw, tags=tag)


# --------------------------------------------------------------------------
# Rounded button with hover / pressed / disabled states
# --------------------------------------------------------------------------
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, *, width=150, height=48, radius=14,
                 bg=BG, fill=TEAL, hover=TEAL_DARK, text_color=WHITE, border=None,
                 shadow=TEAL_DARK, font_spec=None, depth=4):
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.text = text
        self.command = command
        self.radius = radius
        self.depth = depth
        self.font_spec = font_spec or font(-16, "bold")
        self.colors = dict(fill=fill, hover=hover, text=text_color, border=border, shadow=shadow)
        self.enabled = True
        self._hover = False
        self._pressed = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    # ----- public API ----------------------------------------------------
    def set_text(self, text):
        self.text = text
        self._draw()

    def set_colors(self, **kw):
        self.colors.update(kw)
        self._draw()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._hover = self._pressed = False
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    # ----- events --------------------------------------------------------
    def _on_enter(self, _):
        self._hover = True
        self._draw()

    def _on_leave(self, _):
        self._hover = self._pressed = False
        self._draw()

    def _on_press(self, _):
        if self.enabled:
            self._pressed = True
            self._draw()

    def _on_release(self, e):
        was_pressed = self._pressed
        self._pressed = False
        self._draw()
        inside = 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height()
        if was_pressed and inside and self.enabled and self.command:
            self.command()

    # ----- drawing -------------------------------------------------------
    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8:                                   # not mapped yet
            w, h = int(self["width"]), int(self["height"])
        d, c = self.depth, self.colors
        raised = self.enabled and not self._pressed
        off = 0 if raised else (d // 2 if self.enabled else d - 1)
        face_fill = c["hover"] if (self._hover and self.enabled) else c["fill"]
        r = min(self.radius, (h - d) // 2)
        if self.enabled and c["shadow"]:
            round_rect(self, 1, 1 + d, w - 1, h - 1, r, fill=c["shadow"], outline="")
        round_rect(self, 1, 1 + off, w - 1, h - d - 1 + off + (0 if self.enabled else d - 1), r,
                   fill=face_fill, outline=c["border"] or "", width=2 if c["border"] else 1)
        self.create_text(w / 2, (h - d) / 2 + 1 + off, text=self.text, fill=c["text"],
                         font=self.font_spec)


# --------------------------------------------------------------------------
# Card: rounded panel with a soft shadow. Put your widgets in card.inner
# --------------------------------------------------------------------------
class Card(tk.Canvas):
    """
    stretch=True  -> the content area always fills the card (use when the card
                     is stretched by a grid, e.g. the keyboard card).
    stretch=False -> the card hugs its content and grows/shrinks with it
                     (use for result card, score boxes).
    """
    def __init__(self, parent, *, bg=BG, fill=CARD, border=CARD_BORDER, radius=22, pad=16, stretch=True):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0)
        self.fill, self.border, self.radius, self.pad, self.stretch = fill, border, radius, pad, stretch
        self.shadow_h = 6
        self.inner = tk.Frame(self, bg=fill)
        self._win = self.create_window(pad, pad, window=self.inner, anchor="nw")
        self.bind("<Configure>", self._on_resize)
        self.inner.bind("<Configure>", self._on_inner)

    def _on_inner(self, _):
        # the card asks for exactly as much room as its content needs
        self.configure(width=self.inner.winfo_reqwidth() + 2 * self.pad,
                       height=self.inner.winfo_reqheight() + 2 * self.pad + self.shadow_h)

    def _on_resize(self, e):
        self.delete("bg")
        sh = self.shadow_h
        round_rect(self, 2, 2 + sh, e.width - 2, e.height - 1, self.radius, fill=SHADOW, outline="", tags="bg")
        round_rect(self, 2, 2, e.width - 2, e.height - sh - 1, self.radius,
                   fill=self.fill, outline=self.border, width=2, tags="bg")
        self.tag_lower("bg")
        if self.stretch:
            self.itemconfigure(self._win, width=max(1, e.width - 2 * self.pad),
                               height=max(1, e.height - 2 * self.pad - sh))


class StatCard(Card):
    """Small card with a caption and a big value, e.g. SCORE / 125."""
    def __init__(self, parent, title, value="0", *, bg=BG, value_color=INK):
        super().__init__(parent, bg=bg, radius=16, pad=10, stretch=False)
        tk.Label(self.inner, text=title, bg=CARD, fg=INK_SOFT, font=font(8, "bold")).pack(anchor="w")
        self.value_label = tk.Label(self.inner, text=value, bg=CARD, fg=value_color,
                                    font=font(20, "bold", display=True), width=6, anchor="w")
        self.value_label.pack(anchor="w")

    def set(self, value, color=None):
        self.value_label.configure(text=str(value))
        if color:
            self.value_label.configure(fg=color)


# --------------------------------------------------------------------------
# Logo: "HANGMAN" as tiles, with the middle tile dangling from a rope
# --------------------------------------------------------------------------
class LogoCanvas(tk.Canvas):
    COLORS = [(TEAL, WHITE), (GOLD, INK), (CORAL, WHITE), (TEAL, WHITE),
              (GOLD, INK), (CORAL, WHITE), (TEAL, WHITE)]

    def __init__(self, parent, tile=60, bg=BG):
        gap = max(4, tile // 8)
        self.tile, self.gap = tile, gap
        self.drop = int(tile * 0.30)            # how far the dangling tile hangs
        self.rope = int(tile * 0.30)
        width = 7 * tile + 6 * gap + 8
        height = tile + self.drop + self.rope + 8
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, bd=0)
        t, g = tile, gap
        for i, letter in enumerate("HANGMAN"):
            x = 4 + i * (t + g)
            y = 4 + self.rope + (self.drop if i == 3 else 0)
            fill, fg = self.COLORS[i]
            round_rect(self, x, y + 4, x + t, y + t + 4, t * .22, fill=lerp_color(fill, INK, .25), outline="")
            round_rect(self, x, y, x + t, y + t, t * .22, fill=fill, outline="")
            self.create_text(x + t / 2, y + t / 2, text=letter, fill=fg, font=font(-int(t * .58), "bold", True))
            if i == 3:                           # the rope
                self.create_line(x + t / 2, 0, x + t / 2, y, fill=WOOD, width=max(2, t // 16))
                self.create_oval(x + t / 2 - 4, y - 4, x + t / 2 + 4, y + 4, fill=WOOD, outline="")


# --------------------------------------------------------------------------
# Category pill shown in the game header
# --------------------------------------------------------------------------
class CategoryChip(tk.Canvas):
    def __init__(self, parent, bg=BG):
        super().__init__(parent, width=200, height=50, bg=bg, highlightthickness=0, bd=0)

    def set_category(self, key, name):
        self.delete("all")
        accent, tint = CATEGORY_STYLE[key]
        round_rect(self, 2, 2, 198, 46, 22, fill=CARD, outline=CARD_BORDER, width=2)
        self.create_oval(7, 6, 43, 42, fill=tint, outline="")
        draw_category_icon(self, key, 25, 24, 26)
        self.create_text(54, 24, text=name.upper(), anchor="w", fill=INK, font=font(-16, "bold", True))


# --------------------------------------------------------------------------
# Category card for the home screen
# --------------------------------------------------------------------------
class CategoryCard(tk.Canvas):
    def __init__(self, parent, key, name, count, index, on_select, on_play, bg=BG):
        super().__init__(parent, width=190, height=230, bg=bg, highlightthickness=0, bd=0, cursor="hand2")
        self.key, self.name, self.count, self.index = key, name, count, index
        self.selected = False
        self._hover = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", lambda e: on_select(index))
        self.bind("<Double-Button-1>", lambda e: on_play(index))

    def _set_hover(self, flag):
        self._hover = flag
        self._draw()

    def set_selected(self, flag):
        self.selected = flag
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            w, h = int(self["width"]), int(self["height"])
        accent, tint = CATEGORY_STYLE[self.key]
        lift = 5 if (self._hover and not self.selected) else 0
        top, bottom = 6 - lift, h - 12 - lift
        round_rect(self, 5, 12, w - 5, h - 3, 24, fill=SHADOW, outline="")
        round_rect(self, 5, top, w - 5, bottom, 24,
                   fill="#F3FBF9" if self.selected else CARD,
                   outline=TEAL if self.selected else CARD_BORDER, width=4 if self.selected else 2)
        face_h = bottom - top
        r = min(w, face_h) * .27
        cx, cy = w / 2, top + face_h * .38
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=tint, outline="")
        draw_category_icon(self, self.key, cx, cy, r * 1.45)
        px = int(max(18, min(26, face_h * .09)))
        self.create_text(cx, top + face_h * .74, text=self.name, fill=INK, font=font(-px, "bold", True))
        self.create_text(cx, top + face_h * .74 + px * 1.5, text=f"{self.count} words",
                         fill=INK_SOFT, font=font(-13))
        if self.selected:                       # check badge
            bx, by = w - 30, top + 26
            self.create_oval(bx - 14, by - 14, bx + 14, by + 14, fill=TEAL, outline="")
            self.create_line(bx - 6, by, bx - 1, by + 5, bx + 7, by - 5, fill=WHITE, width=3,
                             capstyle="round", joinstyle="round")


# --------------------------------------------------------------------------
# Hearts (remaining lives)
# --------------------------------------------------------------------------
class LivesCanvas(tk.Canvas):
    def __init__(self, parent, maximum=6, size=22, bg=CARD):
        self.maximum, self.size, self.gap = maximum, size, 8
        width = maximum * size + (maximum - 1) * self.gap + 4
        super().__init__(parent, width=width, height=size + 8, bg=bg, highlightthickness=0, bd=0)
        self.lives = maximum
        self._flash_index = None
        self._after = None
        self._draw()

    def set_lives(self, lives, flash=False):
        self.lives = lives
        self._flash_index = lives if flash else None
        self._draw()
        if flash:
            if self._after:
                self.after_cancel(self._after)
            self._after = self.after(450, self._end_flash)

    def _end_flash(self):
        self._after = None
        self._flash_index = None
        try:
            self._draw()
        except tk.TclError:
            pass

    def _draw(self):
        self.delete("all")
        s = self.size
        for i in range(self.maximum):
            cx = 2 + s / 2 + i * (s + self.gap)
            cy = self.winfo_reqheight() / 2
            if i < self.lives:
                self.create_polygon(heart_points(cx, cy, s), fill=CORAL, outline=CORAL_DARK, width=1)
            elif i == self._flash_index:
                self.create_polygon(heart_points(cx, cy, s * 1.2), fill=CORAL_LIGHT, outline=CORAL, width=2)
            else:
                self.create_polygon(heart_points(cx, cy, s), fill="#EFE5CA", outline="#D9CCA8", width=1)


# --------------------------------------------------------------------------
# The Hangman illustration (gallows + figure)
# --------------------------------------------------------------------------
class HangmanCanvas(tk.Canvas):
    BASE_W, BASE_H = 300, 340

    def __init__(self, parent, bg=CARD, width=300, height=340):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, bd=0)
        self.stage = 0
        self._flash = False
        self._after = None
        self.bind("<Configure>", lambda e: self._draw())

    def set_stage(self, stage, flash=False):
        self.stage = stage
        self._flash = flash
        self._draw()
        if flash:
            if self._after:
                self.after_cancel(self._after)
            self._after = self.after(600, self._end_flash)

    def _end_flash(self):
        self._after = None
        self._flash = False
        try:
            self._draw()
        except tk.TclError:
            pass

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            w, h = int(self["width"]), int(self["height"])
        s = min(w / self.BASE_W, h / self.BASE_H)
        ox, oy = (w - self.BASE_W * s) / 2, (h - self.BASE_H * s) / 2

        def P(x, y):
            return ox + x * s, oy + y * s

        def line(x1, y1, x2, y2, color, width):
            a, b = P(x1, y1), P(x2, y2)
            self.create_line(*a, *b, fill=color, width=max(2, width * s), capstyle="round")

        def oval(x1, y1, x2, y2, **kw):
            a, b = P(x1, y1), P(x2, y2)
            self.create_oval(*a, *b, **kw)

        # --- scenery: sun, cloud, grass -------------------------------
        oval(244, 22, 284, 62, fill=GOLD_LIGHT, outline="")
        for cx_, cy_, rx in ((38, 66, 20), (58, 58, 22), (78, 68, 18)):
            oval(cx_ - rx, cy_ - 12, cx_ + rx, cy_ + 12, fill="#F1EBDB", outline="")
        oval(14, 286, 286, 336, fill="#DCE9D2", outline="")

        # --- gallows -----------------------------------------------------
        line(48, 306, 196, 306, WOOD, 10)       # base
        line(92, 306, 92, 52, WOOD, 10)         # post
        line(86, 52, 214, 52, WOOD, 10)         # beam
        line(92, 104, 140, 54, WOOD, 7)         # brace
        line(210, 54, 210, 92, "#B89B72", 4)    # rope

        # --- the figure, one body part per wrong guess -----------------------
        def colour(part):
            return CORAL if (self._flash and self.stage == part) else INK

        if self.stage >= 1:                                      # head
            oval(185, 92, 235, 142, outline=colour(1), width=max(2, 6 * s), fill=CARD)
            if self.stage >= 6:                                  # X eyes
                for ex in (202, 218):
                    line(ex - 4, 112 - 4, ex + 4, 112 + 4, CORAL, 3)
                    line(ex - 4, 112 + 4, ex + 4, 112 - 4, CORAL, 3)
                line(203, 129, 217, 129, INK, 3)
            else:
                for ex in (202, 218):
                    oval(ex - 2.6, 110, ex + 2.6, 115.2, fill=INK, outline="")
                line(204, 128, 216, 128, INK, 3)
        if self.stage >= 2:
            line(210, 142, 210, 214, colour(2), 6)               # body
        if self.stage >= 3:
            line(210, 160, 178, 194, colour(3), 6)               # arm
        if self.stage >= 4:
            line(210, 160, 242, 194, colour(4), 6)               # arm
        if self.stage >= 5:
            line(210, 214, 184, 264, colour(5), 6)               # leg
        if self.stage >= 6:
            line(210, 214, 236, 264, colour(6), 6)               # leg


# --------------------------------------------------------------------------
# The secret word: one tile per letter, with flash + floating "+5" feedback
# --------------------------------------------------------------------------
class WordDisplay(tk.Canvas):
    def __init__(self, parent, bg=CARD):
        super().__init__(parent, bg=bg, highlightthickness=0, bd=0, height=96, width=300)
        self.surface = bg
        self.answer = ""
        self.hint = []
        self.missed = set()
        self._flash = {}
        self._floats = []
        self._slots = []
        self._anim = None
        self.bind("<Configure>", lambda e: self._draw())

    def set_word(self, answer, hint):
        self.answer, self.hint = answer, list(hint)
        self.missed.clear()
        self._flash.clear()
        self.delete("float")
        self._floats.clear()
        self._draw()

    def reveal(self, positions, hint, text="+5"):
        self.hint = list(hint)
        for i in positions:
            self._flash[i] = 0.0
        if positions and self._slots:
            x, y, tile = self._slots[positions[0]]
            item = self.create_text(x + tile / 2, y - 2, text=text, fill=TEAL,
                                    font=font(-22, "bold", True), tags="float")
            self._floats.append({"id": item, "x": x + tile / 2, "y": y - 2, "t": 0.0})
        self._start_anim()

    def show_missing(self):
        """After losing: reveal the letters the player never found (in coral)."""
        for i, ch in enumerate(self.answer):
            if self.hint[i] == "_":
                self.hint[i] = ch
                self.missed.add(i)
        self._draw()

    def _start_anim(self):
        if self._anim is None:
            self._anim = self.after(30, self._tick)

    def _tick(self):
        self._anim = None
        for i in list(self._flash):
            self._flash[i] += 0.07
            if self._flash[i] >= 1:
                del self._flash[i]
        for f in list(self._floats):
            f["t"] += 0.04
            if f["t"] >= 1:
                self.delete(f["id"])
                self._floats.remove(f)
            else:
                self.coords(f["id"], f["x"], f["y"] - 30 * f["t"])
                self.itemconfigure(f["id"], fill=lerp_color(TEAL, self.surface, f["t"] ** 2))
        self._draw()
        if self._flash or self._floats:
            self._start_anim()

    def _draw(self):
        self.delete("tile")
        n = len(self.answer)
        if not n:
            return
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            w, h = int(self["width"]), int(self["height"])
        gap = 8
        units = [0.5 if ch == " " else 1.0 for ch in self.answer]
        tile = max(18, min(58, (w - 24 - gap * (n - 1)) / sum(units)))
        total = sum(u * tile for u in units) + gap * (n - 1)
        x, th = (w - total) / 2, tile * 1.2
        y = (h - th) / 2 + 8
        self._slots = []
        for i, ch in enumerate(self.answer):
            slot_w = units[i] * tile
            self._slots.append((x, y, tile))
            if ch != " ":
                revealed = self.hint[i] != "_"
                if i in self.missed:
                    fill, border, fg = CORAL_LIGHT, CORAL, CORAL
                elif i in self._flash:
                    t = self._flash[i]
                    fill, border, fg = lerp_color(TEAL, WHITE, t), TEAL, lerp_color(WHITE, INK, t)
                elif revealed:
                    fill, border, fg = WHITE, TEAL, INK
                else:
                    fill, border, fg = TILE_EMPTY, TILE_EMPTY, INK
                round_rect(self, x, y, x + tile, y + th, tile * .22, fill=fill, outline=border,
                           width=2, tags="tile")
                if revealed:
                    self.create_text(x + tile / 2, y + th / 2, text=self.hint[i].upper(), fill=fg,
                                     font=font(-int(tile * .6), "bold", True), tags="tile")
                else:
                    self.create_line(x + tile * .24, y + th * .74, x + tile * .76, y + th * .74,
                                     fill=INK_SOFT, width=3, capstyle="round", tags="tile")
            x += slot_w + gap
