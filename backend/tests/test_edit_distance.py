from app.algorithms.edit_distance import edit_distance


def test_kitten_to_sitting_and_alignment_consistency():
    result = edit_distance("KITTEN", "SITTING")
    assert result["distance"] == 3
    assert len(result["aligned_a"]) == len(result["aligned_b"])
    assert len(result["operations"]) == len(result["aligned_a"])
    assert sum(operation != "match" for operation in result["operations"]) == 3


def test_identical_and_empty_strings():
    assert edit_distance("GATTACA", "GATTACA")["distance"] == 0
    assert edit_distance("", "ACGT")["distance"] == 4
    assert edit_distance("ACGT", "")["distance"] == 4
    assert edit_distance("", "")["similarity"] == 1.0


def test_traceback_prefers_diagonal_on_ties():
    result = edit_distance("A", "B")
    assert result["aligned_a"] == "A"
    assert result["aligned_b"] == "B"
    assert result["operations"] == ["substitute"]
