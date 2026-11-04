import random

from app.algorithms.alignment import global_align
from app.algorithms.hirschberg import hirschberg_align


def _rescore(result, match, mismatch, gap):
    score = 0
    for a, b in zip(result["aligned_a"], result["aligned_b"]):
        if a == "-" or b == "-":
            score -= gap
        else:
            score += match if a == b else mismatch
    return score


def test_hirschberg_agrees_with_full_alignment_on_100_random_pairs():
    rng = random.Random(1606)
    for _ in range(100):
        a = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 20)))
        b = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 20)))
        match, mismatch, gap = rng.randint(1, 3), rng.randint(-3, -1), rng.randint(1, 3)
        full = global_align(a, b, match, mismatch, gap, gap)
        linear = hirschberg_align(a, b, match, mismatch, gap)
        assert linear["score"] == full["score"]
        assert linear["score"] == _rescore(linear, match, mismatch, gap)
        assert len(linear["aligned_a"]) == len(linear["aligned_b"])
        assert linear["aligned_a"].replace("-", "") == a
        assert linear["aligned_b"].replace("-", "") == b


def test_hirschberg_handles_empty_side():
    result = hirschberg_align("", "ACG", 2, -1, 2)
    assert result["aligned_a"] == "---"
    assert result["aligned_b"] == "ACG"
    assert result["score"] == -6
