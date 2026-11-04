"""Linear-space Hirschberg global alignment with linear gap costs."""


def _score_row(a: str, b: str, match: int, mismatch: int, gap: int) -> list[int]:
    """Compute one Needleman-Wunsch row in O(len(a)*len(b)) time and O(len(b)) space."""
    previous = [-gap * j for j in range(len(b) + 1)]
    for i, char_a in enumerate(a, 1):
        current = [-gap * i]
        for j, char_b in enumerate(b, 1):
            substitution = match if char_a == char_b else mismatch
            current.append(max(
                previous[j - 1] + substitution,
                previous[j] - gap,
                current[j - 1] - gap,
            ))
        previous = current
    return previous


def _small_alignment(a: str, b: str, match: int, mismatch: int, gap: int) -> tuple[str, str, list[str]]:
    """Align a one-row or one-column subproblem with a small DP matrix."""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = -gap * i
    for j in range(n + 1):
        dp[0][j] = -gap * j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            substitution = match if a[i - 1] == b[j - 1] else mismatch
            dp[i][j] = max(dp[i - 1][j - 1] + substitution, dp[i - 1][j] - gap, dp[i][j - 1] - gap)

    aligned_a: list[str] = []
    aligned_b: list[str] = []
    operations: list[str] = []
    i, j = m, n
    while i or j:
        if i and j:
            substitution = match if a[i - 1] == b[j - 1] else mismatch
            if dp[i][j] == dp[i - 1][j - 1] + substitution:
                char_a, char_b = a[i - 1], b[j - 1]
                aligned_a.append(char_a)
                aligned_b.append(char_b)
                operations.append("match" if char_a == char_b else "mismatch")
                i -= 1
                j -= 1
                continue
        if i and dp[i][j] == dp[i - 1][j] - gap:
            aligned_a.append(a[i - 1])
            aligned_b.append("-")
            operations.append("delete")
            i -= 1
        else:
            aligned_a.append("-")
            aligned_b.append(b[j - 1])
            operations.append("insert")
            j -= 1

    return "".join(reversed(aligned_a)), "".join(reversed(aligned_b)), list(reversed(operations))


def hirschberg_align(a: str, b: str, match: int, mismatch: int, gap: int) -> dict:
    """Return a global linear-gap alignment in O(m*n) time and O(min(m,n)) space."""
    def recurse(left: str, right: str) -> tuple[str, str, list[str]]:
        if not left:
            return "-" * len(right), right, ["insert"] * len(right)
        if not right:
            return left, "-" * len(left), ["delete"] * len(left)
        if len(left) == 1 or len(right) == 1:
            return _small_alignment(left, right, match, mismatch, gap)

        middle = len(left) // 2
        forward = _score_row(left[:middle], right, match, mismatch, gap)
        backward = _score_row(left[middle:][::-1], right[::-1], match, mismatch, gap)
        split = max(range(len(right) + 1), key=lambda index: forward[index] + backward[len(right) - index])
        left_a, left_b, left_ops = recurse(left[:middle], right[:split])
        right_a, right_b, right_ops = recurse(left[middle:], right[split:])
        return left_a + right_a, left_b + right_b, left_ops + right_ops

    if len(b) <= len(a):
        aligned_a, aligned_b, operations = recurse(a, b)
    else:
        aligned_b, aligned_a, operations = recurse(b, a)
        operations = ["delete" if operation == "insert" else "insert" if operation == "delete" else operation for operation in operations]
    score = 0
    for char_a, char_b in zip(aligned_a, aligned_b):
        if char_a == "-" or char_b == "-":
            score -= gap
        elif char_a == char_b:
            score += match
        else:
            score += mismatch
    identity = operations.count("match") / len(operations) if operations else 0.0
    return {
        "score": score,
        "aligned_a": aligned_a,
        "aligned_b": aligned_b,
        "operations": operations,
        "identity": identity,
    }
