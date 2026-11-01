"""Z-algorithm matching (O(n+m) time and space)."""


def _z_values(value: str) -> tuple[list[int], int]:
    """Compute the Z array in O(len(value)) time and space, counting equality tests."""
    length = len(value)
    z = [0] * length
    comparisons = 0
    left = right = 0

    for index in range(1, length):
        if index <= right:
            z[index] = min(right - index + 1, z[index - left])
        while index + z[index] < length:
            comparisons += 1
            if value[z[index]] != value[index + z[index]]:
                break
            z[index] += 1
        if index + z[index] - 1 > right:
            left, right = index, index + z[index] - 1

    return z, comparisons


def z_search(text: str, pattern: str) -> tuple[list[int], int, list[int]]:
    """Find all matches using pattern + separator + text in O(n+m) time and space."""
    m = len(pattern)
    if m == 0:
        return [], 0, []

    joined = pattern + "$" + text
    z, comparisons = _z_values(joined)
    matches = [index - m - 1 for index in range(m + 1, len(joined)) if z[index] == m]
    z_pattern = z[:m]
    z_pattern[0] = m
    return matches, comparisons, z_pattern
