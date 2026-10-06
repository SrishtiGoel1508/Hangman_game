"""
main.py  -  run this file to play:   python main.py
=====================================================
Screens
  HomeScreen   - pick a category card, press PLAY
  GameScreen   - hangman drawing, secret word, A-Z keyboard, score
  ResultScreen - win (confetti) or game over, with the score breakdown

Rules live in game_logic.py, drawing helpers in ui_kit.py.
"""

import math
import random
import tkinter as tk
from tkinter import messagebox

import ui_kit as ui
from ui_kit import (BG, CARD, INK, INK_SOFT, TEAL, TEAL_DARK, TEAL_LIGHT, CORAL, CORAL_DARK,
                    CORAL_LIGHT, GOLD, WHITE, CARD_BORDER, Card, StatCard, RoundedButton)
from game_logic import (GameSession, CATEGORIES, MAX_WRONG, POINTS_PER_CORRECT_GUESS,
                        WIN_BONUS, BONUS_PER_LIFE_LEFT)


# ==========================================================================
# Small helpers for the three screens
# ==========================================================================
def primary_button(parent, text, command, bg=BG, width=200, height=54):
    return RoundedButton(parent, text, command, width=width, height=height, bg=bg,
                         fill=TEAL, hover=TEAL_DARK, shadow=TEAL_DARK, radius=16,
                         font_spec=ui.font(-17, "bold"))


def secondary_button(parent, text, command, bg=BG, width=200, height=54):
    return RoundedButton(parent, text, command, width=width, height=height, bg=bg,
                         fill=WHITE, hover=TEAL_LIGHT, text_color=INK, border=CARD_BORDER,
                         shadow=CARD_BORDER, radius=16, font_spec=ui.font(-16, "bold"))


def danger_button(parent, text, command, bg=BG, width=200, height=54):
    return RoundedButton(parent, text, command, width=width, height=height, bg=bg,
                         fill=CORAL_LIGHT, hover="#F4C3B3", text_color=CORAL_DARK,
                         shadow="#EDB5A3", radius=16, font_spec=ui.font(-16, "bold"))


def animate_number(label, start, end, prefix="", steps=24, delay=22):
    """Count a label up from start to end (used on the result screen)."""
    def step(i):
        try:
            value = round(start + (end - start) * min(1, i / steps))
            label.configure(text=f"{prefix}{value}")
            if i < steps:
                label.after(delay, step, i + 1)
        except tk.TclError:
            pass                     # window was closed mid-animation
    step(0)


# ==========================================================================
# HOME SCREEN
# ==========================================================================
class HomeScreen(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=BG)
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ---- top bar: score, help, quit ---------------------------------
        top = tk.Frame(self, bg=BG)
        top.grid(row=0, column=0, sticky="ew", padx=32, pady=(20, 0))
        top.columnconfigure(0, weight=1)
        self.score_card = StatCard(top, "TOTAL SCORE", "0")
        self.score_card.grid(row=0, column=1, padx=(0, 12))
        secondary_button(top, "How to play", app.show_help, width=130, height=46).grid(row=0, column=2, padx=(0, 10))
        secondary_button(top, "Quit", app.quit_game, width=84, height=46).grid(row=0, column=3)

        # ---- centre: logo, cards, play button ---------------------------
        mid = tk.Frame(self, bg=BG)
        mid.grid(row=1, column=0, sticky="nsew", padx=40, pady=(0, 20))
        center = tk.Frame(mid, bg=BG)
        center.pack(expand=True, fill="x")

        ui.LogoCanvas(center, tile=62).pack()
        tk.Label(center, text="Guess the secret word before the rope runs out",
                 bg=BG, fg=INK_SOFT, font=ui.font(13)).pack(pady=(8, 22))
        tk.Label(center, text="CHOOSE A CATEGORY", bg=BG, fg=INK, font=ui.font(10, "bold")).pack(pady=(0, 10))

        grid = tk.Frame(center, bg=BG)
        grid.pack(fill="x")
        self.cards = []
        for i, cat in enumerate(CATEGORIES):
            grid.columnconfigure(i, weight=1, uniform="cards")
            card = ui.CategoryCard(grid, cat.key, cat.name, len(cat.word_list), i,
                                   on_select=app.select_category, on_play=app.start_from_card)
            card.grid(row=0, column=i, sticky="nsew", padx=8)
            self.cards.append(card)

        self.play_button = primary_button(center, "PLAY", app.start_game, width=340, height=62)
        self.play_button.pack(pady=(24, 6))
        tk.Label(center, text="Tip: press 1-4 to pick a category, Enter to play",
                 bg=BG, fg=INK_SOFT, font=ui.font(10)).pack()
        self.stats_label = tk.Label(center, text="", bg=BG, fg=INK_SOFT, font=ui.font(10, "bold"))
        self.stats_label.pack(pady=(6, 0))

    def refresh(self):
        s = self.app.session
        self.score_card.set(s.total_score)
        for i, card in enumerate(self.cards):
            card.set_selected(i == self.app.category_index)
        name = CATEGORIES[self.app.category_index].name.upper()
        self.play_button.set_text(f"PLAY  ·  {name}")
        self.stats_label.configure(
            text=f"Rounds played: {s.rounds_played}   ·   Wins: {s.wins}" if s.rounds_played else "")

    def on_key(self, event):
        if event.keysym in ("1", "2", "3", "4"):
            self.app.select_category(int(event.keysym) - 1)
        elif event.keysym == "Left":
            self.app.select_category((self.app.category_index - 1) % len(CATEGORIES))
        elif event.keysym == "Right":
            self.app.select_category((self.app.category_index + 1) % len(CATEGORIES))
        elif event.keysym in ("Return", "KP_Enter", "space"):
            self.app.start_game()


# ==========================================================================
# GAME SCREEN
# ==========================================================================
class GameScreen(tk.Frame):
    KEY_ROWS = ["ABCDEFG", "HIJKLMN", "OPQRSTU", "VWXYZ"]
    END_DELAY_WIN, END_DELAY_LOSE = 1000, 1500       # pause before the result screen

    def __init__(self, app):
        super().__init__(app, bg=BG)
        self.app = app
        self.keys = {}
        self.locked = False
        self._end_job = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ---- header -------------------------------------------------------
        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(18, 10))
        header.columnconfigure(2, weight=1)
        ui.LogoCanvas(header, tile=30).grid(row=0, column=0, padx=(0, 20))
        self.chip = ui.CategoryChip(header)
        self.chip.grid(row=0, column=1)
        secondary_button(header, "Skip word", self.skip_word, width=120, height=46).grid(row=0, column=3, padx=(0, 10))
        secondary_button(header, "Menu", self.go_menu, width=90, height=46).grid(row=0, column=4)

        # ---- body: hangman on the left, word + keyboard on the right ----------
        body = tk.Frame(self, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 22))
        body.columnconfigure(0, weight=4)
        body.columnconfigure(1, weight=6)
        body.rowconfigure(0, weight=1)

        left = Card(body, pad=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.hangman = ui.HangmanCanvas(left.inner, width=280, height=320)
        self.hangman.pack(fill="both", expand=True)
        self.mistakes_label = tk.Label(left.inner, text="", bg=CARD, fg=INK_SOFT, font=ui.font(11, "bold"))
        self.mistakes_label.pack(pady=(4, 2))

        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        # stats row: SCORE / ROUND / LIVES
        stats = tk.Frame(right, bg=BG)
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        stats.columnconfigure(2, weight=1)
        self.score_card = StatCard(stats, "SCORE", "0")
        self.score_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.round_card = StatCard(stats, "ROUND", "+0", value_color=TEAL)
        self.round_card.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        lives_card = Card(stats, radius=16, pad=10, stretch=False)
        lives_card.grid(row=0, column=2, sticky="nsew")
        tk.Label(lives_card.inner, text="LIVES", bg=CARD, fg=INK_SOFT, font=ui.font(8, "bold")).pack(anchor="w")
        self.lives = ui.LivesCanvas(lives_card.inner, maximum=MAX_WRONG, size=22)
        self.lives.pack(anchor="w", pady=(4, 0))

        # secret word card
        word_card = Card(right, pad=14)
        word_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.caption = tk.Label(word_card.inner, text="", bg=CARD, fg=INK_SOFT, font=ui.font(10, "bold"))
        self.caption.pack(pady=(2, 0))
        self.word = ui.WordDisplay(word_card.inner)
        self.word.pack(fill="x", expand=True)
        self.status = tk.Label(word_card.inner, text="", bg=CARD, fg=INK, font=ui.font(12, "bold"),
                               wraplength=520)
        self.status.pack(pady=(0, 4))

        # keyboard card
        kb_card = Card(right, pad=14)
        kb_card.grid(row=2, column=0, sticky="nsew")
        kb = kb_card.inner
        for c in range(7):
            kb.columnconfigure(c, weight=1, uniform="keys")
        for r, letters in enumerate(self.KEY_ROWS):
            kb.rowconfigure(r, weight=1)
            offset = (7 - len(letters)) // 2             # centre the short last row
            for c, letter in enumerate(letters):
                btn = RoundedButton(kb, letter, lambda L=letter: self.handle_letter(L),
                                    width=62, height=54, radius=12, bg=CARD, fill=WHITE,
                                    hover=TEAL_LIGHT, text_color=INK, border=CARD_BORDER,
                                    shadow=CARD_BORDER, font_spec=ui.font(-21, "bold"), depth=4)
                btn.grid(row=r, column=c + offset, sticky="nsew", padx=3, pady=2)
                self.keys[letter.lower()] = btn

    # ---- starting a round -------------------------------------------------
    def start_round(self):
        self._cancel_end_job()
        category = CATEGORIES[self.app.category_index]
        rnd = self.app.session.start_round(category)
        self.locked = False
        self.chip.set_category(category.key, category.name)
        self.hangman.set_stage(0)
        self.lives.set_lives(MAX_WRONG)
        self.word.set_word(rnd.answer, rnd.hint)
        letters = sum(ch.isalpha() for ch in rnd.answer)
        self.caption.configure(text=f"SECRET {ui.CATEGORY_SINGULAR[category.key].upper()}  ·  {letters} LETTERS")
        self.set_status("Pick a letter below, or just type it on your keyboard.", INK_SOFT)
        for btn in self.keys.values():
            btn.set_colors(fill=WHITE, hover=TEAL_LIGHT, text=INK, border=CARD_BORDER, shadow=CARD_BORDER)
            btn.set_enabled(True)
        self.refresh_stats()

    def refresh_stats(self):
        s, rnd = self.app.session, self.app.session.round
        self.score_card.set(s.total_score)
        self.round_card.set(f"+{rnd.round_score}")
        self.mistakes_label.configure(text=f"Mistakes: {rnd.wrong_guesses} / {MAX_WRONG}")

    def set_status(self, text, color=INK):
        self.status.configure(text=text, fg=color)

    # ---- guessing ---------------------------------------------------------
    def handle_letter(self, letter):
        if self.locked:
            return
        session = self.app.session
        rnd = session.round
        result = session.guess(letter)
        letter = letter.lower()
        key = self.keys.get(letter)

        if result.status == "repeat":
            self.set_status(f"You already tried '{letter.upper()}'.", INK_SOFT)
            return
        if result.status != "correct" and result.status != "wrong":
            return

        if result.status == "correct":
            key.set_colors(fill=TEAL, hover=TEAL, text=WHITE, border=TEAL_DARK, shadow=None)
            self.word.reveal(result.positions, rnd.hint, text=f"+{result.points}")
            times = len(result.positions)
            self.set_status(f"Nice! '{letter.upper()}' appears {times} time{'s' if times > 1 else ''}.", TEAL_DARK)
        else:
            key.set_colors(fill=CORAL_LIGHT, hover=CORAL_LIGHT, text=CORAL, border=CORAL_LIGHT, shadow=None)
            self.hangman.set_stage(rnd.wrong_guesses, flash=True)
            self.lives.set_lives(rnd.lives_left, flash=True)
            left = rnd.lives_left
            self.set_status(f"No '{letter.upper()}' here  ·  {left} {'life' if left == 1 else 'lives'} left.", CORAL)
        key.set_enabled(False)
        self.refresh_stats()

        if rnd.is_over:
            self.locked = True
            for btn in self.keys.values():
                btn.set_enabled(False)
            if rnd.is_won:
                self.set_status("You got it!", TEAL_DARK)
                delay = self.END_DELAY_WIN
            else:
                self.word.show_missing()
                self.set_status("Out of lives!", CORAL)
                delay = self.END_DELAY_LOSE
            self._end_job = self.after(delay, self.app.show_result)

    # ---- buttons ----------------------------------------------------------
    def _confirm_leave(self, question):
        rnd = self.app.session.round
        if rnd and not rnd.is_over and (rnd.round_score > 0 or rnd.wrong_guesses > 0):
            return messagebox.askyesno("Leave this round?", question + "\n\nPoints from this round won't be added to your total.")
        return True

    def skip_word(self):
        if self.locked or not self._confirm_leave("Skip this word and get a new one?"):
            return
        self.app.session.abandon_round()
        self.start_round()

    def go_menu(self):
        if self.locked:
            return
        if self._confirm_leave("Go back to the category screen?"):
            self.leave()
            self.app.go_home()

    def leave(self):
        self._cancel_end_job()
        if self.app.session.round and not self.app.session.round.is_over:
            self.app.session.abandon_round()

    def _cancel_end_job(self):
        if self._end_job:
            self.after_cancel(self._end_job)
            self._end_job = None

    # ---- physical keyboard --------------------------------------------------
    def on_key(self, event):
        if event.keysym == "Escape":
            self.go_menu()
        elif len(event.char) == 1 and event.char.isalpha() and event.char.isascii():
            self.handle_letter(event.char)


# ==========================================================================
# RESULT SCREEN (win + game over)
# ==========================================================================
class ResultScreen(tk.Frame):
    CONFETTI_COLORS = [TEAL, GOLD, CORAL, "#2F7FBF", "#D9628B", "#7BC4B8"]

    def __init__(self, app):
        super().__init__(app, bg=BG)
        self.app = app
        self.confetti = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.confetti.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.card = Card(self, pad=26, radius=30, stretch=False)
        self.card.place(relx=.5, rely=.5, anchor="center")
        self._particles = []
        self._confetti_job = None
        self._spawn_left = 0
        self._won = False

    # ---- build the card for the finished round -------------------------------
    def show_result(self):
        self.stop_confetti()
        session = self.app.session
        rnd = session.round
        self._won = rnd.is_won
        inner = self.card.inner
        for child in inner.winfo_children():
            child.destroy()
        inner.configure(width=1, height=1)

        accent = TEAL if rnd.is_won else CORAL
        title = "YOU WIN!" if rnd.is_won else "GAME OVER"
        tk.Label(inner, text=title, bg=CARD, fg=accent, font=ui.font(34, "bold", True)).pack(pady=(4, 0))
        tk.Label(inner, text="You saved the day!" if rnd.is_won else "Don't worry, the next word is yours.",
                 bg=CARD, fg=INK_SOFT, font=ui.font(12)).pack(pady=(0, 10))

        if rnd.is_won:
            word_canvas = ui.WordDisplay(inner)
            word_canvas.configure(width=460, height=90)
            word_canvas.pack(pady=(0, 6))
            word_canvas.set_word(rnd.answer, list(rnd.answer))
        else:
            tk.Label(inner, text="The word was", bg=CARD, fg=INK_SOFT, font=ui.font(10, "bold")).pack()
            tk.Label(inner, text=rnd.answer.upper(), bg=CARD, fg=INK, font=ui.font(26, "bold", True)).pack()
            figure = ui.HangmanCanvas(inner, width=150, height=170)
            figure.pack(pady=(4, 6))
            figure.set_stage(MAX_WRONG)

        # ---- score breakdown ----------------------------------------------------
        table = tk.Frame(inner, bg=CARD)
        table.pack(fill="x", padx=30, pady=(4, 0))
        table.columnconfigure(0, weight=1)
        rows = [(f"Correct guesses  ({rnd.correct_guess_count} × {POINTS_PER_CORRECT_GUESS})", rnd.guess_points)]
        if rnd.is_won:
            rows.append(("Win bonus", rnd.win_bonus))
            rows.append((f"Lives bonus  ({rnd.lives_left} × {BONUS_PER_LIFE_LEFT})", rnd.lives_bonus))
        for r, (label, value) in enumerate(rows):
            tk.Label(table, text=label, bg=CARD, fg=INK_SOFT, font=ui.font(12), anchor="w").grid(row=r, column=0, sticky="w", pady=2)
            tk.Label(table, text=f"+{value}", bg=CARD, fg=INK, font=ui.font(12, "bold")).grid(row=r, column=1, sticky="e", pady=2)
        r = len(rows)
        tk.Frame(table, bg=CARD_BORDER, height=2).grid(row=r, column=0, columnspan=2, sticky="ew", pady=6)
        tk.Label(table, text="Round score", bg=CARD, fg=INK, font=ui.font(13, "bold"), anchor="w").grid(row=r + 1, column=0, sticky="w")
        round_label = tk.Label(table, text="+0", bg=CARD, fg=accent, font=ui.font(15, "bold"))
        round_label.grid(row=r + 1, column=1, sticky="e")
        tk.Label(table, text="Total score", bg=CARD, fg=INK, font=ui.font(13, "bold"), anchor="w").grid(row=r + 2, column=0, sticky="w", pady=(6, 0))
        total_label = tk.Label(table, text=str(session.total_score - rnd.round_score), bg=CARD, fg=INK,
                               font=ui.font(22, "bold", True))
        total_label.grid(row=r + 2, column=1, sticky="e", pady=(6, 0))
        animate_number(round_label, 0, rnd.round_score, prefix="+")
        animate_number(total_label, session.total_score - rnd.round_score, session.total_score)

        # ---- buttons -----------------------------------------------------------------
        buttons = tk.Frame(inner, bg=CARD)
        buttons.pack(pady=(18, 4))
        if rnd.is_won:
            primary_button(buttons, "PLAY AGAIN", self.app.play_again, bg=CARD, width=190).grid(row=0, column=0, padx=6)
            secondary_button(buttons, "CHANGE CATEGORY", self.app.go_home, bg=CARD, width=220).grid(row=0, column=1, padx=6)
        else:
            primary_button(buttons, "TRY AGAIN", self.app.play_again, bg=CARD, width=150).grid(row=0, column=0, padx=5)
            secondary_button(buttons, "CHANGE CATEGORY", self.app.go_home, bg=CARD, width=210).grid(row=0, column=1, padx=5)
            danger_button(buttons, "QUIT", self.app.quit_game, bg=CARD, width=100).grid(row=0, column=2, padx=5)

        if rnd.is_won:
            self.after(150, self.start_confetti)

    # ---- confetti (win only) --------------------------------------------------------
    def start_confetti(self):
        self._spawn_left = 110
        self._tick_confetti()

    def stop_confetti(self):
        if self._confetti_job:
            self.after_cancel(self._confetti_job)
            self._confetti_job = None
        self.confetti.delete("all")
        self._particles.clear()
        self._spawn_left = 0

    def _tick_confetti(self):
        self._confetti_job = None
        try:
            w, h = self.confetti.winfo_width(), self.confetti.winfo_height()
            for _ in range(min(3, self._spawn_left)):
                self._spawn_left -= 1
                size = random.randint(7, 12)
                x, y = random.uniform(0, w), random.uniform(-40, -5)
                item = self.confetti.create_rectangle(x, y, x + size, y + size * .6, outline="",
                                                      fill=random.choice(self.CONFETTI_COLORS))
                self._particles.append([item, random.uniform(-1.2, 1.2), random.uniform(2.5, 5.5)])
            for p in list(self._particles):
                self.confetti.move(p[0], p[1] + math.sin(random.random() * 6) * .6, p[2])
                if self.confetti.coords(p[0])[1] > h + 20:
                    self.confetti.delete(p[0])
                    self._particles.remove(p)
            if self._spawn_left or self._particles:
                self._confetti_job = self.after(33, self._tick_confetti)
        except tk.TclError:
            pass

    # ---- keys ------------------------------------------------------------------------------
    def on_key(self, event):
        if event.keysym in ("Return", "KP_Enter", "space"):
            self.app.play_again()
        elif event.keysym == "Escape":
            self.app.go_home()


# ==========================================================================
# THE APPLICATION WINDOW
# ==========================================================================
class HangmanApp(tk.Tk):
    def __init__(self):
        super().__init__()
        ui.init_fonts(self)
        self.title("Hangman")
        self.configure(bg=BG)
        self.minsize(940, 700)
        self._center(1060, 760)

        self.session = GameSession()
        self.category_index = 0

        self.screens = {"home": HomeScreen(self), "game": GameScreen(self), "result": ResultScreen(self)}
        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.current = "home"
        self.bind("<Key>", self._on_key)
        self.protocol("WM_DELETE_WINDOW", self.quit_game)
        self.go_home()

    def _center(self, w, h):
        x = max(0, (self.winfo_screenwidth() - w) // 2)
        y = max(0, (self.winfo_screenheight() - h) // 3)
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ---- navigation ---------------------------------------------------------------------
    def show(self, name):
        self.current = name
        self.screens[name].tkraise()
        self.focus_set()

    def go_home(self):
        self.screens["result"].stop_confetti()
        self.screens["home"].refresh()
        self.show("home")

    def select_category(self, index):
        self.category_index = index
        self.screens["home"].refresh()

    def start_from_card(self, index):                 # double-click on a card
        self.category_index = index
        self.start_game()

    def start_game(self):
        self.screens["result"].stop_confetti()
        self.screens["game"].start_round()
        self.show("game")

    play_again = start_game                           # same category, new word

    def show_result(self):
        self.screens["result"].show_result()
        self.show("result")

    def show_help(self):
        messagebox.showinfo(
            "How to play",
            "1. Pick a category and press PLAY.\n"
            "2. Click letters on the keyboard (or type them) to guess the secret word.\n"
            "3. Every wrong guess adds a part to the hangman. You have 6 lives.\n\n"
            "Scoring\n"
            f"   +{POINTS_PER_CORRECT_GUESS} for every correct guess\n"
            f"   +{WIN_BONUS} bonus for winning\n"
            f"   +{BONUS_PER_LIFE_LEFT} bonus for every life you have left\n\n"
            "Shortcuts: 1-4 pick a category · Enter plays · Esc goes back")

    def quit_game(self):
        self.destroy()

    def _on_key(self, event):
        if event.state & 0x4:                          # ignore Ctrl+key
            return
        self.screens[self.current].on_key(event)


if __name__ == "__main__":
    HangmanApp().mainloop()
