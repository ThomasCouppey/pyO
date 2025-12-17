"""Pygame drawing helpers for the piano display."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import pygame
from screeninfo import get_monitors

from pyo.core._keyboard import Keyboard

M_INFO = get_monitors()[0]


class MIDI:
    """Handle the visual representation of the keyboard + labels."""

    def __init__(
        self,
        piano: Keyboard,
        *,
        width: int | None = None,
        height: int | None = None,
        font_path: Path | None = None,
        title: str = "pyO Keyboard",
    ):
        self.piano = piano
        if not pygame.get_init():
            pygame.init()
        pygame.font.init()
        self.width = width or 0.9 * M_INFO.width
        self.height = height or 0.3 * M_INFO.height
        self.screen = pygame.display.set_mode((self.width, self.height))

        pygame.display.set_caption(title)
        self.font = self._load_font(font_path, 48)
        self.medium_font = self._load_font(font_path, 28)
        self.small_font = self._load_font(font_path, 16)
        self.tiny_font = self._load_font(font_path, 10)

    @property
    def keyboard_top(self) -> float:
        return self.height

    @property
    def key_width(self) -> float:
        """
        Width of a white key (in pixels)

        Note
        ----
        This value is allways equal to the window size devided by the number of keys
        """
        return self.width // len(self.piano.white_notes)

    @property
    def keyboard_width(self) -> float:
        return self.key_width * len(self.piano.white_notes)

    # TODO measure real size and ratios
    @property
    def bkey_width(self) -> float:
        """
        Width of a black key (in pixels)

        Note
        ----
        Equal to ...
        """
        return 0.7 * self.key_width

    @property
    def key_height(self) -> float:
        """
        Height of a white key (in pixels)
        """
        return 0.9 * self.keyboard_top

    @property
    def bkey_height(self) -> float:
        """
        Height of a black key (in pixels)
        """
        return 0.7 * self.key_height

    @property
    def bkey_offset(self) -> float:
        return self.key_width - self.bkey_width / 2

    def _load_font(self, font_path: Path | None, size: int) -> pygame.font.Font:
        if font_path is not None and font_path.exists():
            return pygame.font.Font(str(font_path), size)
        return pygame.font.SysFont("arial", size)

    def render_frame(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        self.screen.fill("gray")
        white_rects, black_rects = self._draw_keyboard()
        self._draw_hand_guides()
        pygame.display.flip()
        return white_rects, black_rects

    def _draw_keyboard(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        white_rects: list[pygame.Rect] = []
        for i in range(len(self.piano.white_notes)):
            _x = i * self.key_width
            _y = self.height - self.key_height
            _dx = self.key_width
            _dy = self.key_height
            rect = pygame.draw.rect(
                self.screen,
                "white",
                [_x, _y, _dx, _dy],
                0,
                2,
            )
            white_rects.append(rect)
            pygame.draw.rect(
                self.screen,
                "black",
                [_x, _y, _dx, _dy],
                2,
                2,
            )

        # TODO add option to start from different keys, see if this should be specified here or in
        # piano class
        black_rects: list[pygame.Rect] = []
        oct_count = 4
        for i in range(self.piano.n_white_keys):
            oct_count = (oct_count + 1) % 7
            if oct_count not in [2, 6]:
                _x = self.bkey_offset + (i * self.key_width)  # + (skip_count * self.key_width)
                _y = self.height - self.key_height
                _dx = self.bkey_width
                _dy = self.bkey_height
                rect = pygame.draw.rect(
                    self.screen,
                    "black",
                    [_x, _y, _dx, _dy],
                    0,
                    2,
                )
                black_rects.append(rect)
        self._draw_highlights(white_rects, black_rects)

        # Drawing the top part the piano
        pygame.draw.rect(
            self.screen,
            (50, 50, 50),
            [0, 0, self.keyboard_width, self.keyboard_top - self.key_height],
            0,
            2,
        )
        pygame.draw.line(
            self.screen,
            (220, 0, 0),
            (0, _y),
            (self.keyboard_width, _y),
            2,
        )

        return white_rects, black_rects

    def _add_key_labels(self):
        for i, note in enumerate(self.piano.white_notes[:3]):
            label = self.small_font.render(note, True, "black")
            self.screen.blit(label, (i * self.key_width + 3, self.height - 20))
        for i, label in enumerate(self.piano.black_labels[:1]):
            _x = self.bkey_offset + (i * self.key_width)  # + (skip_count * self.key_width)
            label_surface = self.tiny_font.render(label, True, "white")
            self.screen.blit(label_surface, (_x + 2, self.height - 120))

    def _draw_highlights(
        self, white_rects: Sequence[pygame.Rect], black_rects: Sequence[pygame.Rect]
    ):
        for _i_active in self.piano.active_keys.index:
            is_black, _idx = self.piano.get_color(_i_active)
            if not is_black:
                _rect = white_rects[_idx]
            else:
                _rect = black_rects[_idx]
            pygame.draw.rect(self.screen, (40, 40, 40, 240), _rect, 0, 2)

        self.piano.decay()

    def _draw_hand_guides(self):
        self._draw_hand_panel(self.piano.left_oct, self.piano.left_hand_labels, _which="left")
        self._draw_hand_panel(self.piano.right_oct, self.piano.right_hand_labels, _which="right")

    def _draw_hand_panel(
        self, octave: int, labels: Sequence[str], _which: Literal["left", "right"]
    ):

        panel_dx = 7 * self.key_width
        # Fist octave (oct0) starts at 5th note
        x_offset = -5 * self.key_width

        panel_x = (octave * panel_dx) + x_offset
        panel_y = 0.95 * self.height

        color = (220, 0, 0)
        face = self.screen

        pygame.draw.line(
            face,
            color,
            (max(0, panel_x), panel_y),
            (min(self.keyboard_width, panel_x + panel_dx), panel_y),
            2,
        )

        dy_head = 0.01 * self.height
        if _which == "left":
            x_head = max(0, panel_x)
            y_head = panel_y
            dx_head = 0.01 * self.width
        else:
            x_head = min(self.keyboard_width, panel_x + panel_dx)
            y_head = panel_y
            dx_head = -0.01 * self.width

        p_head = [
            (x_head, y_head),
            (x_head + dx_head, y_head + dy_head / 2),
            (x_head + dx_head, y_head - dy_head / 2),
        ]
        dx_head = 0.01 * self.width

        pygame.draw.polygon(
            face,
            color,
            p_head,
            2,
        )
