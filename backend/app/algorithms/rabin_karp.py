"""Rabin-Karp search (O(n+m) average, O(n*m) worst case, O(1) space)."""

_VALUES = {"A": 0, "C": 1, "G": 2, "T": 3, "N": 4}
_BASE = 5
_MODULUS = 1_000_000_007


def rabin_karp_search(text: str, pattern: str) -> tuple[list[int], int, int, int]:
    """Return offsets, update/verification comparisons, hash hits, and spurious hits."""
    n, m = len(text), len(pattern)
    matches: list[int] = []
    comparisons = hash_hits = spurious_hits = 0
    if m == 0 or m > n:
        return matches, comparisons, hash_hits, spurious_hits

    try:
        text_values = [_VALUES[char] for char in text]
        pattern_values = [_VALUES[char] for char in pattern]
    except KeyError as error:
        raise ValueError(f"unsupported DNA character: {error.args[0]}") from None

    high_order = pow(_BASE, m - 1, _MODULUS)
    pattern_hash = window_hash = 0
    for index in range(m):
        pattern_hash = (pattern_hash * _BASE + pattern_values[index]) % _MODULUS
        window_hash = (window_hash * _BASE + text_values[index]) % _MODULUS

    for start in range(n - m + 1):
        if window_hash == pattern_hash:
            hash_hits += 1
            for offset in range(m):
                comparisons += 1
                if text_values[start + offset] != pattern_values[offset]:
                    spurious_hits += 1
                    break
            else:
                matches.append(start)

        if start < n - m:
            comparisons += 1
            window_hash = (
                (window_hash - text_values[start] * high_order) * _BASE
                + text_values[start + m]
            ) % _MODULUS
    return matches, comparisons, hash_hits, spurious_hits
