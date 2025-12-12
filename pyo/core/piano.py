"""Pygame-backed piano model that wraps samples and keyboard mappings."""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import pygame
from pygame import mixer

lib_path = Path(os.path.dirname(__file__)).parent.absolute()

@dataclass
class ActiveKey:
    """Track highlight duration for pressed keys."""

    index: int
    frames_remaining: int

    def decay(self) -> bool:
        """Decrease the counter and report whether the key should stay highlighted."""
        self.frames_remaining -= 1
        return self.frames_remaining > 0


class Octave:
    """
    Iterative class
    """

    W_NOTES: Sequence[str] = ("C", "D", "E", "F", "A", "B")
    B_NOTES: Sequence[str] = ("C", "D", "E", "F", "A", "B")


class Piano:
    """Store piano state, play samples, and expose keyboard mappings."""

    WHITE_NOTES: Sequence[str] = (
        "A0",
        "B0",
        "C1",
        "D1",
        "E1",
        "F1",
        "G1",
        "A1",
        "B1",
        "C2",
        "D2",
        "E2",
        "F2",
        "G2",
        "A2",
        "B2",
        "C3",
        "D3",
        "E3",
        "F3",
        "G3",
        "A3",
        "B3",
        "C4",
        "D4",
        "E4",
        "F4",
        "G4",
        "A4",
        "B4",
        "C5",
        "D5",
        "E5",
        "F5",
        "G5",
        "A5",
        "B5",
        "C6",
        "D6",
        "E6",
        "F6",
        "G6",
        "A6",
        "B6",
        "C7",
        "D7",
        "E7",
        "F7",
        "G7",
        "A7",
        "B7",
        "C8",
    )
    BLACK_NOTES: Sequence[str] = (
        "Bb0",
        "Db1",
        "Eb1",
        "Gb1",
        "Ab1",
        "Bb1",
        "Db2",
        "Eb2",
        "Gb2",
        "Ab2",
        "Bb2",
        "Db3",
        "Eb3",
        "Gb3",
        "Ab3",
        "Bb3",
        "Db4",
        "Eb4",
        "Gb4",
        "Ab4",
        "Bb4",
        "Db5",
        "Eb5",
        "Gb5",
        "Ab5",
        "Bb5",
        "Db6",
        "Eb6",
        "Gb6",
        "Ab6",
        "Bb6",
        "Db7",
        "Eb7",
        "Gb7",
        "Ab7",
        "Bb7",
    )
    BLACK_LABELS: Sequence[str] = (
        "A#0",
        "C#1",
        "D#1",
        "F#1",
        "G#1",
        "A#1",
        "C#2",
        "D#2",
        "F#2",
        "G#2",
        "A#2",
        "C#3",
        "D#3",
        "F#3",
        "G#3",
        "A#3",
        "C#4",
        "D#4",
        "F#4",
        "G#4",
        "A#4",
        "C#5",
        "D#5",
        "F#5",
        "G#5",
        "A#5",
        "C#6",
        "D#6",
        "F#6",
        "G#6",
        "A#6",
        "C#7",
        "D#7",
        "F#7",
        "G#7",
        "A#7",
    )
    LEFT_HAND_LABELS: Sequence[str] = ("Z", "S", "X", "D", "C", "V", "G", "B", "H", "N", "J", "M")
    RIGHT_HAND_LABELS: Sequence[str] = ("R", "5", "T", "6", "Y", "U", "8", "I", "9", "O", "0", "P")
    RIGHT_TEMPLATE: Sequence[tuple[str, str]] = (
        ("R", "C"),
        ("5", "C#"),
        ("T", "D"),
        ("6", "D#"),
        ("Y", "E"),
        ("U", "F"),
        ("8", "F#"),
        ("I", "G"),
        ("9", "G#"),
        ("O", "A"),
        ("0", "A#"),
        ("P", "B"),
    )
    LEFT_TEMPLATE: Sequence[tuple[str, str]] = (
        ("W", "C"),
        ("S", "C#"),
        ("X", "D"),
        ("D", "D#"),
        ("C", "E"),
        ("V", "F"),
        ("G", "F#"),
        ("B", "G"),
        ("H", "G#"),
        ("N", "A"),
        ("J", "A#"),
        (",", "B"),
    )

    def __init__(
        self,
        asset_root: Path | None = None,
        sample_pack: str = "lemastertech",
        left_oct: int = 3,
        right_oct: int = 5,
        highlight_frames: int = 30,
        mixer_channels: int = 50,
    ) -> None:
        if asset_root is None:
            self.asset_root = lib_path / "_misc"
        else:
            self.asset_root = Path(asset_root)
        self.sample_pack = sample_pack
        self.left_oct = self._clamp_octave(left_oct)
        self.right_oct = self._clamp_octave(right_oct)
        self.highlight_frames = highlight_frames
        self._ensure_audio_ready(mixer_channels)
        self.white_sounds = self._load_sounds(self.WHITE_NOTES)
        self.black_sounds = self._load_sounds(self.BLACK_NOTES)
        self.active_whites: list[ActiveKey] = []
        self.active_blacks: list[ActiveKey] = []

    @staticmethod
    def _clamp_octave(value: int) -> int:
        return max(0, min(8, value))

    def _ensure_audio_ready(self, channels: int) -> None:
        if not pygame.get_init():
            pygame.init()
        if not mixer.get_init():
            mixer.init()
        mixer.set_num_channels(channels)

    def _load_sounds(self, notes: Iterable[str]) -> list[mixer.Sound]:
        sounds: list[mixer.Sound] = []
        sample_root = self.asset_root / "notes" / self.sample_pack
        for note in notes:
            wav_path = sample_root / f"{note}.wav"
            if not wav_path.exists():
                raise FileNotFoundError(f"Sample {wav_path} not found")
            sounds.append(mixer.Sound(str(wav_path)))
        return sounds

    @property
    def n_white_notes(self) -> Sequence[str]:
        return len(self.WHITE_NOTES)

    @property
    def n_black_notes(self) -> Sequence[str]:
        return len(self.BLACK_NOTES)

    @property
    def white_notes(self) -> Sequence[str]:
        return self.WHITE_NOTES

    @property
    def black_labels(self) -> Sequence[str]:
        return self.BLACK_LABELS

    @property
    def left_hand_labels(self) -> Sequence[str]:
        return self.LEFT_HAND_LABELS

    @property
    def right_hand_labels(self) -> Sequence[str]:
        return self.RIGHT_HAND_LABELS

    def build_left_mapping(self) -> dict[str, str]:
        return self._build_mapping(self.LEFT_TEMPLATE, self.left_oct)

    def build_right_mapping(self) -> dict[str, str]:
        return self._build_mapping(self.RIGHT_TEMPLATE, self.right_oct)

    @staticmethod
    def _build_mapping(template: Sequence[tuple[str, str]], octave: int) -> dict[str, str]:
        return {key: f"{note}{octave}" for key, note in template}

    def handle_text_input(self, text: str) -> bool:
        if not text:
            return False
        key = text.upper()
        for mapping in (self.build_left_mapping(), self.build_right_mapping()):
            if key in mapping:
                self.play_note_label(mapping[key])
                return True
        return False

    def play_note_label(self, label: str) -> None:
        if "#" in label:
            index = self.BLACK_LABELS.index(label)
            self._play_black_index(index)
        else:
            index = self.WHITE_NOTES.index(label)
            self._play_white_index(index)

    def _play_white_index(self, index: int) -> None:
        self.white_sounds[index].play(0, 1000)
        self.active_whites.append(ActiveKey(index=index, frames_remaining=self.highlight_frames))

    def _play_black_index(self, index: int) -> None:
        self.black_sounds[index].play(0, 1000)
        self.active_blacks.append(ActiveKey(index=index, frames_remaining=self.highlight_frames))

    def handle_mouse_white(self, index: int) -> None:
        if 0 <= index < len(self.WHITE_NOTES):
            self._play_white_index(index)

    def handle_mouse_black(self, index: int) -> None:
        if 0 <= index < len(self.BLACK_LABELS):
            self._play_black_index(index)

    def shift_left_octave(self, delta: int) -> None:
        self.left_oct = self._clamp_octave(self.left_oct + delta)

    def shift_right_octave(self, delta: int) -> None:
        self.right_oct = self._clamp_octave(self.right_oct + delta)
