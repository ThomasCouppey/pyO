"""Minimal example launching the interactive piano display."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from pyo.core._pyoapp import PyoApp
from pyo.core.piano import Piano
from pyo.ui import PianoInterface

if __name__ == "__main__":
    piano = Piano()
    print(piano.asset_root)
    interface = PianoInterface(piano)
    app = PyoApp(piano, interface)
    app.display()
