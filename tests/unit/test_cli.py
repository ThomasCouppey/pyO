from pyo import __version__


def test_import():
    import pyo

    assert __version__ == pyo.__version__


def test_version_string():
    assert isinstance(__version__, str)


if __name__ == "__main__":
    test_import()
    test_version_string()
