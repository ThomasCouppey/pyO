"""Event loop that connects the piano model with the pygame interface."""

from __future__ import annotations

import pygame

from pyo.core._keyboard import Keyboard
from pyo.ui._midi import MIDI


class PyoApp:
    """Combine Keyboard + MIDI and drive the event loop."""

    def __init__(self, piano: Keyboard, interface: MIDI, fps: int = 60):
        self.piano = piano
        self.interface = interface
        self.clock = pygame.time.Clock()
        self.fps = fps
        pygame.key.start_text_input()

    def display(self):
        """Start the blocking display loop."""
        running = True
        while running:
            self.clock.tick(self.fps)
            white_rects, black_rects = self.interface.render_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse(event.pos, white_rects, black_rects)
                elif event.type == pygame.TEXTINPUT:
                    self.piano.handle_text_input(event.text)
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)
        pygame.quit()

    def _handle_mouse(self, position, white_rects, black_rects):
        for i, rect in enumerate(black_rects):
            if rect.collidepoint(position):
                self.piano.handle_mouse_black(i)
                return
        for i, rect in enumerate(white_rects):
            if rect.collidepoint(position):
                self.piano.handle_mouse_white(i)
                return

    def _handle_keydown(self, key: int):
        if key == pygame.K_RIGHT:
            self.piano.shift_right_octave(1)
        elif key == pygame.K_LEFT:
            self.piano.shift_right_octave(-1)
        elif key == pygame.K_UP:
            self.piano.shift_left_octave(1)
        elif key == pygame.K_DOWN:
            self.piano.shift_left_octave(-1)
