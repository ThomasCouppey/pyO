"""Core piano primitives built on pygame samples and keyboard mappings."""

from __future__ import annotations

import os
import numpy as np
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pygame
from pygame import mixer
from pandas import DataFrame, Series, concat

lib_path = Path(os.path.dirname(__file__)).parent.absolute()

LEFT_HAND_LABELS: Sequence[str] = (
    "w",
    "s",
    "x",
    "d",
    "c",
    "v",
    "g",
    "b",
    "h",
    "n",
    "j",
    ",",
)
RIGHT_HAND_LABELS: Sequence[str] = ("r", "(", "t", "§", "y", "u", "!", "i", "ç", "o", "à", "p")


class Keys:
    """Track the state of keys that compose a piano keyboard.

    Notes are backed by a :class:`pandas.DataFrame` so that higher level
    components can efficiently derive slices (white keys vs black keys) and
    keep track of the number of frames a key should remain highlighted.

    Attributes
    ----------
    keys : pandas.DataFrame
        Table storing ``note``, ``label``, ``is_black_key`` and the remaining
        ``n_active_frames`` for each key.
    """

    COLUMNS = {
        "note": str,
        "label": str,
        "is_black_key": bool,
        "n_active_frames": int,
    }

    def __init__(self):
        """Initialize the empty DataFrame that stores the key metadata.

        Returns
        -------
        None
            The constructor only sets internal state.
        """
        self.keys: DataFrame = DataFrame(columns=self.COLUMNS.keys()).astype(self.COLUMNS)

    @property
    def n_keys(self) -> int:
        """
        Returns
        -------
        int
            Total number of keys currently registered on the keyboard.
        """
        return len(self.keys)

    @property
    def n_white_keys(self) -> int:
        """
        Returns
        -------
        int
            Number of keys marked as white in the DataFrame.
        """
        return len(self.keys[~self.keys["is_black_key"]])

    @property
    def n_black_keys(self) -> int:
        """
        Returns
        -------
        int
            Number of keys marked as black in the DataFrame.
        """
        return len(self.keys[self.keys["is_black_key"]])

    @property
    def white_keys(self) -> DataFrame:
        """
        Returns
        -------
        pandas.DataFrame
            View containing rows that represent white keys only.
        """
        return self.keys[~self.keys["is_black_key"]]

    @property
    def black_keys(self) -> DataFrame:
        """
        Returns
        -------
        pandas.DataFrame
            View containing rows that represent black keys only.
        """
        return self.keys[self.keys["is_black_key"]]

    @property
    def is_active_keys(self):
        """
        Returns
        -------
        pandas.Series
            Boolean mask that identifies the keys whose highlight counter is
            strictly positive.
        """
        return self.keys["n_active_frames"] > 0

    @property
    def active_keys(self):
        """
        Returns
        -------
        pandas.DataFrame
            Slice of :attr:`keys` that only contains the active keys.
        """
        return self.keys[self.is_active_keys]

    def add_key(self, data: list | dict):
        """Append a single key entry to the DataFrame.

        Parameters
        ----------
        data : list or dict
            Row describing the key. When passing a list, the order must match
            :attr:`COLUMNS`.
        """
        self.keys.loc[self.n_keys] = data

    def add_keys(self, data: Keys | DataFrame | dict):
        """Append multiple keys at once.

        Parameters
        ----------
        data : Keys or pandas.DataFrame or dict
            Source structure describing the keys to append. ``Keys`` instances
            contribute their DataFrame, dictionaries are converted to a
            DataFrame with matching columns.
        """
        if isinstance(data, Keys):
            pd_data = data.keys
        elif isinstance(data, DataFrame):
            pd_data = data
        else:
            pd_data = DataFrame(data)
        self.keys = concat([self.keys, pd_data], ignore_index=True)

    def press_key(self, index: int | list[int], duration: int = 100):
        """Mark key indices as active for the requested number of frames.

        Parameters
        ----------
        index : int or list of int
            Row index or indices to highlight.
        duration : int, default=100
            Number of frames the key should remain highlighted.
        """
        self.keys.at[index, "n_active_frames"] = duration

    def decay(self) -> bool:
        """Decrease highlight counters for one frame.

        Returns
        -------
        bool
            ``True`` if at least one key remains active after decrementing,
            ``False`` otherwise.
        """
        self.keys["n_active_frames"] -= self.is_active_keys.astype(dtype=int)
        return self.is_active_keys.sum() > 0


@dataclass
class Octave(Keys):
    """Represent a contiguous subset of notes that belong to one octave.

    An :class:`Octave` materializes white and black keys sequentially starting
    from the requested note. Instances are later concatenated to form the full
    keyboard layout.
    """

    W_NOTES: Sequence[str] = ("C", "D", "E", "F", "G", "A", "B")
    B_NOTES: Sequence[str] = ("C", "D", "F", "G", "A")

    def __init__(
        self,
        oct_id: int = 0,
        start: int | Literal["C", "D", "E", "F", "G", "A", "B"] = 0,
        n_keys_max: int = 12,
    ):
        """Create a new octave and populate keys immediately.

        Parameters
        ----------
        oct_id : int, default=0
            Identifier appended to generated notes and labels (e.g. ``C4``).
        start : int or {\"C\",\"D\",\"E\",\"F\",\"G\",\"A\",\"B\"}, default=0
            Starting note within :attr:`W_NOTES`. When a string is supplied it
            is converted to the matching index.
        n_keys_max : int, default=12
            Maximum number of keys to materialize for the octave.
        """
        super().__init__()
        self._id = oct_id
        self.n_keys_max = n_keys_max
        if isinstance(start, str):
            self.start = self.W_NOTES.index(start)
        else:
            self.start = start
        self.__build_keys()

    def __build_keys(self):
        """Populate the internal DataFrame with white and black keys.

        Returns
        -------
        None
            The method mutates :attr:`keys` in-place.
        """
        _i_key = self.start
        while _i_key < len(self.W_NOTES) and self.n_keys < self.n_keys_max:
            _note = self.W_NOTES[_i_key]
            self.add_key([f"{_note}{self._id}", f"{_note}{self._id}", False, 0])
            if _note in self.B_NOTES and self.n_keys < self.n_keys_max:
                _note_b = self.W_NOTES[(_i_key + 1) % len(self.W_NOTES)]
                self.add_key([f"{_note_b}b{self._id}", f"{_note}#{self._id}", True, 0])
            _i_key += 1

    def _build_mapping(self, template: Sequence[tuple[str, str]]) -> dict[str, str]:
        """Build a mapping of keyboard glyphs to note labels for an octave.

        Parameters
        ----------
        template : Sequence[str]
            Template containing pairs of glyph and note name without octave.
        octave : int
            Octave index appended to each note in the resulting mapping.

        Returns
        -------
        dict[str, str]
            Mapping ready to be consumed by the text input handler.
        """
        return {
            template[self.start + _i_key].lower(): self.keys.at[_i_key, "label"]
            for _i_key in range(self.n_keys)
        }


class Keyboard(Keys):
    """Store piano state, play samples, and expose keyboard mappings.

    The keyboard is composed by aggregating :class:`Octave` instances. Each
    note is associated with a pygame ``mixer.Sound`` so the class can respond
    to UI actions (mouse or text input) while highlighting pressed keys.
    """

    def __init__(
        self,
        asset_root: Path | None = None,
        sample_pack: str = "lemastertech",
        left_oct: int = 3,
        right_oct: int = 5,
        highlight_frames: int = 30,
        mixer_channels: int = 50,
    ) -> None:
        """Instantiate the keyboard and load the requested samples.

        Parameters
        ----------
        asset_root : pathlib.Path, optional
            Directory that contains the ``notes`` hierarchy; defaults to the
            package ``_misc`` folder.
        sample_pack : str, default=\"lemastertech\"
            Name of the directory inside ``notes`` that holds the WAV files.
        left_oct : int, default=3
            Octave index used as base for the left-hand keyboard mapping.
        right_oct : int, default=5
            Octave index used as base for the right-hand keyboard mapping.
        highlight_frames : int, default=30
            Number of frames a pressed key should remain highlighted.
        mixer_channels : int, default=50
            Number of pygame mixer channels to allocate.
        """
        super().__init__()

        if asset_root is None:
            self.asset_root = lib_path / "_misc"
        else:
            self.asset_root = Path(asset_root)
        self.sample_pack = sample_pack
        self.oct_list: list[Octave] = []
        self.__build_keys()

        self.left_oct = self._clamp_octave(left_oct)
        self.right_oct = self._clamp_octave(right_oct)
        self.highlight_frames = highlight_frames
        self._ensure_audio_ready(mixer_channels)
        self.white_sounds = self._load_sounds(self.white_notes)
        self.black_sounds = self._load_sounds(self.black_notes)

    def __build_keys(self):
        """Create the sequence of octaves that compose the keyboard layout.

        Returns
        -------
        None
            The method extends :attr:`oct_list` and :attr:`keys`.
        """
        self.oct_list += [Octave(oct_id=0, start="A")]
        self.add_keys(self.oct_list[-1])
        for i in range(1, 8):
            self.oct_list += [Octave(oct_id=i)]
            self.add_keys(self.oct_list[-1])

        self.oct_list += [Octave(oct_id=8, n_keys_max=88 - self.n_keys)]
        self.add_keys(self.oct_list[-1])

    @staticmethod
    def _clamp_octave(value: int) -> int:
        """Clamp octave index to the supported piano range [0, 8].

        Parameters
        ----------
        value : int
            Octave index to clamp.

        Returns
        -------
        int
            Clamped octave value constrained to ``[0, 8]``.
        """
        return max(0, min(8, value))

    def _ensure_audio_ready(self, channels: int) -> None:
        """Initialize pygame/mixer if needed and set the channel count.

        Parameters
        ----------
        channels : int
            Number of mixer channels to allocate.
        """
        if not pygame.get_init():
            pygame.init()
        if not mixer.get_init():
            mixer.init()
        mixer.set_num_channels(channels)

    def _load_sounds(self, notes: Iterable[str]) -> list[mixer.Sound]:
        """Read WAV samples for the given note names.

        Parameters
        ----------
        notes : Iterable[str]
            Sequence of note names (e.g. ``[\"C4\", \"D4\"]``) that should be
            loaded.

        Returns
        -------
        list of pygame.mixer.Sound
            Mixer objects ready to be triggered in sync with the note order.
        """
        sounds: list[mixer.Sound] = []
        sample_root = self.asset_root / "notes" / self.sample_pack
        for note in notes:
            wav_path = sample_root / f"{note}.wav"
            if not wav_path.exists():
                raise FileNotFoundError(f"Sample {wav_path} not found")
            sounds.append(mixer.Sound(str(wav_path)))
        return sounds

    @property
    def white_notes(self) -> Series[str]:
        """
        Returns
        -------
        pandas.Series
            Names of the white notes in keyboard order.
        """
        return self.white_keys["note"]

    @property
    def black_notes(self) -> Series[str]:
        """
        Returns
        -------
        pandas.Series
            Names of the black notes in keyboard order.
        """
        return self.black_keys["note"]

    @property
    def black_labels(self) -> Series[str]:
        """
        Returns
        -------
        pandas.Series
            Display labels for black keys.
        """
        return self.black_keys["label"]

    @property
    def left_hand_labels(self) -> Sequence[str]:
        """
        Returns
        -------
        Sequence[str]
            Default key labels assigned to the left hand.
        """
        return LEFT_HAND_LABELS

    @property
    def right_hand_labels(self) -> Sequence[str]:
        """
        Returns
        -------
        Sequence[str]
            Default key labels assigned to the right hand.
        """
        return RIGHT_HAND_LABELS

    def get_color(self, index: int, with_color_index: bool = True) -> int:
        """Return key type and index within its color group.

        Parameters
        ----------
        index : int
            Global key index (row in :attr:`keys`).
        with_color_index : bool, default=True
            ``True`` to also compute the index among keys of the same color.

        Returns
        -------
        bool or tuple
            If ``with_color_index`` is ``False`` a boolean indicating whether
            the key is black is returned. Otherwise the result is a tuple
            ``(is_black, color_index)`` where ``color_index`` counts keys of
            the same color that precede the requested index.
        """
        _is_black = self.keys["is_black_key"].to_numpy(dtype=bool)
        _index_is_black = _is_black[index]
        if not with_color_index:
            return _index_is_black
        if _index_is_black:
            _color_index = np.sum(_is_black[:index])
        else:
            _color_index = np.sum(~_is_black[:index])
        return _index_is_black, _color_index

    @property
    def left_mapping(self) -> dict[str, str]:
        """
        Returns
        -------
        dict[str, str]
            Mapping of keyboard glyphs to note labels for the left hand.
        """
        return self.oct_list[self.left_oct]._build_mapping(LEFT_HAND_LABELS)

    @property
    def right_mapping(self) -> dict[str, str]:
        """
        Returns
        -------
        dict[str, str]
            Mapping of keyboard glyphs to note labels for the right hand.
        """
        return self.oct_list[self.right_oct]._build_mapping(RIGHT_HAND_LABELS)

    def handle_text_input(self, text: str) -> bool:
        """Interpret direct text input as a piano key press.

        Parameters
        ----------
        text : str
            Text emitted by the UI system.

        Returns
        -------
        bool
            ``True`` when the text matched a mapping and a note was played,
            ``False`` otherwise.
        """
        if not text:
            return False
        key = text.lower()
        print(key)
        for mapping in (self.left_mapping, self.right_mapping):
            if key in mapping:
                self.play_note_label(mapping[key])
                return True
        return False

    def play_note_label(self, label: str) -> None:
        """Trigger playback for the given note label.

        Parameters
        ----------
        label : str
            Label that uniquely identifies the target note (e.g. ``\"C4\"``).
        """
        if "#" in label:
            index = self.black_labels.to_list().index(label)
            self._play_black_index(index)
        else:
            index = self.white_notes.to_list().index(label)
            self._play_white_index(index)

    def _play_white_index(self, index: int) -> None:
        """Play the Nth white-key sound and highlight the associated key.

        Parameters
        ----------
        index : int
            Position within :meth:`white_notes`.
        """
        self.white_sounds[index].play(0, 1000)
        w_idx = self.keys[~self.keys["is_black_key"]].iloc[index].name.astype(int)
        self.press_key(index=w_idx, duration=self.highlight_frames)

    def _play_black_index(self, index: int) -> None:
        """Play the Nth black-key sound and highlight the associated key.

        Parameters
        ----------
        index : int
            Position within :meth:`black_labels`.
        """
        self.black_sounds[index].play(0, 1000)
        b_idx = self.keys[self.keys["is_black_key"]].iloc[index].name.astype(int)
        self.press_key(index=b_idx, duration=self.highlight_frames)

    def handle_mouse_white(self, index: int) -> None:
        """Handle clicks on white keys by triggering the appropriate note.

        Parameters
        ----------
        index : int
            Index of the clicked white key.
        """
        if 0 <= index < len(self.white_notes):
            self._play_white_index(index)

    def handle_mouse_black(self, index: int) -> None:
        """Handle clicks on black keys by triggering the appropriate note.

        Parameters
        ----------
        index : int
            Index of the clicked black key.
        """
        if 0 <= index < len(self.black_labels):
            self._play_black_index(index)

    def shift_left_octave(self, delta: int) -> None:
        """Adjust left-hand octave while clamping to the allowed range.

        Parameters
        ----------
        delta : int
            Octave delta applied to :attr:`left_oct`.
        """
        self.left_oct = self._clamp_octave(self.left_oct + delta)

    def shift_right_octave(self, delta: int) -> None:
        """Adjust right-hand octave while clamping to the allowed range.

        Parameters
        ----------
        delta : int
            Octave delta applied to :attr:`right_oct`.
        """
        self.right_oct = self._clamp_octave(self.right_oct + delta)
