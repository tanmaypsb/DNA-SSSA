"""Diagonal-window dot plot calculation."""


def compute_dotplot(seq_a: str, seq_b: str, window: int, threshold: int) -> dict:
    """Mark diagonal windows meeting a match threshold in O(m*n) time and space."""
    m, n = len(seq_a), len(seq_b)
    if window > m or window > n:
        raise ValueError("window must not exceed either sequence length")

    diagonal_prefix = [[0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            diagonal_prefix[i][j] = (1 if seq_a[i] == seq_b[j] else 0)
            if i and j:
                diagonal_prefix[i][j] += diagonal_prefix[i - 1][j - 1]

    rows = m - window + 1
    cols = n - window + 1
    points = []
    for i in range(rows):
        end_i = i + window - 1
        for j in range(cols):
            end_j = j + window - 1
            count = diagonal_prefix[end_i][end_j]
            if i and j:
                count -= diagonal_prefix[i - 1][j - 1]
            if count >= threshold:
                points.append([i, j])
                if len(points) > 200_000:
                    raise ValueError("dot plot has more than 200000 points; increase the window or threshold")
    return {"rows": rows, "cols": cols, "points": points}
