"""Longest common subsequence (O(m*n) time and space)."""

_ALIGNMENT_CELL_LIMIT = 25_000_000


def _length_two_rows(a: str, b: str) -> int:
    """Compute LCS length using O(min(m,n)) auxiliary space."""
    if len(b) > len(a):
        a, b = b, a
    previous = [0] * (len(b) + 1)
    for char_a in a:
        current = [0]
        for j, char_b in enumerate(b, 1):
            if char_a == char_b:
                current.append(previous[j - 1] + 1)
            else:
                current.append(max(previous[j], current[j - 1]))
        previous = current
    return previous[-1]


def lcs(a: str, b: str) -> dict:
    """Return LCS length, one LCS string, similarity, and fallback status."""
    m, n = len(a), len(b)
    if m * n > _ALIGNMENT_CELL_LIMIT:
        length = _length_two_rows(a, b)
        return {
            "length": length,
            "sequence": None,
            "similarity": 2 * length / (m + n) if m + n else 1.0,
            "alignment_skipped": True,
        }

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    sequence: list[str] = []
    i, j = m, n
    while i and j:
        if a[i - 1] == b[j - 1]:
            sequence.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    sequence.reverse()
    length = dp[m][n]
    return {
        "length": length,
        "sequence": "".join(sequence),
        "similarity": 2 * length / (m + n) if m + n else 1.0,
        "alignment_skipped": False,
    }
