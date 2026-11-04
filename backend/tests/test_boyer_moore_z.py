import random

from app.algorithms.boyer_moore import boyer_moore_search
from app.algorithms.z_algorithm import z_search


def _reference(text, pattern):
    matches = []
    if not pattern:
        return matches
    start = text.find(pattern)
    while start != -1:
        matches.append(start)
        start = text.find(pattern, start + 1)
    return matches


def test_boyer_moore_and_z_match_reference_for_random_inputs():
    rng = random.Random(516)
    for _ in range(200):
        text = "".join(rng.choice("ACGT") for _ in range(rng.randrange(0, 60)))
        pattern = "".join(rng.choice("ACGT") for _ in range(rng.randrange(0, 14)))
        expected = _reference(text, pattern)
        assert boyer_moore_search(text, pattern)[0] == expected
        assert z_search(text, pattern)[0] == expected


def test_new_search_algorithms_find_overlaps():
    assert boyer_moore_search("AAAA", "AA")[0] == [0, 1, 2]
    assert z_search("AAAA", "AA")[0] == [0, 1, 2]


def test_z_pattern_array_example():
    assert z_search("ACACAGT", "ACACAGT")[2] == [7, 0, 3, 0, 1, 0, 0]
