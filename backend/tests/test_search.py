import random

from app.algorithms.kmp import build_lps, kmp_search
from app.algorithms.naive import naive_search
from app.algorithms.rabin_karp import rabin_karp_search


def _reference(text, pattern):
    matches = []
    if not pattern:
        return matches
    start = text.find(pattern)
    while start != -1:
        matches.append(start)
        start = text.find(pattern, start + 1)
    return matches


def test_search_algorithms_match_reference_for_random_inputs():
    rng = random.Random(42)
    for _ in range(200):
        text = "".join(rng.choice("ACGT") for _ in range(rng.randrange(0, 50)))
        pattern = "".join(rng.choice("ACGT") for _ in range(rng.randrange(0, 12)))
        expected = _reference(text, pattern)
        assert naive_search(text, pattern)[0] == expected
        assert kmp_search(text, pattern)[0] == expected
        assert rabin_karp_search(text, pattern)[0] == expected


def test_search_edge_cases_and_overlaps():
    assert naive_search("", "A")[0] == []
    assert kmp_search("ACGT", "")[0] == []
    assert rabin_karp_search("AC", "ACG")[0] == []
    assert naive_search("AAAA", "AA")[0] == [0, 1, 2]
    assert kmp_search("AAAA", "AA")[0] == [0, 1, 2]
    assert rabin_karp_search("AAAA", "AA")[0] == [0, 1, 2]


def test_kmp_lps_example():
    assert build_lps("ACACAGT") == [0, 0, 1, 2, 3, 0, 0]
