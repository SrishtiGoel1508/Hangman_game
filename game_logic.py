"""
game_logic.py
=============
Pure game rules for Hangman - NO GUI code lives here.

Everything in this file comes straight from your original terminal game:
  * 6 wrong guesses allowed
  * +5 points for every correct guess
  * +20 win bonus
  * +10 bonus for every life left when you win
  * "_" for hidden letters, spaces (e.g. "south africa") shown from the start

The GUI (main.py) only *calls* these classes, so the rules can be tested
or changed without touching any drawing code.
"""

import random
from dataclasses import dataclass
from typing import List, Optional, Set

from wordslist import words, fruits, flowers, countries

# --------------------------------------------------------------------------
# Constants (same values as the original game)
# --------------------------------------------------------------------------
MAX_WRONG = 6                    # wrong guesses allowed
POINTS_PER_CORRECT_GUESS = 5
WIN_BONUS = 20
BONUS_PER_LIFE_LEFT = 10


@dataclass(frozen=True)
class Category:
    key: str            # "animals", "flowers", ... (also used to pick the icon)
    name: str           # label shown on screen
    word_list: tuple    # the words from wordslist.py


# Order = order of the cards on the home screen.
CATEGORIES = [
    Category("animals", "Animals", words),
    Category("flowers", "Flowers", flowers),
    Category("fruits", "Fruits", fruits),
    Category("countries", "Countries", countries),
]


# --------------------------------------------------------------------------
# Result of a single guess
# --------------------------------------------------------------------------
@dataclass
class GuessResult:
    status: str                       # "correct" | "wrong" | "repeat" | "invalid"
    letter: str = ""
    positions: Optional[List[int]] = None   # where the letter appears in the word
    points: int = 0                   # points earned by this guess (+5 or 0)


# --------------------------------------------------------------------------
# One round of Hangman
# --------------------------------------------------------------------------
class HangmanRound:
    """One word, from the first guess until win or lose."""

    def __init__(self, category: Category, answer: str):
        self.category = category
        self.answer = answer.strip().lower()
        # Letters hidden as "_", everything else (spaces) shown
        self.hint: List[str] = ["_" if ch.isalpha() else ch for ch in self.answer]
        self.guessed: Set[str] = set()
        self.correct_letters: Set[str] = set()
        self.wrong_letters: List[str] = []       # in the order they were guessed
        self.correct_guess_count = 0

    # ----- state ---------------------------------------------------------
    @property
    def wrong_guesses(self) -> int:
        return len(self.wrong_letters)

    @property
    def lives_left(self) -> int:
        return MAX_WRONG - self.wrong_guesses

    @property
    def is_won(self) -> bool:
        return "_" not in self.hint

    @property
    def is_lost(self) -> bool:
        return self.wrong_guesses >= MAX_WRONG and not self.is_won

    @property
    def is_over(self) -> bool:
        return self.is_won or self.is_lost

    # ----- scoring -------------------------------------------------------
    @property
    def guess_points(self) -> int:
        return self.correct_guess_count * POINTS_PER_CORRECT_GUESS

    @property
    def win_bonus(self) -> int:
        return WIN_BONUS if self.is_won else 0

    @property
    def lives_bonus(self) -> int:
        return self.lives_left * BONUS_PER_LIFE_LEFT if self.is_won else 0

    @property
    def round_score(self) -> int:
        return self.guess_points + self.win_bonus + self.lives_bonus

    # ----- action --------------------------------------------------------
    def guess(self, letter: str) -> GuessResult:
        letter = (letter or "").strip().lower()
        if self.is_over or len(letter) != 1 or not letter.isalpha():
            return GuessResult("invalid", letter)
        if letter in self.guessed:
            return GuessResult("repeat", letter)

        self.guessed.add(letter)
        if letter in self.answer:
            positions = [i for i, ch in enumerate(self.answer) if ch == letter]
            for i in positions:
                self.hint[i] = letter
            self.correct_letters.add(letter)
            self.correct_guess_count += 1
            return GuessResult("correct", letter, positions, POINTS_PER_CORRECT_GUESS)

        self.wrong_letters.append(letter)
        return GuessResult("wrong", letter, [], 0)


# --------------------------------------------------------------------------
# A whole play session (many rounds, running total)
# --------------------------------------------------------------------------
class GameSession:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.total_score = 0
        self.rounds_played = 0
        self.wins = 0
        self.round: Optional[HangmanRound] = None
        self._bags = {}            # category key -> words not used yet
        self._last_word = {}       # category key -> last word served
        self._banked = False

    def _next_word(self, category: Category) -> str:
        """Random word, but never the same word twice before the list is used up."""
        bag = self._bags.get(category.key)
        if not bag:
            bag = list(category.word_list)
            self.rng.shuffle(bag)
            last = self._last_word.get(category.key)
            if len(bag) > 1 and bag[-1] == last:      # avoid an instant repeat
                bag[0], bag[-1] = bag[-1], bag[0]
            self._bags[category.key] = bag
        word = bag.pop()
        self._last_word[category.key] = word
        return word

    def start_round(self, category: Category) -> HangmanRound:
        self.round = HangmanRound(category, self._next_word(category))
        self._banked = False
        return self.round

    def guess(self, letter: str) -> GuessResult:
        result = self.round.guess(letter)
        if self.round.is_over and not self._banked:
            self._bank_round()
        return result

    def _bank_round(self) -> None:
        """Add the finished round to the total (same as the original game)."""
        self.total_score += self.round.round_score
        self.rounds_played += 1
        if self.round.is_won:
            self.wins += 1
        self._banked = True

    def abandon_round(self) -> None:
        """Leaving a round early: its points are NOT added to the total."""
        self._banked = True
        self.round = None
