# Algorithm Notes

The search functions return every matching start position, including overlapping matches. In the descriptions below, `n` and `m` are text and pattern lengths for searching, and are the two input lengths for the dynamic programming algorithms. Space figures mean auxiliary space and exclude the returned matches or alignment.

## 1. Naive matching

**Idea.** Place the pattern at each possible text position. Compare from left to right and stop comparing that position at its first mismatch. A position is reported when all pattern characters match. This naturally keeps overlapping matches.

**Complexity.** Best case is Θ(n − m + 1) when `m ≤ n` and each position mismatches on its first comparison. For independent, uniformly random DNA text and a fixed pattern, the expected work is Θ(n), since most positions fail quickly. Worst case is Θ((n − m + 1)m), or O(nm), when many positions share long prefixes with the pattern. Auxiliary space is O(1).

**Example.** Text `ACGTAC`, pattern `TAC`:

| Start | Window | Comparisons | Result |
|---:|:---:|:---:|:---|
| 0 | ACG | 1 (`A` ≠ `T`) | no match |
| 1 | CGT | 1 (`C` ≠ `T`) | no match |
| 2 | GTA | 1 (`G` ≠ `T`) | no match |
| 3 | TAC | 3 | match at 3 |

The returned match list is `[3]`.

## 2. Knuth–Morris–Pratt (KMP)

**Idea.** Before scanning the text, build an LPS array. At each pattern position, LPS records the length of the longest proper prefix that is also a suffix. When a mismatch occurs, this lets the search retain the prefix information already established instead of moving the text pointer backward. After a full match, the search resumes using the final LPS value, so overlaps are found.

**Complexity.** LPS construction takes Θ(m). The text scan is Θ(n) in the best, average, and worst cases; total time is Θ(n + m) in all cases. Auxiliary space is Θ(m) for the LPS array.

**Example.** For pattern `ACACAGT`, the prefix table is:

| Pattern index | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Character | A | C | A | C | A | G | T |
| LPS | 0 | 0 | 1 | 2 | 3 | 0 | 0 |

So `build_lps("ACACAGT")` returns `[0, 0, 1, 2, 3, 0, 0]`. Searching for this pattern in `ACACACAGT` reports the occurrence at index `2`. When the first attempted alignment reaches `G` in the pattern but finds `A` in the text, LPS allows the search to retain the already matched `ACA` prefix.

## 3. Rabin–Karp

**Idea.** Map `A`, `C`, `G`, `T`, `N` to `0`, `1`, `2`, `3`, `4`, respectively, and hash the pattern and each text window using base 5 modulo 1,000,000,007. A rolling update removes the outgoing character and adds the incoming one. Every equal hash is verified character by character; a hash equality that does not match the characters is counted as a spurious hit.

**Complexity.** Character values are looked up as needed while initializing and updating the hashes, so best and average total running time is Θ(n + m). With few hash hits, expected scan and verification work remains Θ(n + m). In the worst case, many windows may require up to `m` verification comparisons, for O(nm) time. Auxiliary space is O(1), excluding the output list.

**Example.** Text `ACGTAC`, pattern `TAC`. Under the specified mapping, `TAC` is `[3, 0, 1]`, and its base-5 hash is `3·5² + 0·5 + 1 = 76` (the modulus does not change this value). The four text-window hashes are:

| Start | Window | Hash | Verification |
|---:|:---:|---:|:---|
| 0 | ACG | 7 | no hash hit |
| 1 | CGT | 38 | no hash hit |
| 2 | GTA | 65 | no hash hit |
| 3 | TAC | 76 | verified match |

The result is a match at index `3`, one hash hit, and zero spurious hits.

## 4. Levenshtein edit distance

**Idea.** A dynamic programming cell stores the minimum cost of converting one input prefix into another. Deleting or inserting a character costs 1; substituting costs 1; matching equal characters costs 0. The implementation fills the full matrix and traces backward to return an alignment. When traceback choices tie, it prefers diagonal (match or substitution), then delete, then insert. If the product of the input lengths exceeds 25,000,000, it computes only the distance with two rows and marks alignment as skipped.

**Complexity.** The full-matrix path takes Θ(mn) time and Θ(mn) space in best, average, and worst cases. The large-input fallback still takes Θ(mn) time but uses Θ(min(m,n)) auxiliary space. The matrix path also returns the alignment and operations; the fallback returns the distance without them.

**Example.** Converting `CAT` (rows) to `CUT` (columns) gives this full DP matrix:

|   | ∅ | C | U | T |
|:--|--:|--:|--:|--:|
| **∅** | 0 | 1 | 2 | 3 |
| **C** | 1 | 0 | 1 | 2 |
| **A** | 2 | 1 | 1 | 2 |
| **T** | 3 | 2 | 2 | 1 |

The bottom-right value is distance `1`. The alignment is `CAT` / `CUT`, with operations match, substitute, match.

## 5. Longest common subsequence (LCS)

**Idea.** Each dynamic programming cell stores the LCS length for two prefixes. Equal final characters extend the diagonal result by one; otherwise, the cell takes the larger of the value above and the value to the left. Traceback returns one LCS: on a mismatch tie, the implementation moves up. If the product of the lengths exceeds 25,000,000, a two-row calculation returns only the length and skips the sequence.

**Complexity.** The full-matrix path takes Θ(mn) time and Θ(mn) space in best, average, and worst cases. The large-input fallback takes Θ(mn) time and Θ(min(m,n)) auxiliary space.

**Example.** Rows are prefixes of `AGGT`; columns are prefixes of `GXT`:

|   | ∅ | G | X | T |
|:--|--:|--:|--:|--:|
| **∅** | 0 | 0 | 0 | 0 |
| **A** | 0 | 0 | 0 | 0 |
| **G** | 0 | 1 | 1 | 1 |
| **G** | 0 | 1 | 1 | 1 |
| **T** | 0 | 1 | 1 | 2 |

The LCS has length `2`; traceback returns `GT`. Its similarity is `2 × 2 / (4 + 3) = 4/7`.

## Comparison

| Algorithm | Purpose | Best time | Average time | Worst time | Auxiliary space |
|:--|:--|:--|:--|:--|:--|
| Naive matching | Find all occurrences of one pattern | Θ(n − m + 1) | Θ(n) for random text and fixed pattern; data-dependent | Θ(nm) | O(1) |
| KMP | Find all occurrences using prefix reuse | Θ(n + m) | Θ(n + m) | Θ(n + m) | Θ(m) |
| Rabin–Karp | Find occurrences using rolling hashes and verification | Θ(n + m) | Θ(n + m) expected | O(nm) | O(1) |
| Edit distance | Minimum insert, delete, and substitute cost plus alignment | Θ(mn) | Θ(mn) | Θ(mn) | Θ(mn), or Θ(min(m,n)) in the large-input fallback |
| LCS | Recover a longest shared subsequence | Θ(mn) | Θ(mn) | Θ(mn) | Θ(mn), or Θ(min(m,n)) in the large-input fallback |

Here the naive matcher’s average assumes random text over a fixed alphabet and a fixed pattern; the actual comparison count depends on the input. Rabin–Karp’s average bound describes expected verification work when hash hits are sparse. Output storage for returned matches or alignments is not included in auxiliary space.
