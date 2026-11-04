import random

from fastapi.testclient import TestClient

from app.algorithms.edit_distance import edit_distance
from app.algorithms.kmp import kmp_search
from app.algorithms.naive import naive_search
from app.algorithms.rabin_karp import rabin_karp_search
from app.main import app
from app.trace import trace_edit_distance, trace_search

client = TestClient(app)


def test_search_traces_match_real_algorithms_on_100_random_cases():
    rng = random.Random(90210)
    matchers = {
        "naive": naive_search,
        "kmp": kmp_search,
        "rabin_karp": rabin_karp_search,
    }
    for _ in range(100):
        text = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 30)))
        pattern = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 8)))
        for algorithm, matcher in matchers.items():
            assert trace_search(algorithm, text, pattern)["matches"] == matcher(text, pattern)[0]


def test_edit_distance_trace_matches_real_algorithm_on_100_random_cases():
    rng = random.Random(441)
    for _ in range(100):
        seq_a = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 12)))
        seq_b = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 12)))
        assert trace_edit_distance(seq_a, seq_b)["distance"] == edit_distance(seq_a, seq_b)["distance"]


def test_trace_search_api_shapes():
    response = client.post("/api/trace", json={"algorithm": "kmp", "text": "ACACACAGT", "pattern": "ACACAG"})
    assert response.status_code == 200
    data = response.json()
    assert data["matches"] == [2]
    assert data["lps"] == [0, 0, 1, 2, 3, 0]
    assert any(step["type"] == "fallback" for step in data["steps"])


def test_trace_edit_distance_api_matrix_and_traceback():
    response = client.post("/api/trace", json={"algorithm": "edit_distance", "seq_a": "CAT", "seq_b": "CGT"})
    assert response.status_code == 200
    data = response.json()
    assert data["distance"] == 1
    assert data["matrix"][-1][-1] == 1
    assert len(data["cells"]) == 16
    assert data["traceback"][0] == [3, 3]
    assert data["traceback"][-1] == [0, 0]


def test_trace_rejects_oversize_search_input():
    response = client.post(
        "/api/trace", json={"algorithm": "naive", "text": "A" * 301, "pattern": "A"}
    )
    assert response.status_code == 422
