"""Step-recording versions of search and edit-distance algorithms for visualization."""

from app.algorithms.kmp import build_lps

_VALUES = {"A": 0, "C": 1, "G": 2, "T": 3, "N": 4}
_BASE = 5
_MODULUS = 1_000_000_007


def trace_search(algorithm: str, text: str, pattern: str) -> dict:
    """Return per-operation search trace steps and all match positions."""
    if algorithm == "naive":
        return _trace_naive(text, pattern)
    if algorithm == "kmp":
        return _trace_kmp(text, pattern)
    if algorithm == "rabin_karp":
        return _trace_rabin_karp(text, pattern)
    raise ValueError(f"unsupported trace algorithm: {algorithm}")


def _trace_naive(text: str, pattern: str) -> dict:
    matches: list[int] = []
    steps: list[dict] = []
    n, m = len(text), len(pattern)
    for shift in range(max(0, n - m + 1)):
        for pattern_index in range(m):
            result = "match" if text[shift + pattern_index] == pattern[pattern_index] else "mismatch"
            steps.append({
                "type": "compare",
                "shift": shift,
                "pattern_index": pattern_index,
                "text_index": shift + pattern_index,
                "result": result,
            })
            if result == "mismatch":
                break
        else:
            matches.append(shift)
            steps.append({"type": "match_found", "shift": shift})
    return {"algorithm": "naive", "text": text, "pattern": pattern, "matches": matches, "lps": None, "steps": steps}


def _trace_kmp(text: str, pattern: str) -> dict:
    lps = build_lps(pattern)
    matches: list[int] = []
    steps: list[dict] = []
    text_index = pattern_index = 0
    while pattern and text_index < len(text):
        result = "match" if text[text_index] == pattern[pattern_index] else "mismatch"
        steps.append({
            "type": "compare",
            "text_index": text_index,
            "pattern_index": pattern_index,
            "result": result,
        })
        if result == "match":
            text_index += 1
            pattern_index += 1
            if pattern_index == len(pattern):
                shift = text_index - len(pattern)
                matches.append(shift)
                steps.append({"type": "match_found", "shift": shift})
                fallback = lps[pattern_index - 1]
                steps.append({"type": "fallback", "from": pattern_index, "to": fallback})
                pattern_index = fallback
        elif pattern_index:
            fallback = lps[pattern_index - 1]
            steps.append({"type": "fallback", "from": pattern_index, "to": fallback})
            pattern_index = fallback
        else:
            text_index += 1
    return {"algorithm": "kmp", "text": text, "pattern": pattern, "matches": matches, "lps": lps, "steps": steps}


def _trace_rabin_karp(text: str, pattern: str) -> dict:
    matches: list[int] = []
    steps: list[dict] = []
    n, m = len(text), len(pattern)
    if not m or m > n:
        return {"algorithm": "rabin_karp", "text": text, "pattern": pattern, "matches": matches, "lps": None, "steps": steps}

    high_order = pow(_BASE, m - 1, _MODULUS)
    pattern_hash = window_hash = 0
    for index in range(m):
        pattern_hash = (pattern_hash * _BASE + _VALUES[pattern[index]]) % _MODULUS
        window_hash = (window_hash * _BASE + _VALUES[text[index]]) % _MODULUS

    for shift in range(n - m + 1):
        equal = window_hash == pattern_hash
        steps.append({
            "type": "hash",
            "shift": shift,
            "window_hash": window_hash,
            "pattern_hash": pattern_hash,
            "equal": equal,
        })
        if equal:
            verified = True
            for offset in range(m):
                if text[shift + offset] != pattern[offset]:
                    verified = False
                    break
            steps.append({"type": "verify", "shift": shift, "result": "match" if verified else "spurious"})
            if verified:
                matches.append(shift)
                steps.append({"type": "match_found", "shift": shift})

        if shift < n - m:
            window_hash = (
                (window_hash - _VALUES[text[shift]] * high_order) * _BASE
                + _VALUES[text[shift + m]]
            ) % _MODULUS
    return {"algorithm": "rabin_karp", "text": text, "pattern": pattern, "matches": matches, "lps": None, "steps": steps}


def trace_edit_distance(seq_a: str, seq_b: str) -> dict:
    """Return a full edit-distance matrix, cell provenance, and deterministic traceback."""
    m, n = len(seq_a), len(seq_b)
    matrix = [[0] * (n + 1) for _ in range(m + 1)]
    cells: list[dict] = []

    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 and j == 0:
                source = "init"
            elif i == 0:
                matrix[i][j] = j
                source = "init"
            elif j == 0:
                matrix[i][j] = i
                source = "init"
            else:
                diagonal_cost = matrix[i - 1][j - 1] + (seq_a[i - 1] != seq_b[j - 1])
                delete_cost = matrix[i - 1][j] + 1
                insert_cost = matrix[i][j - 1] + 1
                matrix[i][j] = min(diagonal_cost, delete_cost, insert_cost)
                if diagonal_cost == matrix[i][j]:
                    source = "match" if seq_a[i - 1] == seq_b[j - 1] else "substitute"
                elif delete_cost == matrix[i][j]:
                    source = "delete"
                else:
                    source = "insert"
            cells.append({"i": i, "j": j, "value": matrix[i][j], "source": source})

    traceback = [[m, n]]
    i, j = m, n
    while i or j:
        if i and j:
            cost = 0 if seq_a[i - 1] == seq_b[j - 1] else 1
            if matrix[i][j] == matrix[i - 1][j - 1] + cost:
                i -= 1
                j -= 1
            elif i and matrix[i][j] == matrix[i - 1][j] + 1:
                i -= 1
            else:
                j -= 1
        elif i:
            i -= 1
        else:
            j -= 1
        traceback.append([i, j])

    return {
        "seq_a": seq_a,
        "seq_b": seq_b,
        "distance": matrix[m][n],
        "matrix": matrix,
        "cells": cells,
        "traceback": traceback,
    }
