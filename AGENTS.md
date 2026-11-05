# AGENTS.md: DNA Sequence Search and Similarity Analyzer

## Project goal

A DAA (Design and Analysis of Algorithms) lab project. A web app that searches for DNA patterns in sequences and measures similarity between sequences, using string algorithms written from scratch, with benchmarks that compare their performance.

## Working rules (read first)

1. Work in phases. Do ONLY the phase requested in the current prompt. Do not start later phases.
2. Do not add features, libraries, files, or pages that are not listed in this document.
3. If something in this document is ambiguous, pick the simplest interpretation, state your assumption in one line, and continue. Do not ask questions unless you are completely blocked.
4. After finishing a phase, run the relevant tests or build, fix failures, then stop and report results briefly.
5. Keep code readable, with short docstrings stating each algorithm's time and space complexity. No unnecessary abstractions.

6\. Phases 1-4 are frozen. New work must be additive: existing endpoints, response keys, and tests must keep working. If a test must change because a contract was extended, make the smallest possible change and report it.

7\. Every phase ends with the FULL test suite passing (`pytest -v` from backend/) and `npm run build` succeeding.



## Tech stack (fixed, do not substitute)

* Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic v2
* Testing: pytest, httpx (for API tests)
* Frontend: React 18 + Vite + TypeScript, Tailwind CSS, Recharts
* Storage: none. Everything is in memory. No database, no auth.
* Ports: backend 8000, frontend 5173. Vite dev server proxies `/api` to `http://localhost:8000`.
* Enable CORS on the backend for `http://localhost:5173`.

## Algorithm rule (critical)

All core algorithms MUST be implemented from scratch in pure Python.
FORBIDDEN inside `backend/app/algorithms/`: `re`, `str.find`, `str.index`, `str.count`, `str.replace`, `in` operator for substring search, `difflib`, `Levenshtein`, `numpy`, `Bio`/Biopython, or any library that performs matching or alignment.
`str.find` and similar are allowed ONLY inside test files, as a reference to verify correctness.

Allowed standard-library helpers in algorithms: `collections.deque`, `math`, `random`, `time`. Nothing else that performs matching or alignment.



## Input rules

* Alphabet: A, C, G, T (N also accepted and treated as an ordinary character).
* Normalisation (in `backend/app/utils.py`): remove FASTA header lines (starting with `>`), strip all whitespace and newlines, convert to uppercase.
* After normalisation, any character outside `ACGTN` returns HTTP 422 with a clear message.
* Empty sequence or empty pattern returns HTTP 422.
* Maximum input length: 2,000,000 characters per sequence. Longer returns HTTP 422.
* Matching indices are 0-based and include overlapping matches.

## Folder structure (create exactly this)

```

dna-analyzer/   <- this is the workspace root, do NOT create another nested folder

&#x20; AGENTS.md

&#x20; README.md

&#x20; ALGORITHMS.md

&#x20; .gitignore

&#x20; backend/

&#x20;   requirements.txt

&#x20;   pytest.ini

&#x20;   app/

&#x20;     \_\_init\_\_.py

&#x20;     main.py

&#x20;     schemas.py

&#x20;     utils.py

&#x20;     benchmark.py

&#x20;     trace.py

&#x20;     dotplot.py

&#x20;     algorithms/

&#x20;       \_\_init\_\_.py

&#x20;       naive.py

&#x20;       kmp.py

&#x20;       rabin\_karp.py

&#x20;       boyer\_moore.py

&#x20;       z\_algorithm.py

&#x20;       edit\_distance.py

&#x20;       lcs.py

&#x20;       alignment.py

&#x20;       hirschberg.py

&#x20;       aho\_corasick.py

&#x20;   tests/

&#x20;     test\_search.py

&#x20;     test\_edit\_distance.py

&#x20;     test\_lcs.py

&#x20;     test\_api.py

&#x20;     test\_boyer\_moore\_z.py

&#x20;     test\_trace.py

&#x20;     test\_alignment.py

&#x20;     test\_hirschberg.py

&#x20;     test\_dotplot.py

&#x20;     test\_revcomp\_aho.py

&#x20; frontend/    <- Vite React TS project

&#x20;   src/

&#x20;     App.tsx

&#x20;     main.tsx

&#x20;     index.css

&#x20;     components/    <- new tabs and shared pieces may be split into files here

```

The workspace root IS the project root. Create `backend/` and `frontend/` directly inside it. Phase 1-4 files already exist and must not be moved or renamed. Only add the files listed above for the current phase.```

The workspace root IS the project root. Create `backend/` and `frontend/` directly inside it.

## Algorithm specifications

### 1\. Naive matching (`naive.py`)

* Slide the pattern over every shift 0..n-m, compare left to right, stop at the first mismatch.
* Time O(n\*m) worst case, space O(1).
* Function: `naive\_search(text, pattern) -> (matches: list\[int], comparisons: int)`
* `comparisons` counts every single character comparison.

### 2\. KMP (`kmp.py`)

* Build the LPS (longest proper prefix which is also suffix) array in O(m).
* Scan the text in O(n) with the text pointer never moving backwards.
* Time O(n+m), space O(m).
* Functions: `build\_lps(pattern) -> list\[int]` and `kmp\_search(text, pattern) -> (matches, comparisons, lps)`
* Must find overlapping matches (after a full match, continue using `lps\[m-1]`).

### 3\. Rabin-Karp (`rabin\_karp.py`)

* Character mapping: A=0, C=1, G=2, T=3, N=4. Base = 5. Modulus q = 1\_000\_000\_007.
* Rolling hash: precompute `base^(m-1) mod q`. Remove the leading character, shift, and add the trailing character. Always use `% q` to keep values non-negative.
* On every hash equality, verify the window character by character. Count a hash hit that fails verification as a spurious hit.
* Time O(n+m) average, O(n\*m) worst case, space O(1).
* Function: `rabin\_karp\_search(text, pattern) -> (matches, comparisons, hash\_hits, spurious\_hits)`
* `comparisons` counts hash window updates plus verification character comparisons.

### 4\. Edit distance (`edit\_distance.py`)

* Levenshtein distance. Insert = 1, delete = 1, substitute = 1, match = 0.
* Full (m+1) x (n+1) DP matrix, then traceback from (m, n) to (0, 0).
* Traceback priority when costs tie: diagonal (match or substitute), then delete, then insert.
* Returns: `distance`, `aligned\_a` and `aligned\_b` (strings with `-` for gaps, equal length), `operations` (list of "match" | "substitute" | "insert" | "delete", same length as the aligned strings).
* Similarity = `1 - distance / max(m, n)`, as a float from 0 to 1.
* Time O(m*n), space O(m*n).
* Large input fallback: if `m \* n > 25\_000\_000`, use the two-row space-optimised version, return only `distance`, set alignment fields to `null`, and set `alignment\_skipped = true`.
* Function: `edit\_distance(a, b) -> dict`

### 5\. LCS (`lcs.py`)

* Classic DP matrix with traceback to recover ONE actual longest common subsequence string.
* Traceback tie rule: on a match go diagonal; otherwise move up if `dp\[i-1]\[j] >= dp\[i]\[j-1]`, else left.
* Similarity = `2 \* lcs\_length / (m + n)`, as a float from 0 to 1.
* Time O(m*n), space O(m*n). Same large input fallback as edit distance (length only, `lcs` string = `null`, `alignment\_skipped = true`).
* Function: `lcs(a, b) -> dict` with `length`, `sequence`, `similarity`, `alignment\_skipped`.

### 6\. Benchmark (`benchmark.py`)

* Use `time.perf\_counter\_ns`. For each algorithm run 5 times and report the MEDIAN time in milliseconds.
* Random text: generated with `random.Random(42)` over `ACGT`, so results are reproducible.
* Pattern: taken as a slice of the generated text at its middle, so at least one match exists. Length = `pattern\_length`.
* Preset `"worst\_case"`: text = `"A" \* size`, pattern = `"A" \* (pattern\_length - 1) + "C"`.
* For each text size returns, per algorithm (naive, kmp, rabin\_karp): `time\_ms`, `comparisons`, `match\_count`.
* Limits: text\_sizes values max 200,000. Max 8 sizes per request. pattern\_length between 2 and 1,000.

## API contract (fixed, do not rename)

All endpoints under `/api`, JSON in and out.

### POST /api/search

Request: `{ "text": str, "pattern": str, "algorithms": \["naive","kmp","rabin\_karp"] }` (a non-empty subset).
Response:

```
{
  "results": {
    "<algorithm>": {
      "matches": \[int],
      "match\_count": int,
      "time\_ms": float,
      "comparisons": int
    }
  },
  "kmp\_lps": \[int] | null,
  "rabin\_karp\_stats": { "hash\_hits": int, "spurious\_hits": int } | null,
  "text\_length": int,
  "pattern\_length": int
}
```

Timing here is a single run per algorithm with `perf\_counter\_ns`, converted to ms.

### POST /api/similarity

Request: `{ "seq\_a": str, "seq\_b": str }`
Response:

```
{
  "edit\_distance": int,
  "edit\_similarity": float,
  "aligned\_a": str | null,
  "aligned\_b": str | null,
  "operations": \[str] | null,
  "lcs\_length": int,
  "lcs\_sequence": str | null,
  "lcs\_similarity": float,
  "alignment\_skipped": bool
}
```

### POST /api/benchmark

Request: `{ "pattern\_length": int, "text\_sizes": \[int], "preset": "random" | "worst\_case" }`
Response: `{ "preset": str, "series": \[ { "text\_size": int, "naive": {...}, "kmp": {...}, "rabin\_karp": {...} } ] }` where each algorithm object has `time\_ms`, `comparisons`, `match\_count`.

### POST /api/upload

Multipart file upload (`.fasta`, `.fa`, `.txt`, max 5 MB). Response: `{ "sequence": str, "length": int }` (normalised).

### GET /api/generate?length=N

N between 1 and 1,000,000. Response: `{ "sequence": str }` (random ACGT, unseeded).

### Errors

HTTP 422 with `{ "detail": "<human readable message>" }`.

## Frontend specification

Single page app with 3 tabs. Tailwind for styling. Clean, simple, dark-on-light UI. Show loading and error states on every request.

### Tab 1: Search

* Two inputs: "Text sequence" (textarea plus file upload button plus "Generate random" button with a length field) and "Pattern" (textarea).
* Checkboxes for naive, KMP, Rabin-Karp (all checked by default).
* "Run search" button.
* Results table: algorithm, matches found, time (ms), comparisons.
* Text preview with matches highlighted (only render highlights for the first 5,000 characters of the text, and show a note if truncated).
* Show the KMP LPS array as a row of boxes when KMP ran. Show Rabin-Karp hash hits and spurious hits.

### Tab 2: Similarity

* Two sequence inputs (textarea plus upload for each).
* "Compare" button.
* Score cards: edit distance, edit similarity %, LCS length, LCS similarity %.
* Alignment display in monospace: matches in green, substitutions in amber, gaps in red, with aligned\_a on top, a marker row, aligned\_b below. Wrap long alignments in horizontally scrollable blocks. If `alignment\_skipped`, show a notice instead.
* Show the LCS string if present.

### Tab 3: Benchmark

* Inputs: pattern length (default 10), text sizes (default 1000, 5000, 10000, 50000, 100000), preset dropdown (random or worst case).
* "Run benchmark" button.
* Two Recharts line charts: time (ms) against text size, and comparisons against text size, one line per algorithm.
* A data table below the charts.

## Testing requirements

* `test\_search.py`: for 200 random (text, pattern) cases over ACGT, naive, KMP, and Rabin-Karp must return identical match lists, equal to a reference built with a `str.find` loop (reference exists only in the test). Also test: empty-ish edge cases at function level, pattern longer than text returns no matches, `"AAAA"` with `"AA"` returns `\[0,1,2]`, and the LPS array for `"ACACAGT"` equals `\[0,0,1,2,3,0,0]`.
* `test\_edit\_distance.py`: `("KITTEN","SITTING") -> 3`, identical strings -> 0, one empty string -> length of the other, aligned strings have equal length, the operations count of non-match items equals the distance.
* `test\_lcs.py`: `("AGGTAB","GXTXAYB") -> length 4, sequence "GTAB"`, identical strings -> full length, no common characters -> 0, the returned sequence is a subsequence of both inputs.
* `test\_api.py`: each endpoint success case, and a 422 case for invalid characters, empty input, and oversize input.
* Unit tests call algorithm functions directly, so they may use non-DNA letters. Only the API enforces the DNA alphabet.

## Phases

1. Backend algorithms plus unit tests.
2. FastAPI endpoints, schemas, benchmark module, API tests.
3. React frontend.
4. README.md (setup and run instructions for Windows) and ALGORITHMS.md (each algorithm: idea, time and space complexity, a small worked example).
5. &#x20;Boyer-Moore, Z-algorithm, step-by-step visualizer (backend + frontend)
6. &#x20;Global/local alignment with affine gaps, Hirschberg, dot plot (backend + frontend)
7. &#x20;Reverse complement, both-strand search, Aho-Corasick (backend + frontend)

## Definition of done

* all tests pass, with no fixed count
* `npm run build` in `frontend/` succeeds.
* Both servers run with the commands in README.md and the three tabs work end to end.



\---



\# EXTENSION PHASES 5-7



\## Phase 5: Boyer-Moore, Z-algorithm, Visualizer



\### Boyer-Moore (`boyer\_moore.py`)

\- Implement BOTH the bad-character rule (last-occurrence dict) and the strong good-suffix rule. Scan the pattern right to left.

\- After a full match, shift by the good-suffix shift for a full match (m minus the longest border of the pattern). This keeps overlapping matches.

\- Time: O(n/m) best case, O(n\*m) worst case (no Galil rule). Space O(m + alphabet).

\- Function: `boyer\_moore\_search(text, pattern) -> (matches, comparisons)`. `comparisons` counts every text-versus-pattern character comparison.



\### Z-algorithm (`z\_algorithm.py`)

\- Build `s = pattern + "$" + text`, compute the Z array with the standard Z-box method, and report a match where `z\[k] == m` at position `k - m - 1`. The `$` separator is added internally and never appears in inputs.

\- Time O(n+m), space O(n+m).

\- Function: `z\_search(text, pattern) -> (matches, comparisons, z\_pattern)`. `z\_pattern` is the Z array of the pattern part only (first m values). `comparisons` counts each character equality test made while extending Z values.



\### API changes (additive)

\- `/api/search`: the `algorithms` list now also accepts `"boyer\_moore"` and `"z\_algorithm"`. Result objects have the same shape as the other algorithms. Add optional `"z\_array": \[int] | null` at the top level, set only when z\_algorithm ran.

\- `/api/benchmark`: each series item now also includes `boyer\_moore` and `z\_algorithm` objects (`time\_ms`, `comparisons`, `match\_count`). The benchmark always runs all five.

\- Frontend: add both algorithms to the Search checkboxes (all five checked by default) and add their lines to both benchmark charts and the table.



\### Visualizer API (`trace.py`)

`POST /api/trace` with body `{ "algorithm": "naive"|"kmp"|"rabin\_karp"|"edit\_distance", ... }`.



\*\*Search algorithms:\*\* body `{ "algorithm", "text", "pattern" }`. Limits: text <= 300 chars, pattern <= 30 chars, steps <= 5000 (else 422). Response:

```

{ "algorithm": str, "text": str, "pattern": str, "matches": \[int],

&#x20; "lps": \[int] | null,            // kmp only

&#x20; "steps": \[ ... ] }

```

Step types (all include `"type"`):

\- naive: `{"type":"compare","shift":s,"pattern\_index":j,"text\_index":s+j,"result":"match"|"mismatch"}` and `{"type":"match\_found","shift":s}`

\- kmp: `{"type":"compare","text\_index":i,"pattern\_index":j,"result":"match"|"mismatch"}`, `{"type":"fallback","from":j,"to":k}` (emitted after a mismatch with j>0, and after a full match where from=m), and `{"type":"match\_found","shift":i-m+1}`

\- rabin\_karp: `{"type":"hash","shift":s,"window\_hash":int,"pattern\_hash":int,"equal":bool}`; when equal, `{"type":"verify","shift":s,"result":"match"|"spurious"}`; for a true match also `{"type":"match\_found","shift":s}`



\*\*Edit distance:\*\* body `{ "algorithm":"edit\_distance", "seq\_a", "seq\_b" }`, each <= 40 chars. Response:

```

{ "seq\_a": str, "seq\_b": str, "distance": int, "matrix": \[\[int]],

&#x20; "cells": \[ {"i":int,"j":int,"value":int,"source":"init"|"match"|"substitute"|"delete"|"insert"} ],

&#x20; "traceback": \[\[i,j], ...] }      // from (m,n) down to (0,0)

```

`cells` lists every cell in row-major order, including row 0 and column 0 (source "init"). When costs tie, `source` uses the same priority as the traceback: diagonal, then delete, then insert.



\*\*Implementation rule:\*\* the trace functions are separate step-recording versions in `trace.py`. Tests must assert that, on 100 random cases, the trace's `matches` equals the real algorithm's matches and the trace's `distance` equals the real edit distance.



\### Visualizer frontend: new 4th tab "Visualizer"

\- Controls: algorithm dropdown, input fields (with defaults `ACACACAGT` / `ACACAG` for search and `KITTEN`-style DNA strings for edit distance), Load button.

\- Playback: Play/Pause, Step forward, Step back, Reset, speed slider.

\- Search view: text on one row, pattern on a second row aligned at the current shift. Colour compared characters green (match) or red (mismatch), and show the current step's explanation in one sentence. For KMP show the LPS array with the current fallback highlighted. For Rabin-Karp show window hash against pattern hash.

\- Edit-distance view: the matrix filling cell by cell in `cells` order, the current cell highlighted, and at the end the traceback path highlighted.



\### Phase 5 tests

\- Boyer-Moore and Z must match the `str.find` reference on 200 random cases (reuse the existing reference approach), plus `"AAAA"`/`"AA"` -> `\[0,1,2]`.

\- Z array for pattern `"ACACAGT"` equals `\[7,0,3,0,1,0,0]` (the first entry equals the pattern length by convention).

\- Trace tests as described above, plus a 422 test for oversize input.



\## Phase 6: Alignment, Hirschberg, Dot plot



\### Scoring parameters (all in the request, with defaults)

`match=2`, `mismatch=-1`, `gap\_open=3`, `gap\_extend=1` (positive numbers that are SUBTRACTED). A gap of length k costs `gap\_open + (k-1)\*gap\_extend`. If `gap\_open == gap\_extend` this is a linear gap penalty. Use `NEG = -10\*\*9` as minus infinity (integers only).



\### Global alignment (Needleman-Wunsch with affine gaps, Gotoh) in `alignment.py`

Three matrices M, X, Y of size (m+1) x (n+1), where s(x,y) = match if x==y else mismatch:

```

M\[i]\[j] = s(a\_i,b\_j) + max(M\[i-1]\[j-1], X\[i-1]\[j-1], Y\[i-1]\[j-1])

X\[i]\[j] = max(M\[i-1]\[j] - gap\_open, X\[i-1]\[j] - gap\_extend, Y\[i-1]\[j] - gap\_open)   # a\_i against a gap

Y\[i]\[j] = max(M\[i]\[j-1] - gap\_open, Y\[i]\[j-1] - gap\_extend, X\[i]\[j-1] - gap\_open)   # b\_j against a gap

```

Initialisation: `M\[0]\[0]=0`; `X\[0]\[0]=Y\[0]\[0]=NEG`; for i>0: `M\[i]\[0]=NEG, Y\[i]\[0]=NEG, X\[i]\[0]= -gap\_open-(i-1)\*gap\_extend`; for j>0: `M\[0]\[j]=NEG, X\[0]\[j]=NEG, Y\[0]\[j]= -gap\_open-(j-1)\*gap\_extend`. Score = max of the three at (m,n). Traceback starts in the best state at (m,n); on ties prefer M, then X, then Y.



\### Local alignment (Smith-Waterman, affine) in `alignment.py`

Same X and Y recurrences. M restarts at zero: `M\[i]\[j] = s(a\_i,b\_j) + max(0, M\[i-1]\[j-1], X\[i-1]\[j-1], Y\[i-1]\[j-1])`. Boundary rows and columns are NEG for X and Y and 0 for M. Score = the maximum M cell anywhere (first one in row-major order on ties). Traceback runs from that cell until the "0" restart is chosen. Return the aligned segments only, plus 0-based start and end indices in each sequence.



\### Hirschberg (`hirschberg.py`)

Linear-space global alignment with LINEAR gaps only. It requires `gap\_open == gap\_extend`, else HTTP 422. Use the standard divide-and-conquer: forward and backward score rows, split the middle of `a`, recurse. Its score must equal the Gotoh global score for the same linear parameters.



\### Function signatures

\- `global\_align(a, b, match, mismatch, gap\_open, gap\_extend) -> dict`

\- `local\_align(a, b, match, mismatch, gap\_open, gap\_extend) -> dict`

\- `hirschberg\_align(a, b, match, mismatch, gap) -> dict`



All return `score`, `aligned\_a`, `aligned\_b`, `operations` ("match"|"mismatch"|"insert"|"delete", where "insert" means a gap in a and "delete" means a gap in b), `identity` (matches divided by alignment length, 0-1 float), and for local also `a\_start`, `a\_end`, `b\_start`, `b\_end`.



\### Endpoint

`POST /api/align` body `{ "seq\_a", "seq\_b", "mode":"global"|"local", "method":"full"|"hirschberg", "match":2, "mismatch":-1, "gap\_open":3, "gap\_extend":1 }`.

\- `method:"hirschberg"` is valid only with `mode:"global"` and `gap\_open == gap\_extend`, else 422.

\- Limits: `m\*n <= 4,000,000` for `full`; each sequence <= 3,000 chars for `hirschberg`. Else 422.

\- Response: the dict above plus `mode`, `method`.



\### Dot plot (`dotplot.py`)

`POST /api/dotplot` body `{ "seq\_a", "seq\_b", "window":1, "threshold":1 }`. Each sequence <= 1,000 chars, `window` 1..20, `threshold` 1..window. Mark cell (i,j) when at least `threshold` of the `window` characters on the diagonal starting at (i,j) match. Compute with diagonal running sums so time is O(m\*n), independent of `window`. Response: `{ "rows": m-window+1, "cols": n-window+1, "points": \[\[i,j],...] }`. If points exceed 200,000, return 422 suggesting a larger window or threshold.



\### Frontend: new 5th tab "Alignment"

\- Inputs: two sequences (textarea plus upload each), mode (global/local), method (full/hirschberg), the four scoring fields. When "hirschberg" is chosen, set gap\_extend equal to gap\_open automatically and show a note.

\- Output: score card, identity %, alignment in the same colour-coded monospace style as the Similarity tab (gaps red, mismatches amber, matches green), and the local start/end positions.

\- Dot plot section on the same tab: window and threshold inputs and a `<canvas>` render (one pixel block per point, scaled to fit, with axis labels showing the sequence lengths). Diagonals indicate similarity or repeats.



\### Phase 6 tests

\- `("GATTACA","GCATGCU")`-style classic values must not be used with the DNA validator, so call the functions directly. Known case: global linear gaps with match=1, mismatch=-1, gap\_open=gap\_extend=1 on `"GATTACA"` against `"GCATGCA"` has score 0 (verify by the Needleman-Wunsch recurrence in the test by an independent simple O(mn) linear-gap implementation written inside the test).

\- Property tests on 100 random pairs: affine global score with `gap\_open==gap\_extend` equals the independent linear implementation; Hirschberg's alignment re-scored from its aligned strings equals the full global score; aligned strings have equal length and removing "-" recovers the originals; local score >= 0 and local alignment segments are substrings of the inputs.

\- Dot plot: identical sequences give the full main diagonal; a 422 case for oversize input.



\## Phase 7: Reverse complement, Both-strand search, Aho-Corasick



\### Reverse complement (`utils.py`)

`reverse\_complement(seq)`: A<->T, C<->G, N->N, then reverse. Endpoint `POST /api/revcomp` body `{ "sequence" }` returns `{ "sequence", "reverse\_complement" }`.



\### Both-strand search (additive on `/api/search`)

New optional request field `"both\_strands": bool` (default false). When true, each algorithm's result also includes `"reverse\_matches": \[int]`: the forward-strand start positions of occurrences of the reverse complement of the pattern. When false, `reverse\_matches` is `null`. Run each selected algorithm on the reverse-complemented pattern for this.



\### Aho-Corasick (`aho\_corasick.py`)

\- Build a trie (dict of dicts), BFS failure links (`collections.deque`), and dictionary-suffix (output) links so that all overlapping matches of all patterns are reported.

\- Time O(n + total pattern length + z) where z is the number of matches; space O(total pattern length \* alphabet).

\- Function: `aho\_corasick\_search(text, patterns) -> (matches: list\[tuple\[int,int]], comparisons: int, node\_count: int)` where each match is `(start, pattern\_index)`, sorted by start then pattern\_index. `comparisons` counts transitions followed (including failure-link moves).

\- Endpoint: `POST /api/multisearch` body `{ "text", "patterns": \[str] }` with 1-100 patterns of length 1-100, duplicates removed preserving order. Response: `{ "matches": \[{"pattern":str,"start":int}], "counts": {"<pattern>": int}, "node\_count": int, "comparisons": int }`.



\### Frontend

\- Search tab: add a "Search both strands" checkbox; show forward and reverse matches in different highlight colours.

\- Search tab: new "Multi-pattern search" section with a textarea (one pattern per line), a Run button, a table of counts per pattern, and highlights in the text preview (first 5,000 chars only).



\### Phase 7 tests

\- Aho-Corasick must match a `str.find`-loop reference over every pattern on 200 random cases (patterns of length 1-6 including repeats and substrings of each other).

\- Classic case: patterns `\["A","AB","BAB","BC","BCA","C","CAA"]` on text `"ABCCABAB"` checked against the reference, calling the function directly.

\- `reverse\_complement("AACGT") == "ACGTT"`; reverse\_complement applied twice returns the original.

\- `both\_strands` API test where the pattern's reverse complement occurs in the text.

