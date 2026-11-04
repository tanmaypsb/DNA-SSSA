import random

import pytest
from fastapi.testclient import TestClient

from app.algorithms.alignment import global_align, local_align
from app.main import app

client = TestClient(app)


def _linear_score(a, b, match, mismatch, gap):
    previous = [-gap * j for j in range(len(b) + 1)]
    for i, char_a in enumerate(a, 1):
        current = [-gap * i]
        for j, char_b in enumerate(b, 1):
            current.append(max(
                previous[j - 1] + (match if char_a == char_b else mismatch),
                previous[j] - gap,
                current[j - 1] - gap,
            ))
        previous = current
    return previous[-1]


def _rescore(result, match, mismatch, gap_open, gap_extend):
    score = 0
    gap_side = None
    gap_length = 0
    for char_a, char_b in zip(result["aligned_a"], result["aligned_b"]):
        side = "a" if char_a == "-" else "b" if char_b == "-" else None
        if side:
            if side != gap_side:
                if gap_length:
                    score -= gap_open + (gap_length - 1) * gap_extend
                gap_side, gap_length = side, 0
            gap_length += 1
        else:
            if gap_length:
                score -= gap_open + (gap_length - 1) * gap_extend
                gap_side, gap_length = None, 0
            score += match if char_a == char_b else mismatch
    if gap_length:
        score -= gap_open + (gap_length - 1) * gap_extend
    return score


def test_global_linear_case_matches_independent_dynamic_program():
    result = global_align("GATTACA", "GATTGCA", 1, -1, 1, 1)
    # The specified recurrence gives six matches and one mismatch, for a score of 5.
    assert result["score"] == 5
    assert result["score"] == _linear_score("GATTACA", "GATTGCA", 1, -1, 1)


def test_affine_alignment_recovers_inputs_and_score():
    a, b = "ACGTT", "ACT"
    result = global_align(a, b, 2, -1, 3, 1)
    assert result["aligned_a"].replace("-", "") == a
    assert result["aligned_b"].replace("-", "") == b
    assert len(result["aligned_a"]) == len(result["aligned_b"]) == len(result["operations"])
    assert result["score"] == _rescore(result, 2, -1, 3, 1)
    assert 0 <= result["identity"] <= 1


def test_affine_global_score_equals_linear_reference_for_random_cases():
    rng = random.Random(602)
    for _ in range(100):
        a = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 10)))
        b = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 10)))
        match = rng.randint(1, 3)
        mismatch = rng.randint(-3, -1)
        gap = rng.randint(1, 3)
        result = global_align(a, b, match, mismatch, gap, gap)
        assert result["score"] == _linear_score(a, b, match, mismatch, gap)
        assert result["score"] == _rescore(result, match, mismatch, gap, gap)


def test_local_alignment_segments_and_score():
    a, b = "TTACGTAA", "GGACGTA"
    result = local_align(a, b, 2, -1, 3, 1)
    assert result["score"] >= 0
    assert a[result["a_start"]:result["a_end"]].replace("-", "") == result["aligned_a"].replace("-", "")
    assert b[result["b_start"]:result["b_end"]].replace("-", "") == result["aligned_b"].replace("-", "")
    assert result["score"] == _rescore(result, 2, -1, 3, 1)


def test_align_endpoint_global_local_and_validation():
    global_response = client.post("/api/align", json={
        "seq_a": "ACGT", "seq_b": "AGT", "mode": "global", "method": "full",
    })
    assert global_response.status_code == 200
    assert global_response.json()["mode"] == "global"
    local_response = client.post("/api/align", json={
        "seq_a": "TACGT", "seq_b": "ACG", "mode": "local", "method": "full",
    })
    assert local_response.status_code == 200
    assert local_response.json()["a_start"] == 1
    assert client.post("/api/align", json={
        "seq_a": "ACGT", "seq_b": "AGT", "mode": "local", "method": "hirschberg",
    }).status_code == 422
    assert client.post("/api/align", json={
        "seq_a": "ACGT", "seq_b": "AGT", "mode": "global", "method": "hirschberg", "gap_open": 2, "gap_extend": 1,
    }).status_code == 422


def test_align_endpoint_hirschberg():
    response = client.post("/api/align", json={
        "seq_a": "ACGTAC", "seq_b": "ACTAC", "mode": "global", "method": "hirschberg",
        "gap_open": 2, "gap_extend": 2,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == global_align("ACGTAC", "ACTAC", 2, -1, 2, 2)["score"]


@pytest.mark.parametrize("bad", ["ACGX", ""])
def test_align_endpoint_rejects_invalid_or_empty_sequence(bad):
    response = client.post("/api/align", json={
        "seq_a": bad, "seq_b": "AC", "mode": "global", "method": "full",
    })
    assert response.status_code == 422
