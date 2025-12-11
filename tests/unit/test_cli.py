from pyo import __version__
from pyo.cli import build_parser


def test_parser_has_run_command():
    parser = build_parser()
    commands = parser._subparsers._group_actions[0].choices  # type: ignore[attr-defined]
    assert "run" in commands


def test_version_string():
    assert isinstance(__version__, str)
