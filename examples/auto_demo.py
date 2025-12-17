"""Minimal example launching the interactive piano display."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from pyo.ui import PyoApp, MIDI
from pyo.core import Keyboard

if __name__ == "__main__":
    piano = Keyboard()
    print(piano.asset_root)
    interface = MIDI(piano)
    app = PyoApp(piano, interface)
    app.display()
