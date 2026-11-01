"""Global and local pairwise alignment with affine gap penalties."""

NEG = -(10**9)
_M, _X, _Y, _STOP = 0, 1, 2, 3


def _identity(operations: list[str]) -> float:
    """Return the fraction of alignment columns that are exact matches."""
    return operations.count("match") / len(operations) if operations else 0.0


def global_align(a: str, b: str, match: int, mismatch: int, gap_open: int, gap_extend: int) -> dict:
    """Needleman-Wunsch/Gotoh global alignment in O(m*n) time and space."""
    m, n = len(a), len(b)
    M = [[NEG] * (n + 1) for _ in range(m + 1)]
    X = [[NEG] * (n + 1) for _ in range(m + 1)]
    Y = [[NEG] * (n + 1) for _ in range(m + 1)]
    trace_M = [bytearray(n + 1) for _ in range(m + 1)]
    trace_X = [bytearray(n + 1) for _ in range(m + 1)]
    trace_Y = [bytearray(n + 1) for _ in range(m + 1)]
    M[0][0] = 0
    for i in range(1, m + 1):
        X[i][0] = -gap_open - (i - 1) * gap_extend
        trace_X[i][0] = _M if i == 1 else _X
    for j in range(1, n + 1):
        Y[0][j] = -gap_open - (j - 1) * gap_extend
        trace_Y[0][j] = _M if j == 1 else _Y

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            substitution = match if a[i - 1] == b[j - 1] else mismatch
            diagonal = (M[i - 1][j - 1], X[i - 1][j - 1], Y[i - 1][j - 1])
            M[i][j] = max(diagonal) + substitution
            trace_M[i][j] = diagonal.index(max(diagonal))

            x_scores = (
                M[i - 1][j] - gap_open,
                X[i - 1][j] - gap_extend,
                Y[i - 1][j] - gap_open,
            )
            X[i][j] = max(x_scores)
            trace_X[i][j] = x_scores.index(X[i][j])

            y_scores = (
                M[i][j - 1] - gap_open,
                Y[i][j - 1] - gap_extend,
                X[i][j - 1] - gap_open,
            )
            Y[i][j] = max(y_scores)
            trace_Y[i][j] = (_M, _Y, _X)[y_scores.index(Y[i][j])]

    terminal_scores = (M[m][n], X[m][n], Y[m][n])
    state = terminal_scores.index(max(terminal_scores))
    score = terminal_scores[state]
    aligned_a: list[str] = []
    aligned_b: list[str] = []
    operations: list[str] = []
    i, j = m, n
    while i or j:
        if state == _M:
            previous = trace_M[i][j]
            char_a, char_b = a[i - 1], b[j - 1]
            aligned_a.append(char_a)
            aligned_b.append(char_b)
            operations.append("match" if char_a == char_b else "mismatch")
            i -= 1
            j -= 1
            state = previous
        elif state == _X:
            previous = trace_X[i][j]
            aligned_a.append(a[i - 1])
            aligned_b.append("-")
            operations.append("delete")
            i -= 1
            state = previous
        else:
            previous = trace_Y[i][j]
            aligned_a.append("-")
            aligned_b.append(b[j - 1])
            operations.append("insert")
            j -= 1
            state = previous

    aligned_a.reverse()
    aligned_b.reverse()
    operations.reverse()
    return {
        "score": score,
        "aligned_a": "".join(aligned_a),
        "aligned_b": "".join(aligned_b),
        "operations": operations,
        "identity": _identity(operations),
    }


def local_align(a: str, b: str, match: int, mismatch: int, gap_open: int, gap_extend: int) -> dict:
    """Smith-Waterman/Gotoh local alignment in O(m*n) time and space."""
    m, n = len(a), len(b)
    M = [[0] * (n + 1) for _ in range(m + 1)]
    X = [[NEG] * (n + 1) for _ in range(m + 1)]
    Y = [[NEG] * (n + 1) for _ in range(m + 1)]
    trace_M = [bytearray(n + 1) for _ in range(m + 1)]
    trace_X = [bytearray(n + 1) for _ in range(m + 1)]
    trace_Y = [bytearray(n + 1) for _ in range(m + 1)]
    best_score = 0
    best_i = best_j = 0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            substitution = match if a[i - 1] == b[j - 1] else mismatch
            diagonal = (M[i - 1][j - 1], X[i - 1][j - 1], Y[i - 1][j - 1])
            m_scores = (0, diagonal[0] + substitution, diagonal[1] + substitution, diagonal[2] + substitution)
            M[i][j] = max(m_scores)
            trace_M[i][j] = _STOP if m_scores[0] == M[i][j] else m_scores.index(M[i][j]) - 1

            x_scores = (
                M[i - 1][j] - gap_open,
                X[i - 1][j] - gap_extend,
                Y[i - 1][j] - gap_open,
            )
            X[i][j] = max(x_scores)
            trace_X[i][j] = x_scores.index(X[i][j])

            y_scores = (
                M[i][j - 1] - gap_open,
                Y[i][j - 1] - gap_extend,
                X[i][j - 1] - gap_open,
            )
            Y[i][j] = max(y_scores)
            trace_Y[i][j] = (_M, _Y, _X)[y_scores.index(Y[i][j])]

            if M[i][j] > best_score:
                best_score, best_i, best_j = M[i][j], i, j

    aligned_a: list[str] = []
    aligned_b: list[str] = []
    operations: list[str] = []
    i, j, state = best_i, best_j, _M
    while state != _STOP:
        if state == _M:
            if M[i][j] == 0:
                break
            previous = trace_M[i][j]
            char_a, char_b = a[i - 1], b[j - 1]
            aligned_a.append(char_a)
            aligned_b.append(char_b)
            operations.append("match" if char_a == char_b else "mismatch")
            i -= 1
            j -= 1
            state = previous
        elif state == _X:
            previous = trace_X[i][j]
            aligned_a.append(a[i - 1])
            aligned_b.append("-")
            operations.append("delete")
            i -= 1
            state = previous
        else:
            previous = trace_Y[i][j]
            aligned_a.append("-")
            aligned_b.append(b[j - 1])
            operations.append("insert")
            j -= 1
            state = previous

    aligned_a.reverse()
    aligned_b.reverse()
    operations.reverse()
    return {
        "score": best_score,
        "aligned_a": "".join(aligned_a),
        "aligned_b": "".join(aligned_b),
        "operations": operations,
        "identity": _identity(operations),
        "a_start": i,
        "a_end": best_i,
        "b_start": j,
        "b_end": best_j,
    }
