"""Pygame-backed rendering helpers for the on-screen piano keyboard."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import pygame
from screeninfo import get_monitors

from pyo.core._keyboard import Keyboard

M_INFO = get_monitors()[0]

key_colors = {
    "black": {"0": "black", "1": (0, 100, 0)},
    "white": {"0": "white", "1": (0, 255, 0)},
}


class MIDI:
    """Render the visual representation of the keyboard and helper overlays."""

    def __init__(
        self,
        piano: Keyboard,
        *,
        width: int | None = None,
        height: int | None = None,
        font_path: Path | None = None,
        title: str = "pyO Keyboard",
    ):
        """Create a new renderer bound to a :class:`~pyo.core._keyboard.Keyboard`.

        Parameters
        ----------
        piano : Keyboard
            Keyboard instance that provides notes, labels, and active state.
        width : int, optional
            Window width in pixels; defaults to 90% of the primary monitor width.
        height : int, optional
            Window height in pixels; defaults to 30% of the primary monitor height.
        font_path : pathlib.Path, optional
            Custom font to use when drawing labels; falls back to Arial when not
            supplied or missing.
        title : str, default=\"pyO Keyboard\"
            Caption set on the pygame display surface.
        """
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
        """
        Returns
        -------
        float
            Pixel coordinate of the bottom of the drawable area.
        """
        return self.height

    @property
    def key_width(self) -> float:
        """
        Width of a white key in pixels.

        Note
        ----
        This value always equals the window width divided by the number of white keys.
        """
        return self.width // len(self.piano.white_notes)

    @property
    def keyboard_width(self) -> float:
        """
        Returns
        -------
        float
            Total width occupied by the keyboard portion of the window.
        """
        return self.key_width * len(self.piano.white_notes)

    # TODO measure real size and ratios
    @property
    def bkey_width(self) -> float:
        """
        Width of a black key in pixels.

        Note
        ----
        Approximated at 70% of a white key width.
        """
        return 0.7 * self.key_width

    @property
    def key_height(self) -> float:
        """
        Returns
        -------
        float
            Height of a white key in pixels.
        """
        return 0.9 * self.keyboard_top

    @property
    def bkey_height(self) -> float:
        """
        Returns
        -------
        float
            Height of a black key in pixels.
        """
        return 0.7 * self.key_height

    @property
    def bkey_offset(self) -> float:
        """
        Returns
        -------
        float
            Horizontal offset to position a black key relative to the preceding white key.
        """
        return self.key_width - self.bkey_width / 2

    def _load_font(self, font_path: Path | None, size: int) -> pygame.font.Font:
        """Load a font from disk or fall back to the system default.

        Parameters
        ----------
        font_path : pathlib.Path, optional
            Path to the TTF file; ignored when missing or ``None``.
        size : int
            Font size in points.

        Returns
        -------
        pygame.font.Font
            Loaded font ready for rendering text surfaces.
        """
        if font_path is not None and font_path.exists():
            return pygame.font.Font(str(font_path), size)
        return pygame.font.SysFont("arial", size)

    def render_frame(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        """Draw a full frame including keyboard and helper overlays.

        Returns
        -------
        tuple[list[pygame.Rect], list[pygame.Rect]]
            Rectangles corresponding to white and black keys, respectively.
        """
        self.screen.fill("gray")
        white_rects, black_rects = self._draw_keyboard()
        self._draw_hand_guides()
        pygame.display.flip()
        return white_rects, black_rects

    def _draw_keyboard(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        """Render all keys, highlights, and top bar.

        Returns
        -------
        tuple[list[pygame.Rect], list[pygame.Rect]]
            Rectangles for white keys and black keys.
        """
        white_rects: list[pygame.Rect] = []
        black_rects: list[pygame.Rect] = []
        _is_black: bool = False
        for _i_key in range(self.piano.n_keys):
            if not _is_black:
                white_rects, black_rects, _is_black = self._draw_key(
                    _i_key,
                    white_rects,
                    black_rects,
                )
            else:
                _is_black = False
        self._draw_top()
        self.piano.decay()
        return white_rects, black_rects

    def _draw_key(
        self,
        kindex: int,
        white_rects: tuple[list[pygame.Rect]],
        black_rects: tuple[list[pygame.Rect]],
    ) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        """Draw an individual key and return updated rectangles.

        Parameters
        ----------
        kindex : int
            Index of the key to render within :attr:`piano.keys`.
        white_rects : tuple[list[pygame.Rect]]
            Accumulator for white key rectangles (order is preserved).
        black_rects : tuple[list[pygame.Rect]]
            Accumulator for black key rectangles (order is preserved).

        Returns
        -------
        tuple[list[pygame.Rect], list[pygame.Rect]]
            Updated accumulators reflecting the newly drawn key.
        """
        _key = self.piano.keys.iloc[kindex]
        _is_active = (_key["n_active_frames"] > 0).astype(int)
        _color_kindex = len(white_rects)

        if _key["is_black_key"]:
            #! Not ideal: draw following white to impose all black notes in front
            white_rects, black_rects, _ = self._draw_key(kindex + 1, white_rects, black_rects)
            #! ---
            _x = self.bkey_offset + ((_color_kindex - 1) * self.key_width)
            _y = self.height - self.key_height
            _dx = self.bkey_width
            _dy = self.bkey_height
            _color = key_colors["black"][str(_is_active)]
        else:
            _x = _color_kindex * self.key_width
            _y = self.height - self.key_height
            _dx = self.key_width
            _dy = self.key_height
            _color = key_colors["white"][str(_is_active)]

        rect = pygame.draw.rect(
            self.screen,
            _color,
            [_x, _y, _dx, _dy],
            0,
            2,
        )
        pygame.draw.rect(
            self.screen,
            "black",
            [_x, _y, _dx, _dy],
            2,
            2,
        )

        if _key["is_black_key"]:
            return white_rects, black_rects + [rect], True
        else:
            return white_rects + [rect], black_rects, False

    def _draw_top(self):
        """Draw the top bar that caps the keyboard body."""
        # Drawing the top part the piano
        _y = self.height - self.key_height
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

    def _add_key_labels(self):
        """Render small note labels on a subset of keys."""
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
        """Shade active keys based on the keyboard state.

        Parameters
        ----------
        white_rects : Sequence[pygame.Rect]
            Rectangles representing the white keys.
        black_rects : Sequence[pygame.Rect]
            Rectangles representing the black keys.
        """
        for _i_active in self.piano.active_keys.index:
            is_black, _idx = self.piano.get_color(_i_active)
            if not is_black:
                _rect = white_rects[_idx]
            else:
                _rect = black_rects[_idx]
            pygame.draw.rect(self.screen, (40, 40, 40, 240), _rect, 0, 2)

        self.piano.decay()

    def _draw_hand_guides(self):
        """Draw visual guides showing the active left/right hand octaves."""
        self._draw_hand_panel(self.piano.left_oct, self.piano.left_hand_labels, _which="left")
        self._draw_hand_panel(self.piano.right_oct, self.piano.right_hand_labels, _which="right")

    def _draw_hand_panel(
        self, octave: int, labels: Sequence[str], _which: Literal["left", "right"]
    ):
        """Render an octave guide panel for one hand.

        Parameters
        ----------
        octave : int
            Octave index to highlight.
        labels : Sequence[str]
            Labels (keyboard glyphs) mapped to notes for the chosen hand.
        _which : {\"left\", \"right\"}
            Indicates which hand panel is drawn; influences arrow direction.
        """

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
