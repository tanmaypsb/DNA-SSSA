from app.algorithms.lcs import lcs


def _is_subsequence(candidate, text):
    position = 0
    for char in text:
        if position < len(candidate) and candidate[position] == char:
            position += 1
    return position == len(candidate)


def test_classic_lcs_example_and_subsequence():
    result = lcs("AGGTAB", "GXTXAYB")
    assert result["length"] == 4
    assert result["sequence"] == "GTAB"
    assert _is_subsequence(result["sequence"], "AGGTAB")
    assert _is_subsequence(result["sequence"], "GXTXAYB")


def test_identical_and_disjoint_strings():
    assert lcs("ACGT", "ACGT")["length"] == 4
    result = lcs("AAA", "CCC")
    assert result["length"] == 0
    assert result["sequence"] == ""


def test_empty_strings_similarity():
    assert lcs("", "")["similarity"] == 1.0
    assert lcs("", "AC")["length"] == 0
