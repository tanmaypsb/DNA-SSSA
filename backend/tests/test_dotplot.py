import pytest
from fastapi.testclient import TestClient

from app.dotplot import compute_dotplot
from app.main import app

client = TestClient(app)


def test_identical_sequences_produce_main_diagonal():
    result = compute_dotplot("ACGT", "ACGT", 2, 2)
    assert result == {"rows": 3, "cols": 3, "points": [[0, 0], [1, 1], [2, 2]]}


def test_dotplot_threshold_counts_matches_within_window():
    result = compute_dotplot("AAAA", "AAAT", 3, 3)
    assert [0, 0] in result["points"]
    assert [0, 1] not in result["points"]


def test_dotplot_endpoint_success_and_limits():
    response = client.post("/api/dotplot", json={"seq_a": "ACGT", "seq_b": "ACGT", "window": 2, "threshold": 2})
    assert response.status_code == 200
    assert response.json()["points"] == [[0, 0], [1, 1], [2, 2]]
    assert client.post("/api/dotplot", json={"seq_a": "AAAA", "seq_b": "AAAA", "window": 3, "threshold": 4}).status_code == 422
    assert client.post("/api/dotplot", json={"seq_a": "A" * 500, "seq_b": "A" * 500}).status_code == 422
