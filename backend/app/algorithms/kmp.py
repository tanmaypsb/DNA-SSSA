"""Knuth-Morris-Pratt search (O(n+m) time, O(m) auxiliary space)."""


def build_lps(pattern: str) -> list[int]:
    """Build the longest proper prefix/suffix length for each pattern prefix."""
    lps = [0] * len(pattern)
    length = 0
    index = 1
    while index < len(pattern):
        if pattern[index] == pattern[length]:
            length += 1
            lps[index] = length
            index += 1
        elif length:
            length = lps[length - 1]
        else:
            index += 1
    return lps


def kmp_search(text: str, pattern: str) -> tuple[list[int], int, list[int]]:
    """Return overlapping match offsets, comparisons, and the pattern LPS table."""
    lps = build_lps(pattern)
    matches: list[int] = []
    comparisons = 0
    if not pattern:
        return matches, comparisons, lps

    text_index = pattern_index = 0
    while text_index < len(text):
        comparisons += 1
        if text[text_index] == pattern[pattern_index]:
            text_index += 1
            pattern_index += 1
            if pattern_index == len(pattern):
                matches.append(text_index - pattern_index)
                pattern_index = lps[pattern_index - 1]
        elif pattern_index:
            pattern_index = lps[pattern_index - 1]
        else:
            text_index += 1
    return matches, comparisons, lps
