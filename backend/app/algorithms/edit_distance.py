"""Levenshtein distance and deterministic alignment (O(m*n) time and space)."""

_ALIGNMENT_CELL_LIMIT = 25_000_000


def _distance_two_rows(a: str, b: str) -> int:
    """Compute Levenshtein distance using O(min(m,n)) auxiliary space."""
    if len(b) > len(a):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (char_a != char_b),
            ))
        previous = current
    return previous[-1]


def edit_distance(a: str, b: str) -> dict:
    """Return Levenshtein distance, similarity, and a tie-broken alignment."""
    m, n = len(a), len(b)
    if m * n > _ALIGNMENT_CELL_LIMIT:
        distance = _distance_two_rows(a, b)
        return {
            "distance": distance,
            "similarity": 1.0 - distance / max(m, n),
            "aligned_a": None,
            "aligned_b": None,
            "operations": None,
            "alignment_skipped": True,
        }

    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i][j] = min(
                dp[i - 1][j - 1] + (a[i - 1] != b[j - 1]),
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
            )

    aligned_a: list[str] = []
    aligned_b: list[str] = []
    operations: list[str] = []
    i, j = m, n
    while i or j:
        if i and j:
            cost = 0 if a[i - 1] == b[j - 1] else 1
            if dp[i][j] == dp[i - 1][j - 1] + cost:
                aligned_a.append(a[i - 1])
                aligned_b.append(b[j - 1])
                operations.append("match" if cost == 0 else "substitute")
                i -= 1
                j -= 1
                continue
        if i and dp[i][j] == dp[i - 1][j] + 1:
            aligned_a.append(a[i - 1])
            aligned_b.append("-")
            operations.append("delete")
            i -= 1
        else:
            aligned_a.append("-")
            aligned_b.append(b[j - 1])
            operations.append("insert")
            j -= 1

    aligned_a.reverse()
    aligned_b.reverse()
    operations.reverse()
    distance = dp[m][n]
    return {
        "distance": distance,
        "similarity": 1.0 - distance / max(m, n) if max(m, n) else 1.0,
        "aligned_a": "".join(aligned_a),
        "aligned_b": "".join(aligned_b),
        "operations": operations,
        "alignment_skipped": False,
    }
