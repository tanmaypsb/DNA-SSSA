"""Boyer-Moore search with bad-character and strong good-suffix rules."""


def _good_suffix_shifts(pattern: str) -> list[int]:
    """Build strong good-suffix shifts in O(m) time and O(m) space."""
    length = len(pattern)
    shifts = [0] * (length + 1)
    borders = [0] * (length + 1)

    i = length
    j = length + 1
    borders[i] = j
    while i > 0:
        while j <= length and pattern[i - 1] != pattern[j - 1]:
            if shifts[j] == 0:
                shifts[j] = j - i
            j = borders[j]
        i -= 1
        j -= 1
        borders[i] = j

    j = borders[0]
    for i in range(length + 1):
        if shifts[i] == 0:
            shifts[i] = j
        if i == j:
            j = borders[j]
    return shifts


def boyer_moore_search(text: str, pattern: str) -> tuple[list[int], int]:
    """Find overlapping matches in O(n/m) best, O(n*m) worst time, O(m+alphabet) space."""
    n, m = len(text), len(pattern)
    matches: list[int] = []
    comparisons = 0
    if m == 0 or m > n:
        return matches, comparisons

    last_occurrence = {character: index for index, character in enumerate(pattern)}
    good_suffix = _good_suffix_shifts(pattern)
    shift = 0

    while shift <= n - m:
        pattern_index = m - 1
        while pattern_index >= 0:
            comparisons += 1
            if pattern[pattern_index] != text[shift + pattern_index]:
                break
            pattern_index -= 1

        if pattern_index < 0:
            matches.append(shift)
            shift += good_suffix[0]
        else:
            bad_character = pattern_index - last_occurrence.get(text[shift + pattern_index], -1)
            shift += max(1, bad_character, good_suffix[pattern_index + 1])

    return matches, comparisons
