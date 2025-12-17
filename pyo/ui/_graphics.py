"""Graphics helpers for the MIDI interface."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

import pygame

if TYPE_CHECKING:
    from pyo.ui._midi import MIDI


class MIDIGraphicsTemplate:
    """Template used to implement different graphic setups for the MIDI view."""

    def __init__(self) -> None:
        self._midi: MIDI | None = None

    def attach(self, midi: MIDI) -> None:
        """Bind the graphics helper to a ``MIDI`` instance."""
        self._midi = midi

    @property
    def midi(self) -> MIDI:
        if self._midi is None:
            msg = "MIDIGraphicsTemplate.attach must be called before drawing."
            raise RuntimeError(msg)
        return self._midi

    def render_frame(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        raise NotImplementedError

    def draw_keyboard(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        raise NotImplementedError

    def add_key_labels(self) -> None:
        raise NotImplementedError

    def draw_highlights(
        self, white_rects: Sequence[pygame.Rect], black_rects: Sequence[pygame.Rect]
    ) -> None:
        raise NotImplementedError

    def draw_hand_guides(self) -> None:
        raise NotImplementedError

    def draw_hand_panel(
        self,
        octave: int,
        labels: Sequence[str],
        which: Literal["left", "right"],
    ) -> None:
        raise NotImplementedError


class DefaultMIDIGraphics(MIDIGraphicsTemplate):
    """Current pygame based drawing implementation."""

    def render_frame(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        midi = self.midi
        midi.screen.fill("gray")
        white_rects, black_rects = self.draw_keyboard()
        self.draw_hand_guides()
        pygame.display.flip()
        return white_rects, black_rects

    def draw_keyboard(self) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
        midi = self.midi
        white_rects: list[pygame.Rect] = []
        for i in range(len(midi.piano.white_notes)):
            _x = i * midi.key_width
            _y = midi.height - midi.key_height
            _dx = midi.key_width
            _dy = midi.key_height
            rect = pygame.draw.rect(
                midi.screen,
                "white",
                [_x, _y, _dx, _dy],
                0,
                2,
            )
            white_rects.append(rect)
            pygame.draw.rect(
                midi.screen,
                "black",
                [_x, _y, _dx, _dy],
                2,
                2,
            )

        black_rects: list[pygame.Rect] = []
        oct_count = 4
        for i in range(midi.piano.n_white_keys):
            oct_count = (oct_count + 1) % 7
            if oct_count not in [2, 6]:
                _x = midi.bkey_offset + (i * midi.key_width)
                _y = midi.height - midi.key_height
                _dx = midi.bkey_width
                _dy = midi.bkey_height
                rect = pygame.draw.rect(
                    midi.screen,
                    "black",
                    [_x, _y, _dx, _dy],
                    0,
                    2,
                )
                black_rects.append(rect)

        self.draw_highlights(white_rects, black_rects)

        pygame.draw.rect(
            midi.screen,
            (50, 50, 50),
            [0, 0, midi.keyboard_width, midi.keyboard_top - midi.key_height],
            0,
            2,
        )
        pygame.draw.line(
            midi.screen,
            (220, 0, 0),
            (0, midi.height - midi.key_height),
            (midi.keyboard_width, midi.height - midi.key_height),
            2,
        )

        return white_rects, black_rects

    def add_key_labels(self) -> None:
        midi = self.midi
        for i, note in enumerate(midi.piano.white_notes[:3]):
            label = midi.small_font.render(note, True, "black")
            midi.screen.blit(label, (i * midi.key_width + 3, midi.height - 20))
        for i, label in enumerate(midi.piano.black_labels[:1]):
            _x = midi.bkey_offset + (i * midi.key_width)
            label_surface = midi.tiny_font.render(label, True, "white")
            midi.screen.blit(label_surface, (_x + 2, midi.height - 120))

    def draw_highlights(
        self, white_rects: Sequence[pygame.Rect], black_rects: Sequence[pygame.Rect]
    ) -> None:
        midi = self.midi
        for active_idx in midi.piano.active_keys.index:
            is_black, idx = midi.piano.get_color(active_idx)
            if not is_black:
                rect = white_rects[idx]
            else:
                rect = black_rects[idx]
            pygame.draw.rect(midi.screen, (40, 40, 40, 240), rect, 0, 2)

        midi.piano.decay()

    def draw_hand_guides(self) -> None:
        midi = self.midi
        self.draw_hand_panel(midi.piano.left_oct, midi.piano.left_hand_labels, "left")
        self.draw_hand_panel(midi.piano.right_oct, midi.piano.right_hand_labels, "right")

    def draw_hand_panel(
        self,
        octave: int,
        labels: Sequence[str],
        which: Literal["left", "right"],
    ) -> None:
        midi = self.midi
        panel_dx = 7 * midi.key_width
        x_offset = -5 * midi.key_width

        panel_x = (octave * panel_dx) + x_offset
        panel_y = 0.95 * midi.height

        color = (220, 0, 0)
        face = midi.screen

        pygame.draw.line(
            face,
            color,
            (max(0, panel_x), panel_y),
            (min(midi.keyboard_width, panel_x + panel_dx), panel_y),
            2,
        )

        dy_head = 0.01 * midi.height
        if which == "left":
            x_head = max(0, panel_x)
            y_head = panel_y
            dx_head = 0.01 * midi.width
        else:
            x_head = min(midi.keyboard_width, panel_x + panel_dx)
            y_head = panel_y
            dx_head = -0.01 * midi.width

        p_head = [
            (x_head, y_head),
            (x_head + dx_head, y_head + dy_head / 2),
            (x_head + dx_head, y_head - dy_head / 2),
        ]

        pygame.draw.polygon(
            face,
            color,
            p_head,
            2,
        )
