"""FastAPI application for DNA searching, similarity, and benchmarks."""

import random
import time
from email import policy
from email.parser import BytesParser

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.algorithms.edit_distance import edit_distance
from app.algorithms.kmp import kmp_search
from app.algorithms.lcs import lcs
from app.algorithms.naive import naive_search
from app.algorithms.rabin_karp import rabin_karp_search
from app.benchmark import run_benchmark
from app.schemas import BenchmarkRequest, SearchRequest, SimilarityRequest
from app.utils import validate_sequence

app = FastAPI(title="DNA Sequence Search and Similarity Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/search")
def search(request: SearchRequest) -> dict:
    text = validate_sequence(request.text, "text")
    pattern = validate_sequence(request.pattern, "pattern")
    results = {}
    lps = None
    rk_stats = None
    matchers = {
        "naive": naive_search,
        "kmp": kmp_search,
        "rabin_karp": rabin_karp_search,
    }
    for algorithm in request.algorithms:
        started = time.perf_counter_ns()
        output = matchers[algorithm](text, pattern)
        elapsed = (time.perf_counter_ns() - started) / 1_000_000
        matches, comparisons = output[0], output[1]
        results[algorithm] = {
            "matches": matches,
            "match_count": len(matches),
            "time_ms": elapsed,
            "comparisons": comparisons,
        }
        if algorithm == "kmp":
            lps = output[2]
        elif algorithm == "rabin_karp":
            rk_stats = {"hash_hits": output[2], "spurious_hits": output[3]}
    return {
        "results": results,
        "kmp_lps": lps,
        "rabin_karp_stats": rk_stats,
        "text_length": len(text),
        "pattern_length": len(pattern),
    }


@app.post("/api/similarity")
def similarity(request: SimilarityRequest) -> dict:
    seq_a = validate_sequence(request.seq_a, "seq_a")
    seq_b = validate_sequence(request.seq_b, "seq_b")
    edit = edit_distance(seq_a, seq_b)
    common = lcs(seq_a, seq_b)
    return {
        "edit_distance": edit["distance"],
        "edit_similarity": edit["similarity"],
        "aligned_a": edit["aligned_a"],
        "aligned_b": edit["aligned_b"],
        "operations": edit["operations"],
        "lcs_length": common["length"],
        "lcs_sequence": common["sequence"],
        "lcs_similarity": common["similarity"],
        "alignment_skipped": edit["alignment_skipped"] or common["alignment_skipped"],
    }


@app.post("/api/benchmark")
def benchmark(request: BenchmarkRequest) -> dict:
    return run_benchmark(request.pattern_length, request.text_sizes, request.preset)


@app.post("/api/upload")
async def upload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")
    if not content_type.lower().startswith("multipart/form-data"):
        raise HTTPException(status_code=422, detail="upload must use multipart/form-data")
    body = await request.body()
    if len(body) > 5 * 1024 * 1024 + 16_384:
        raise HTTPException(status_code=422, detail="upload file must be at most 5 MB")
    message = BytesParser(policy=policy.default).parsebytes(
        b"MIME-Version: 1.0\r\nContent-Type: "
        + content_type.encode("latin-1")
        + b"\r\n\r\n"
        + body
    )
    if not message.is_multipart():
        raise HTTPException(status_code=422, detail="invalid multipart upload")
    file_part = next(
        (part for part in message.iter_parts() if part.get_param("name", header="content-disposition") == "file"),
        None,
    )
    if file_part is None:
        raise HTTPException(status_code=422, detail="multipart field 'file' is required")
    filename = file_part.get_filename() or ""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in {"fasta", "fa", "txt"}:
        raise HTTPException(status_code=422, detail="file must have a .fasta, .fa, or .txt extension")
    payload = file_part.get_payload(decode=True) or b""
    if len(payload) > 5 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="upload file must be at most 5 MB")
    try:
        raw_sequence = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="uploaded file must be UTF-8 text") from None
    sequence = validate_sequence(raw_sequence, "uploaded sequence")
    return {"sequence": sequence, "length": len(sequence)}


@app.get("/api/generate")
def generate(length: int):
    if length < 1 or length > 1_000_000:
        raise HTTPException(status_code=422, detail="length must be between 1 and 1000000")
    rng = random.Random()
    return {"sequence": "".join(rng.choices("ACGT", k=length))}
