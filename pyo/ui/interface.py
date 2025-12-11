"""Pygame drawing helpers for the piano display."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple, Literal

import pygame
from pyo.core.piano import Piano
from screeninfo import get_monitors

M_INFO = get_monitors()[0]

class PianoInterface:
    """Handle the visual representation of the keyboard + labels."""

    def __init__(
        self,
        piano: Piano,
        *,
        width: int | None = None,
        height: int | None = None,
        font_path: Path | None = None,
        title: str = "pyO Piano",
    ) -> None:
        self.piano = piano
        if not pygame.get_init():
            pygame.init()
        pygame.font.init()
        self.width = width or .9 * M_INFO.width
        self.height = height or .3 * M_INFO.height
        self.screen = pygame.display.set_mode((self.width, self.height))

        pygame.display.set_caption(title)
        self.font = self._load_font(font_path, 48)
        self.medium_font = self._load_font(font_path, 28)
        self.small_font = self._load_font(font_path, 16)
        self.tiny_font = self._load_font(font_path, 10)

    @property
    def KEYBOARD_TOP(self)->float:
        return self.height

    @property
    def KEY_WIDTH(self)->float:
        """
        Width of a white key (in pixels)

        Note
        ----
        This value is allways equal to the window size devided by the number of keys
        """
        return self.width // len(self.piano.white_notes)

    @property
    def KEYBOARD_WIDTH(self)->float:
        return self.KEY_WIDTH * len(self.piano.white_notes)

    #TODO measure real size and ratios
    @property
    def BKEY_WIDTH(self)->float:
        """
        Width of a black key (in pixels)

        Note
        ----
        Equal to ...
        """
        return .7 * self.KEY_WIDTH

    @property
    def KEY_HEIGHT(self)->float:
        """
        Height of a white key (in pixels)
        """
        return .9 * self.KEYBOARD_TOP

    @property
    def BKEY_HEIGHT(self)->float:
        """
        Height of a black key (in pixels)
        """
        return .7 * self.KEY_HEIGHT

    @property
    def BKEY_OFFSET(self)->float:
        return self.KEY_WIDTH - self.BKEY_WIDTH / 2

    def _load_font(self, font_path: Path | None, size: int) -> pygame.font.Font:
        if font_path is not None and font_path.exists():
            return pygame.font.Font(str(font_path), size)
        return pygame.font.SysFont("arial", size)

    def render_frame(self) -> Tuple[List[pygame.Rect], List[pygame.Rect]]:
        self.screen.fill("gray")
        white_rects, black_rects = self._draw_keyboard()
        self._draw_hand_guides()
        pygame.display.flip()
        return white_rects, black_rects

    def _draw_keyboard(self) -> Tuple[List[pygame.Rect], List[pygame.Rect]]:
        white_rects: List[pygame.Rect] = []
        for i in range(len(self.piano.white_notes)):
            _x = i * self.KEY_WIDTH
            _y = self.height - self.KEY_HEIGHT
            _dx = self.KEY_WIDTH
            _dy =  self.KEY_HEIGHT
            rect = pygame.draw.rect(
                self.screen,
                "white",
                [_x, _y , _dx, _dy],
                0,
                2,
            )
            white_rects.append(rect)
            pygame.draw.rect(
                self.screen,
                "black",
                [_x, _y , _dx, _dy],
                2,
                2,
            )

        #TODO add option to start from different keys, see if this should be specified here or in piano class
        black_rects: List[pygame.Rect] = []
        oct_count = 4
        for i in range(len(self.piano.white_notes)-1):
            oct_count = (oct_count + 1) % 7
            if oct_count not in [2, 6]:
                _x = self.BKEY_OFFSET + (i * self.KEY_WIDTH) #+ (skip_count * self.KEY_WIDTH)
                _y = self.height - self.KEY_HEIGHT
                _dx = self.BKEY_WIDTH
                _dy = self.BKEY_HEIGHT
                rect = pygame.draw.rect(
                    self.screen,
                    "black",
                    [_x, _y, _dx, _dy],
                    0,
                    2,
                )
                black_rects.append(rect)

        # Drawing the top part the piano
        top:pygame.Rect = pygame.draw.rect(
                self.screen,
                (50,50,50),
                [0, 0 , self.KEYBOARD_WIDTH, self.KEYBOARD_TOP - self.KEY_HEIGHT],
                0,
                2,
            )
        line:pygame.line = pygame.draw.line(
        self.screen,
        (220,0,0),
        (0, _y),
        (self.KEYBOARD_WIDTH, _y),
        2,
            )
        
        self._draw_highlights(white_rects, black_rects)
        return white_rects, black_rects

    def _add_key_labels(self):
        for i, note in enumerate(self.piano.white_notes[:3]):
            label = self.small_font.render(note, True, "black")
            self.screen.blit(label, (i * self.KEY_WIDTH + 3, self.height - 20))
        for i, label in enumerate(self.piano.black_labels[:1]):
            label_surface = self.tiny_font.render(label, True, "white")
            self.screen.blit(label_surface, (x + 2, self.height - 120))


    def _draw_highlights(self, white_rects: Sequence[pygame.Rect], black_rects: Sequence[pygame.Rect]) -> None:
        surviving_white = []
        for active in self.piano.active_whites:
            idx = active.index
            rect = pygame.Rect(idx * self.KEY_WIDTH, self.height - 100, self.KEY_WIDTH, 100)
            pygame.draw.rect(self.screen, "green", rect, 2, 2)
            if active.decay():
                surviving_white.append(active)
        self.piano.active_whites = surviving_white

        surviving_black = []
        for active in self.piano.active_blacks:
            idx = active.index
            if 0 <= idx < len(black_rects):
                pygame.draw.rect(self.screen, "green", black_rects[idx], 2, 2)
            if active.decay():
                surviving_black.append(active)
        self.piano.active_blacks = surviving_black

    def _draw_hand_guides(self) -> None:
        self._draw_hand_panel(self.piano.left_oct, self.piano.left_hand_labels, _which="left")
        self._draw_hand_panel(self.piano.right_oct, self.piano.right_hand_labels, _which="right")

    def _draw_hand_panel(self, octave: int, labels: Sequence[str], _which:Literal["left", "right"]) -> None:

        panel_dx = 7 * self.KEY_WIDTH
        # Fist octave (oct0) starts at 5th note
        x_offset = -5 * self.KEY_WIDTH

        panel_x = (octave * panel_dx) + x_offset
        panel_y = .95 * self.height

        color = (220,0,0)
        face = self.screen

        pygame.draw.line(
        face,
        color,
        (max(0, panel_x), panel_y),
        (min(self.KEYBOARD_WIDTH, panel_x+panel_dx), panel_y),
        2,
            )

        dy_head = 0.01*self.height
        if _which == "left":
            x_head = max(0, panel_x)
            y_head = panel_y
            dx_head = 0.01*self.width
        else:
            x_head = min(self.KEYBOARD_WIDTH, panel_x+panel_dx)
            y_head = panel_y
            dx_head = -0.01*self.width

        p_head = [
            (x_head, y_head),
            (x_head+dx_head, y_head+dy_head/2),
            (x_head+dx_head, y_head-dy_head/2)
        ]
        dx_head = 0.01*self.width

        pygame.draw.polygon(
        face,
        color,
        p_head,
        2,
            )
