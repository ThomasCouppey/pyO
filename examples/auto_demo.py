"""Minimal example launching the interactive piano display."""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from pyo.core._PyoApp import PyoApp
from pyo.core.piano import Piano
from pyo.ui.interface import PianoInterface


if __name__ == "__main__":
    asset_root = PROJECT_ROOT / "pyo" / "_misc"
    piano = Piano(asset_root=asset_root)
    interface = PianoInterface(piano)
    app = PyoApp(piano, interface)
    app.display()
