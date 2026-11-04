from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_all_algorithms_and_optional_statistics():
    response = client.post(
        "/api/search",
        json={"text": "a cgtACGT", "pattern": "ACG", "algorithms": ["naive", "kmp", "rabin_karp", "boyer_moore", "z_algorithm"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["text_length"] == 8
    assert data["pattern_length"] == 3
    assert data["results"]["naive"]["matches"] == [0, 4]
    assert data["results"]["kmp"]["matches"] == [0, 4]
    assert data["results"]["rabin_karp"]["matches"] == [0, 4]
    assert data["results"]["boyer_moore"]["matches"] == [0, 4]
    assert data["results"]["z_algorithm"]["matches"] == [0, 4]
    assert data["kmp_lps"] == [0, 0, 0]
    assert data["rabin_karp_stats"] == {"hash_hits": 2, "spurious_hits": 0}
    assert data["z_array"] == [3, 0, 0]
    assert all("time_ms" in result and "comparisons" in result for result in data["results"].values())


def test_search_subset_has_null_optional_stats():
    response = client.post(
        "/api/search", json={"text": "AAAA", "pattern": "AA", "algorithms": ["naive"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"]["naive"]["matches"] == [0, 1, 2]
    assert data["kmp_lps"] is None
    assert data["rabin_karp_stats"] is None
    assert data["z_array"] is None


def test_similarity_success_and_normalization():
    response = client.post("/api/similarity", json={"seq_a": ">a\nACGT", "seq_b": "acg"})
    assert response.status_code == 200
    data = response.json()
    assert data["edit_distance"] == 1
    assert data["lcs_length"] == 3
    assert data["lcs_sequence"] == "ACG"
    assert len(data["aligned_a"]) == len(data["aligned_b"]) == len(data["operations"])


def test_benchmark_success_shape_and_reproducible_counts():
    payload = {"pattern_length": 2, "text_sizes": [8, 10], "preset": "random"}
    first = client.post("/api/benchmark", json=payload)
    second = client.post("/api/benchmark", json=payload)
    assert first.status_code == second.status_code == 200
    data = first.json()
    assert data["preset"] == "random"
    assert [row["text_size"] for row in data["series"]] == [8, 10]
    for row in data["series"]:
        for algorithm in ("naive", "kmp", "rabin_karp", "boyer_moore", "z_algorithm"):
            assert set(row[algorithm]) == {"time_ms", "comparisons", "match_count"}
            assert row[algorithm]["match_count"] >= 1
    assert [[row["naive"]["match_count"], row["kmp"]["match_count"], row["rabin_karp"]["match_count"]] for row in data["series"]] == [
        [row["naive"]["match_count"], row["kmp"]["match_count"], row["rabin_karp"]["match_count"]]
        for row in second.json()["series"]
    ]


def test_benchmark_worst_case():
    response = client.post(
        "/api/benchmark", json={"pattern_length": 3, "text_sizes": [8], "preset": "worst_case"}
    )
    assert response.status_code == 200
    assert all(item["match_count"] == 0 for key, item in response.json()["series"][0].items() if key != "text_size")


def test_upload_fasta_success():
    response = client.post(
        "/api/upload",
        files={"file": ("sample.fasta", b">sample\nac gt\n", "text/plain")},
    )
    assert response.status_code == 200
    assert response.json() == {"sequence": "ACGT", "length": 4}


def test_generate_success_and_range():
    response = client.get("/api/generate?length=25")
    assert response.status_code == 200
    sequence = response.json()["sequence"]
    assert len(sequence) == 25
    assert set(sequence) <= set("ACGT")
    assert client.get("/api/generate?length=0").status_code == 422


def test_invalid_characters_return_422():
    response = client.post(
        "/api/search", json={"text": "ACGX", "pattern": "A", "algorithms": ["naive"]}
    )
    assert response.status_code == 422
    assert "invalid character" in response.json()["detail"]


def test_empty_input_returns_422():
    response = client.post(
        "/api/search", json={"text": "ACGT", "pattern": " \n", "algorithms": ["naive"]}
    )
    assert response.status_code == 422
    assert "must not be empty" in response.json()["detail"]


def test_oversize_input_returns_422():
    response = client.post(
        "/api/search",
        json={"text": "A" * 2_000_001, "pattern": "A", "algorithms": ["naive"]},
    )
    assert response.status_code == 422
    assert "at most 2000000" in response.json()["detail"]
