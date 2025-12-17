"""Minimal example launching the interactive piano display."""

from pyo.ui._pyoapp import PyoApp
from pyo.core._keyboard import Keyboard
from pyo.ui._midi import MIDI

if __name__ == "__main__":
    piano = Keyboard()
    interface = MIDI(piano)
    app = PyoApp(piano, interface)
    app.display()
