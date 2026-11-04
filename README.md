# DNA Sequence Search and Similarity Analyzer

A small DAA lab project for searching DNA patterns, comparing sequences, and benchmarking classic string algorithms. The backend is a FastAPI service with in-memory processing; the frontend is a React workbench with Search, Similarity, and Benchmark tabs. There is no database or authentication.

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer, with npm

## Setup and run on Linux

Run the backend and frontend in separate terminals from the project root.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

The API runs at `http://localhost:8000`. Keep this terminal open while using the frontend.

### Frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal, normally `http://localhost:5173`. Requests to `/api` are proxied to the backend at `http://localhost:8000`.

## Run tests

From the project root:

```bash
cd backend && pytest -v
```

## Using the workbench

- **Pattern search:** Enter or upload a DNA text sequence and a pattern. Choose Naive, KMP, and/or Rabin–Karp, then run the search. You can also generate random text. Results include match counts, timings, and comparisons; the text preview highlights matches. KMP displays its LPS table, and Rabin–Karp displays hash and spurious hit counts.
- **Sequence similarity:** Enter or upload two sequences and choose Compare. The page shows Levenshtein edit distance and similarity, an alignment when available, and the length, string, and similarity of one longest common subsequence.
- **Algorithm benchmark:** Set a pattern length and one or more text sizes, choose Random DNA or Worst case, and run the benchmark. The page plots median runtime and comparison counts for all three search algorithms and shows the underlying values in a table.

The API normalizes FASTA text by removing header lines, whitespace, and lowercase differences. It accepts `A`, `C`, `G`, `T`, and `N`; invalid or empty sequences are rejected.
