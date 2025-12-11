from pyo import __version__
from pyo.cli import build_parser


def test_version_string():
    assert isinstance(__version__, str)


if __name__ == "__main__":
    test_version_string()
