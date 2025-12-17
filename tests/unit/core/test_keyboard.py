from pandas import DataFrame

from pyo.core import Keys, _keyboard as kb


def test_initial_state():
    k = Keys()
    # empty on init
    assert k.n_keys == 0
    # expected columns present
    expected_cols = {"note", "label", "is_black_key", "n_active_frames"}
    assert set(k.keys.columns) == expected_cols
    # no white or black keys
    assert k.n_white_keys == 0
    assert k.n_black_keys == 0


def test_add_key_and_counts():
    k = Keys()
    # add a white key and a black key
    k.add_key(["C4", "C4", False, 0])
    k.add_key(["Db4", "C#4", True, 0])
    assert k.n_keys == 2
    assert k.n_white_keys == 1
    assert k.n_black_keys == 1

    k2 = Keys()
    k2.add_keys(
        {
            "note": ["D4", "Db4"],
            "label": ["D4", "D#4"],
            "is_black_key": [False, True],
            "n_active_frames": [0, 0],
        }
    )
    assert k2.n_keys == 2
    assert k2.n_white_keys == 1
    assert k2.n_black_keys == 1

    k.add_keys(k2)
    # print(k.keys)


def test_decay_decrements_and_returns():
    k = Keys()
    k.add_key(["C4", "C4", False, 0])
    k.press_key(0, duration=2)
    # first decay: should decrement from 2 -> 1 and report still active
    ret1 = k.decay()
    assert int(k.keys.loc[0, "n_active_frames"]) == 1
    assert bool(ret1) is True
    # second decay: should decrement from 1 -> 0 and report no longer active
    ret2 = k.decay()
    assert int(k.keys.loc[0, "n_active_frames"]) == 0
    assert bool(ret2) is False


def test_octave_creation():
    o1 = kb.Octave()
    assert o1.W_NOTES == ("C", "D", "E", "F", "G", "A", "B")
    assert o1.n_keys == 12
    assert o1.n_white_keys == 7
    assert o1.n_black_keys == 5

    assert isinstance(o1.keys, DataFrame)
    # print(o1.keys, o1.n_keys, o1.n_white_keys)

    o2 = kb.Octave(start=6, oct_id=1)
    # assert o2.n_keys == 1
    # assert o2.n_white_keys == 1
    # assert o2.n_black_keys == 0

    print(o2.keys, o2.n_keys, o2.n_white_keys)

    o3 = kb.Octave(n_keys_max=3, oct_id=2)
    # assert o3.n_keys == 3
    # assert o3.n_white_keys == 2
    # assert o3.n_black_keys == 1
    # print(o3.keys, o3.n_keys, o3.n_white_keys)

    print(o1._build_mapping(kb.LEFT_HAND_LABELS))
    print(o1._build_mapping(kb.RIGHT_HAND_LABELS))
    print(o2._build_mapping(kb.LEFT_HAND_LABELS))
    print(o3._build_mapping(kb.LEFT_HAND_LABELS))


def test_instantiate_keyboard():
    p = kb.Keyboard()

    print(p.keys)
    p.press_key(3, 100)
    p.press_key(15, 100)


if __name__ == "__main__":
    # test_initial_state()
    # test_add_key_and_counts()
    # test_decay_decrements_and_returns()
    test_octave_creation()
    # test_instantiate_keyboard()
