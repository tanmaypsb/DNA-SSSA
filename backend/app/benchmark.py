"""Reproducible timing benchmarks for DNA matching algorithms."""

import random
import statistics
import time

from app.algorithms.kmp import kmp_search
from app.algorithms.naive import naive_search
from app.algorithms.rabin_karp import rabin_karp_search
from app.algorithms.boyer_moore import boyer_moore_search
from app.algorithms.z_algorithm import z_search

_DNA = "ACGT"


def run_benchmark(pattern_length: int, text_sizes: list[int], preset: str) -> dict:
    """Benchmark each matcher five times and return median milliseconds."""
    rng = random.Random(42)
    series = []
    for size in text_sizes:
        if preset == "worst_case":
            text = "A" * size
            pattern = "A" * (pattern_length - 1) + "C"
        else:
            text = "".join(rng.choice(_DNA) for _ in range(size))
            middle = max(0, (size - pattern_length) // 2)
            pattern = text[middle : middle + pattern_length]

        row = {"text_size": size}
        for name, matcher in (
            ("naive", naive_search),
            ("kmp", kmp_search),
            ("rabin_karp", rabin_karp_search),
            ("boyer_moore", boyer_moore_search),
            ("z_algorithm", z_search),
        ):
            times = []
            matches = []
            comparisons = 0
            for _ in range(5):
                started = time.perf_counter_ns()
                result = matcher(text, pattern)
                times.append((time.perf_counter_ns() - started) / 1_000_000)
                matches = result[0]
                comparisons = result[1]
            row[name] = {
                "time_ms": statistics.median(times),
                "comparisons": comparisons,
                "match_count": len(matches),
            }
        series.append(row)
    return {"preset": preset, "series": series}
