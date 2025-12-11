"""Command line entry points for pyo."""
from __future__ import annotations

import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyo",
        description="Numerical piano playground (manual + automatic).",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=Path(__file__).resolve().parent / "_misc",
        help="Path to piano assets (samples, fonts).",
    )
    parser.add_argument(
        "--sample-pack",
        default="lemastertech",
        help="Folder within the assets/notes directory that contains WAV files.",
    )
    parser.add_argument("--left-oct", type=int, default=3, help="Starting octave for the left hand.")
    parser.add_argument("--right-oct", type=int, default=5, help="Starting octave for the right hand.")
    parser.add_argument("--fps", type=int, default=60, help="Target refresh rate for the display.")
    sub = parser.add_subparsers(dest="command", required=False)
    sub.add_parser("run", help="Start the interactive piano display")
    return parser


def app(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command not in (None, "run"):
        parser.error(f"Unknown command: {args.command}")

    from pyO.pyo.core._PyoApp import PianoApp
    from pyo.core.piano import Piano
    from pyo.ui.interface import PianoInterface

    piano = Piano(
        asset_root=args.assets,
        sample_pack=args.sample_pack,
        left_oct=args.left_oct,
        right_oct=args.right_oct,
    )
    interface = PianoInterface(piano)
    PianoApp(piano, interface, fps=args.fps).display()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(app())
