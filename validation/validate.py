"""Standalone cross-checks for the DNA analyzer implementation."""

from __future__ import annotations

import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app import benchmark  # noqa: E402
from app.algorithms.aho_corasick import aho_corasick_search  # noqa: E402
from app.algorithms.alignment import global_align, local_align  # noqa: E402
from app.algorithms.boyer_moore import boyer_moore_search  # noqa: E402
from app.algorithms.edit_distance import edit_distance  # noqa: E402
from app.algorithms.kmp import kmp_search  # noqa: E402
from app.algorithms.lcs import lcs  # noqa: E402
from app.algorithms.naive import naive_search  # noqa: E402
from app.algorithms.rabin_karp import rabin_karp_search  # noqa: E402
from app.algorithms.z_algorithm import z_search  # noqa: E402
from app.utils import normalize_sequence  # noqa: E402


def reference_matches(text: str, pattern: str) -> list[int]:
    """Use Python's find only as an independent validation reference."""
    found: list[int] = []
    start = 0
    while True:
        start = text.find(pattern, start)
        if start < 0:
            return found
        found.append(start)
        start += 1


def alignment_score(aligned_a: str, aligned_b: str, match: int, mismatch: int, gap: int) -> int:
    score = 0
    for char_a, char_b in zip(aligned_a, aligned_b):
        score += -gap if "-" in (char_a, char_b) else match if char_a == char_b else mismatch
    return score


def report(label: str, passed: bool, detail: str = "") -> bool:
    print(f"{'PASS' if passed else 'FAIL'}: {label}" + (f" — {detail}" if detail else ""))
    return passed


def main() -> int:
    checks: list[bool] = []
    fasta = ROOT / "validation" / "sample.fasta"
    sequence = normalize_sequence(fasta.read_text(encoding="utf-8"))
    checks.append(report("FASTA normalization", bool(sequence), f"loaded {len(sequence):,} bases"))
    if not sequence:
        print("Summary: 0 passed, 1 failed")
        return 1

    rng = random.Random(42)
    search_ok = True
    for _ in range(20):
        pattern_length = rng.randint(8, 20)
        start = rng.randint(0, len(sequence) - pattern_length)
        pattern = sequence[start : start + pattern_length]
        expected = reference_matches(sequence, pattern)
        observed = [
            naive_search(sequence, pattern)[0],
            kmp_search(sequence, pattern)[0],
            rabin_karp_search(sequence, pattern)[0],
            boyer_moore_search(sequence, pattern)[0],
            z_search(sequence, pattern)[0],
            [position for position, _ in aho_corasick_search(sequence, [pattern])[0]],
        ]
        if any(matches != expected for matches in observed):
            search_ok = False
            break
    checks.append(report("Six search algorithms agree on 20 sampled patterns", search_ok))

    # Reuse the benchmark module's algorithm implementations, with real FASTA
    # prefixes in place of its built-in generated text.
    sizes = [size for size in (1_000, 5_000, 10_000, 50_000, 100_000) if size <= len(sequence)]
    matchers = (
        ("naive", benchmark.naive_search),
        ("kmp", benchmark.kmp_search),
        ("rabin_karp", benchmark.rabin_karp_search),
        ("boyer_moore", benchmark.boyer_moore_search),
        ("z_algorithm", benchmark.z_search),
    )
    print("\nReal-sequence benchmark (median of 5; milliseconds)")
    print(f"{'size':>8}  " + "  ".join(f"{name:>13}" for name, _ in matchers))
    benchmark_ok = bool(sizes)
    for size in sizes:
        text = sequence[:size]
        pattern_length = min(20, size)
        midpoint = max(0, (size - pattern_length) // 2)
        pattern = text[midpoint : midpoint + pattern_length]
        timings = []
        for _, matcher in matchers:
            samples = []
            for _ in range(5):
                before = time.perf_counter_ns()
                matcher(text, pattern)
                samples.append((time.perf_counter_ns() - before) / 1_000_000)
            timings.append(statistics.median(samples))
        print(f"{size:>8,}  " + "  ".join(f"{value:>13.3f}" for value in timings))
    checks.append(report("Benchmark completed on real-sequence prefixes", benchmark_ok,
                         f"largest size {max(sizes):,}" if sizes else "no benchmark sizes available"))

    try:
        from Bio.Align import PairwiseAligner
    except ImportError:
        checks.append(report("Biopython score cross-check", True, "SKIP: Biopython is not installed"))
    else:
        aligner_edit = PairwiseAligner(mode="global", match_score=0, mismatch_score=-1,
                                       open_gap_score=-1, extend_gap_score=-1)
        aligner_lcs = PairwiseAligner(mode="global", match_score=1, mismatch_score=0,
                                      open_gap_score=0, extend_gap_score=0)
        aligner_global = PairwiseAligner(mode="global", match_score=2, mismatch_score=-1,
                                         open_gap_score=-1, extend_gap_score=-1)
        # PairwiseAligner charges open_gap_score for the first gap column and
        # extend_gap_score for each later one, matching gap_open + (k-1)*gap_extend.
        aligner_affine_global = PairwiseAligner(mode="global", match_score=2, mismatch_score=-1,
                                                open_gap_score=-3, extend_gap_score=-1)
        aligner_affine_local = PairwiseAligner(mode="local", match_score=2, mismatch_score=-1,
                                               open_gap_score=-3, extend_gap_score=-1)
        score_ok = True
        affine_ok = True
        for _ in range(20):
            start_a = rng.randint(0, len(sequence) - 200)
            start_b = rng.randint(0, len(sequence) - 200)
            seq_a, seq_b = sequence[start_a : start_a + 200], sequence[start_b : start_b + 200]
            project_edit = edit_distance(seq_a, seq_b)["distance"]
            project_lcs = lcs(seq_a, seq_b)["length"]
            project_global = global_align(seq_a, seq_b, 2, -1, 1, 1)["score"]
            project_affine_global = global_align(seq_a, seq_b, 2, -1, 3, 1)["score"]
            project_local = local_align(seq_a, seq_b, 2, -1, 3, 1)["score"]
            if (-project_edit != aligner_edit.score(seq_a, seq_b)
                    or project_lcs != aligner_lcs.score(seq_a, seq_b)
                    or project_global != aligner_global.score(seq_a, seq_b)):
                score_ok = False
            if (project_affine_global != aligner_affine_global.score(seq_a, seq_b)
                    or project_local != aligner_affine_local.score(seq_a, seq_b)):
                affine_ok = False
        checks.append(report("20 edit distance, LCS, and linear-gap global score pairs vs Biopython", score_ok))
        checks.append(report("20 affine global and local alignment score pairs vs Biopython", affine_ok))

    passed = sum(checks)
    failed = len(checks) - passed
    print(f"\nSummary: {passed} passed, {failed} failed ({len(checks)} checks)")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
