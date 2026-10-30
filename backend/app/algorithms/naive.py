"""Naive DNA pattern matching (O(n*m) time, O(1) auxiliary space)."""


def naive_search(text: str, pattern: str) -> tuple[list[int], int]:
    """Return overlapping match offsets and the number of character comparisons."""
    n, m = len(text), len(pattern)
    matches: list[int] = []
    comparisons = 0
    if m == 0 or m > n:
        return matches, comparisons

    for start in range(n - m + 1):
        offset = 0
        while offset < m:
            comparisons += 1
            if text[start + offset] != pattern[offset]:
                break
            offset += 1
        if offset == m:
            matches.append(start)
    return matches, comparisons
