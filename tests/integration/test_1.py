"""Minimal example launching the interactive piano display."""

from pyo.core._pyoapp import PyoApp
from pyo.core.piano import Piano
from pyo.ui.interface import PianoInterface

if __name__ == "__main__":
    piano = Piano()
    interface = PianoInterface(piano)
    app = PyoApp(piano, interface)
    app.display()