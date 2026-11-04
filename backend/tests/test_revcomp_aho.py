import random

from fastapi.testclient import TestClient

from app.algorithms.aho_corasick import aho_corasick_search
from app.main import app
from app.utils import reverse_complement

client = TestClient(app)


def _reference_matches(text, patterns):
    found = []
    for pattern_index, pattern in enumerate(patterns):
        if not pattern:
            continue
        start = text.find(pattern)
        while start != -1:
            found.append((start, pattern_index))
            start = text.find(pattern, start + 1)
    return sorted(found)


def _reference_reverse_complement(sequence):
    complement = {"A": "T", "C": "G", "G": "C", "T": "A", "N": "N"}
    return "".join(complement[character] for character in reversed(sequence))


def test_aho_corasick_matches_reference_for_200_random_cases():
    rng = random.Random(707)
    for _ in range(200):
        text = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 60)))
        seed = "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 6)))
        patterns = [seed[:length] for length in range(1, len(seed) + 1)]
        patterns.append(seed)
        patterns.extend(
            "".join(rng.choice("ACGT") for _ in range(rng.randint(1, 6)))
            for _ in range(rng.randint(1, 5))
        )
        expected = _reference_matches(text, patterns)
        matches, comparisons, node_count = aho_corasick_search(text, patterns)
        assert matches == expected
        assert comparisons >= 0
        assert node_count >= 1


def test_aho_corasick_classic_case_matches_reference():
    patterns = ["A", "AB", "BAB", "BC", "BCA", "C", "CAA"]
    text = "ABCCABAB"
    assert aho_corasick_search(text, patterns)[0] == _reference_matches(text, patterns)


def test_reverse_complement_matches_independent_reference_and_involution():
    sequence = "AACGT"
    expected = _reference_reverse_complement(sequence)
    assert reverse_complement(sequence) == expected
    assert reverse_complement(reverse_complement(sequence)) == sequence
    response = client.post("/api/revcomp", json={"sequence": sequence.lower()})
    assert response.status_code == 200
    assert response.json() == {"sequence": sequence, "reverse_complement": expected}


def test_search_both_strands_returns_forward_coordinates():
    text = "AACGTTA"
    pattern = "ACG"
    reverse_pattern = _reference_reverse_complement(pattern)
    expected_forward = [start for start, _ in _reference_matches(text, [pattern])]
    expected_reverse = [start for start, _ in _reference_matches(text, [reverse_pattern])]
    response = client.post("/api/search", json={
        "text": text, "pattern": pattern, "algorithms": ["kmp"], "both_strands": True,
    })
    assert response.status_code == 200
    result = response.json()["results"]["kmp"]
    assert result["matches"] == expected_forward
    assert result["reverse_matches"] == expected_reverse

    forward_only = client.post("/api/search", json={
        "text": text, "pattern": pattern, "algorithms": ["kmp"],
    })
    assert forward_only.status_code == 200
    assert forward_only.json()["results"]["kmp"]["reverse_matches"] is None


def test_multisearch_endpoint_deduplicates_patterns_and_returns_counts():
    response = client.post("/api/multisearch", json={
        "text": "ACGTAC", "patterns": ["AC", "CG", "AC", "T"],
    })
    assert response.status_code == 200
    data = response.json()
    unique_patterns = list(dict.fromkeys(["AC", "CG", "AC", "T"]))
    expected = _reference_matches("ACGTAC", unique_patterns)
    assert data["matches"] == [{"pattern": unique_patterns[index], "start": start} for start, index in expected]
    expected_counts = {pattern: sum(1 for start, index in expected if unique_patterns[index] == pattern) for pattern in unique_patterns}
    assert data["counts"] == expected_counts
    assert data["node_count"] > 1
    assert data["comparisons"] >= 0


def test_multisearch_endpoint_rejects_invalid_pattern_limits():
    assert client.post("/api/multisearch", json={"text": "ACGT", "patterns": []}).status_code == 422
    assert client.post("/api/multisearch", json={"text": "ACGT", "patterns": ["A" * 101]}).status_code == 422
