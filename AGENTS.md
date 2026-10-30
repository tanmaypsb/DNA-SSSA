# AGENTS.md: DNA Sequence Search and Similarity Analyzer

## Project goal
A DAA (Design and Analysis of Algorithms) lab project. A web app that searches for DNA patterns in sequences and measures similarity between sequences, using string algorithms written from scratch, with benchmarks that compare their performance.

## Working rules (read first)
1. Work in phases. Do ONLY the phase requested in the current prompt. Do not start later phases.
2. Do not add features, libraries, files, or pages that are not listed in this document.
3. If something in this document is ambiguous, pick the simplest interpretation, state your assumption in one line, and continue. Do not ask questions unless you are completely blocked.
4. After finishing a phase, run the relevant tests or build, fix failures, then stop and report results briefly.
5. Keep code readable, with short docstrings stating each algorithm's time and space complexity. No unnecessary abstractions.

## Tech stack (fixed, do not substitute)
- Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
- Testing: pytest, httpx (for API tests)
- Frontend: React 18 + Vite + TypeScript, Tailwind CSS, Recharts
- Storage: none. Everything is in memory. No database, no auth.
- Ports: backend 8000, frontend 5173. Vite dev server proxies `/api` to `http://localhost:8000`.
- Enable CORS on the backend for `http://localhost:5173`.

## Algorithm rule (critical)
All core algorithms MUST be implemented from scratch in pure Python.
FORBIDDEN inside `backend/app/algorithms/`: `re`, `str.find`, `str.index`, `str.count`, `str.replace`, `in` operator for substring search, `difflib`, `Levenshtein`, `numpy`, `Bio`/Biopython, or any library that performs matching or alignment.
`str.find` and similar are allowed ONLY inside test files, as a reference to verify correctness.

## Input rules
- Alphabet: A, C, G, T (N also accepted and treated as an ordinary character).
- Normalisation (in `backend/app/utils.py`): remove FASTA header lines (starting with `>`), strip all whitespace and newlines, convert to uppercase.
- After normalisation, any character outside `ACGTN` returns HTTP 422 with a clear message.
- Empty sequence or empty pattern returns HTTP 422.
- Maximum input length: 2,000,000 characters per sequence. Longer returns HTTP 422.
- Matching indices are 0-based and include overlapping matches.

## Folder structure (create exactly this)
```
dna-analyzer/   <- this is the workspace root, do NOT create another nested folder
  AGENTS.md
  README.md
  ALGORITHMS.md
  backend/
    requirements.txt
    app/
      __init__.py
      main.py
      schemas.py
      utils.py
      benchmark.py
      algorithms/
        __init__.py
        naive.py
        kmp.py
        rabin_karp.py
        edit_distance.py
        lcs.py
    tests/
      test_search.py
      test_edit_distance.py
      test_lcs.py
      test_api.py
  frontend/    <- Vite React TS project
```
The workspace root IS the project root. Create `backend/` and `frontend/` directly inside it.

## Algorithm specifications

### 1. Naive matching (`naive.py`)
- Slide the pattern over every shift 0..n-m, compare left to right, stop at the first mismatch.
- Time O(n*m) worst case, space O(1).
- Function: `naive_search(text, pattern) -> (matches: list[int], comparisons: int)`
- `comparisons` counts every single character comparison.

### 2. KMP (`kmp.py`)
- Build the LPS (longest proper prefix which is also suffix) array in O(m).
- Scan the text in O(n) with the text pointer never moving backwards.
- Time O(n+m), space O(m).
- Functions: `build_lps(pattern) -> list[int]` and `kmp_search(text, pattern) -> (matches, comparisons, lps)`
- Must find overlapping matches (after a full match, continue using `lps[m-1]`).

### 3. Rabin-Karp (`rabin_karp.py`)
- Character mapping: A=0, C=1, G=2, T=3, N=4. Base = 5. Modulus q = 1_000_000_007.
- Rolling hash: precompute `base^(m-1) mod q`. Remove the leading character, shift, and add the trailing character. Always use `% q` to keep values non-negative.
- On every hash equality, verify the window character by character. Count a hash hit that fails verification as a spurious hit.
- Time O(n+m) average, O(n*m) worst case, space O(1).
- Function: `rabin_karp_search(text, pattern) -> (matches, comparisons, hash_hits, spurious_hits)`
- `comparisons` counts hash window updates plus verification character comparisons.

### 4. Edit distance (`edit_distance.py`)
- Levenshtein distance. Insert = 1, delete = 1, substitute = 1, match = 0.
- Full (m+1) x (n+1) DP matrix, then traceback from (m, n) to (0, 0).
- Traceback priority when costs tie: diagonal (match or substitute), then delete, then insert.
- Returns: `distance`, `aligned_a` and `aligned_b` (strings with `-` for gaps, equal length), `operations` (list of "match" | "substitute" | "insert" | "delete", same length as the aligned strings).
- Similarity = `1 - distance / max(m, n)`, as a float from 0 to 1.
- Time O(m*n), space O(m*n).
- Large input fallback: if `m * n > 25_000_000`, use the two-row space-optimised version, return only `distance`, set alignment fields to `null`, and set `alignment_skipped = true`.
- Function: `edit_distance(a, b) -> dict`

### 5. LCS (`lcs.py`)
- Classic DP matrix with traceback to recover ONE actual longest common subsequence string.
- Traceback tie rule: on a match go diagonal; otherwise move up if `dp[i-1][j] >= dp[i][j-1]`, else left.
- Similarity = `2 * lcs_length / (m + n)`, as a float from 0 to 1.
- Time O(m*n), space O(m*n). Same large input fallback as edit distance (length only, `lcs` string = `null`, `alignment_skipped = true`).
- Function: `lcs(a, b) -> dict` with `length`, `sequence`, `similarity`, `alignment_skipped`.

### 6. Benchmark (`benchmark.py`)
- Use `time.perf_counter_ns`. For each algorithm run 5 times and report the MEDIAN time in milliseconds.
- Random text: generated with `random.Random(42)` over `ACGT`, so results are reproducible.
- Pattern: taken as a slice of the generated text at its middle, so at least one match exists. Length = `pattern_length`.
- Preset `"worst_case"`: text = `"A" * size`, pattern = `"A" * (pattern_length - 1) + "C"`.
- For each text size returns, per algorithm (naive, kmp, rabin_karp): `time_ms`, `comparisons`, `match_count`.
- Limits: text_sizes values max 200,000. Max 8 sizes per request. pattern_length between 2 and 1,000.

## API contract (fixed, do not rename)
All endpoints under `/api`, JSON in and out.

### POST /api/search
Request: `{ "text": str, "pattern": str, "algorithms": ["naive","kmp","rabin_karp"] }` (a non-empty subset).
Response:
```
{
  "results": {
    "<algorithm>": {
      "matches": [int],
      "match_count": int,
      "time_ms": float,
      "comparisons": int
    }
  },
  "kmp_lps": [int] | null,
  "rabin_karp_stats": { "hash_hits": int, "spurious_hits": int } | null,
  "text_length": int,
  "pattern_length": int
}
```
Timing here is a single run per algorithm with `perf_counter_ns`, converted to ms.

### POST /api/similarity
Request: `{ "seq_a": str, "seq_b": str }`
Response:
```
{
  "edit_distance": int,
  "edit_similarity": float,
  "aligned_a": str | null,
  "aligned_b": str | null,
  "operations": [str] | null,
  "lcs_length": int,
  "lcs_sequence": str | null,
  "lcs_similarity": float,
  "alignment_skipped": bool
}
```

### POST /api/benchmark
Request: `{ "pattern_length": int, "text_sizes": [int], "preset": "random" | "worst_case" }`
Response: `{ "preset": str, "series": [ { "text_size": int, "naive": {...}, "kmp": {...}, "rabin_karp": {...} } ] }` where each algorithm object has `time_ms`, `comparisons`, `match_count`.

### POST /api/upload
Multipart file upload (`.fasta`, `.fa`, `.txt`, max 5 MB). Response: `{ "sequence": str, "length": int }` (normalised).

### GET /api/generate?length=N
N between 1 and 1,000,000. Response: `{ "sequence": str }` (random ACGT, unseeded).

### Errors
HTTP 422 with `{ "detail": "<human readable message>" }`.

## Frontend specification
Single page app with 3 tabs. Tailwind for styling. Clean, simple, dark-on-light UI. Show loading and error states on every request.

### Tab 1: Search
- Two inputs: "Text sequence" (textarea plus file upload button plus "Generate random" button with a length field) and "Pattern" (textarea).
- Checkboxes for naive, KMP, Rabin-Karp (all checked by default).
- "Run search" button.
- Results table: algorithm, matches found, time (ms), comparisons.
- Text preview with matches highlighted (only render highlights for the first 5,000 characters of the text, and show a note if truncated).
- Show the KMP LPS array as a row of boxes when KMP ran. Show Rabin-Karp hash hits and spurious hits.

### Tab 2: Similarity
- Two sequence inputs (textarea plus upload for each).
- "Compare" button.
- Score cards: edit distance, edit similarity %, LCS length, LCS similarity %.
- Alignment display in monospace: matches in green, substitutions in amber, gaps in red, with aligned_a on top, a marker row, aligned_b below. Wrap long alignments in horizontally scrollable blocks. If `alignment_skipped`, show a notice instead.
- Show the LCS string if present.

### Tab 3: Benchmark
- Inputs: pattern length (default 10), text sizes (default 1000, 5000, 10000, 50000, 100000), preset dropdown (random or worst case).
- "Run benchmark" button.
- Two Recharts line charts: time (ms) against text size, and comparisons against text size, one line per algorithm.
- A data table below the charts.

## Testing requirements
- `test_search.py`: for 200 random (text, pattern) cases over ACGT, naive, KMP, and Rabin-Karp must return identical match lists, equal to a reference built with a `str.find` loop (reference exists only in the test). Also test: empty-ish edge cases at function level, pattern longer than text returns no matches, `"AAAA"` with `"AA"` returns `[0,1,2]`, and the LPS array for `"ACACAGT"` equals `[0,0,1,2,3,0,0]`.
- `test_edit_distance.py`: `("KITTEN","SITTING") -> 3`, identical strings -> 0, one empty string -> length of the other, aligned strings have equal length, the operations count of non-match items equals the distance.
- `test_lcs.py`: `("AGGTAB","GXTXAYB") -> length 4, sequence "GTAB"`, identical strings -> full length, no common characters -> 0, the returned sequence is a subsequence of both inputs.
- `test_api.py`: each endpoint success case, and a 422 case for invalid characters, empty input, and oversize input.
- Unit tests call algorithm functions directly, so they may use non-DNA letters. Only the API enforces the DNA alphabet.

## Phases
1. Backend algorithms plus unit tests.
2. FastAPI endpoints, schemas, benchmark module, API tests.
3. React frontend.
4. README.md (setup and run instructions for Windows) and ALGORITHMS.md (each algorithm: idea, time and space complexity, a small worked example).

## Definition of done
- `pytest` passes with no failures.
- `npm run build` in `frontend/` succeeds.
- Both servers run with the commands in README.md and the three tabs work end to end.