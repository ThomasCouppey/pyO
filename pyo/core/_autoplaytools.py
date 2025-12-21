from __future__ import annotations

import os

from pandas import DataFrame, concat
from pathlib import Path


lib_path = Path(os.path.dirname(__file__)).parent.absolute()


class AutoPlayTools:
    COLUMNS = {
        "note": str,
        "duration": int,
        "start": int,
    }

    def __init__(self, playrate: float = 1.0):
        self.playrate = playrate
        self.notes: DataFrame = DataFrame(columns=self.COLUMNS.keys()).astype(self.COLUMNS)

        self.playtime: int = 0

    @property
    def n_notes(self) -> int:
        return len(self.notes)

    @property
    def notes_start(self) -> DataFrame:
        _start = self.playrate * self.notes["start"]
        return _start.round()

    @property
    def notes_duration(self) -> DataFrame:
        _duration = self.playrate * self.notes["duration"]
        return _duration.round().astype(dtype=int)

    def add_note(self, data: list | dict):
        """Append a single note entry to the DataFrame.

        Parameters
        ----------
        data : list or dict
            Row describing the key. When passing a list, the order must match
            :attr:`COLUMNS`.
        """
        self.notes.loc[self.n_notes] = data

    def add_keys(self, data: AutoPlayTools | DataFrame | dict):
        """Append multiple notes at once.

        Parameters
        ----------
        data : Keys or pandas.DataFrame or dict
            Source structure describing the notes to append. ``Keys`` instances
            contribute their DataFrame, dictionaries are converted to a
            DataFrame with matching columns.
        """
        if isinstance(data, AutoPlayTools):
            pd_data = data.notes
        elif isinstance(data, DataFrame):
            pd_data = data
        else:
            pd_data = DataFrame(data)
        self.notes = concat([self.notes, pd_data], ignore_index=True)

    # Play related method
    def set_playrate(self, playrate: float):
        self.playrate = playrate

    def update_time(self):
        self.playtime += 1

    def reset_time(self, value: int = 0):
        self.playtime = value

    @property
    def to_press(self) -> DataFrame:
        return self.notes_start == self.playtime


class Music(AutoPlayTools):
    def __init__(self, playrate=1, duration=None, data=None):
        super().__init__(playrate)
        self.duration = None

    def build_music(self, data):
        pass

    def __build_music_from_json(self, data: str):
        pass

    def save(self, fname):
        print(fname)
        pass
