"""pyo - Numerical piano with didactic overlays."""

from importlib import metadata

try:
    __version__ = metadata.version("pyo")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"


from .core._PyoApp import *
from .core.piano import *
from .ui.interface import *

__all__ = ["__version__"]
