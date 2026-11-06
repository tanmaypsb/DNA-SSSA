"""FastAPI application for DNA searching, similarity, and benchmarks."""

import random
import time
from email import policy
from email.parser import BytesParser

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.algorithms.edit_distance import edit_distance
from app.algorithms.boyer_moore import boyer_moore_search
from app.algorithms.alignment import global_align, local_align
from app.algorithms.aho_corasick import aho_corasick_search
from app.algorithms.hirschberg import hirschberg_align
from app.algorithms.kmp import kmp_search
from app.algorithms.lcs import lcs
from app.algorithms.naive import naive_search
from app.algorithms.rabin_karp import rabin_karp_search
from app.algorithms.z_algorithm import z_search
from app.benchmark import run_benchmark
from app.schemas import AlignmentRequest, BenchmarkRequest, DotplotRequest, MultiSearchRequest, ReverseComplementRequest, SearchRequest, SimilarityRequest
from app.trace import trace_edit_distance, trace_search
from app.dotplot import compute_dotplot
from app.utils import reverse_complement, validate_sequence

app = FastAPI(title="DNA Sequence Search and Similarity Analyzer")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", 
                   "https://dna-sssa.pages.dev",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/search")
def search(request: SearchRequest) -> dict:
    text = validate_sequence(request.text, "text")
    pattern = validate_sequence(request.pattern, "pattern")
    reverse_pattern = reverse_complement(pattern) if request.both_strands else None
    results = {}
    lps = None
    rk_stats = None
    z_array = None
    matchers = {
        "naive": naive_search,
        "kmp": kmp_search,
        "rabin_karp": rabin_karp_search,
        "boyer_moore": boyer_moore_search,
        "z_algorithm": z_search,
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
            "reverse_matches": matchers[algorithm](text, reverse_pattern)[0] if reverse_pattern is not None else None,
        }
        if algorithm == "kmp":
            lps = output[2]
        elif algorithm == "rabin_karp":
            rk_stats = {"hash_hits": output[2], "spurious_hits": output[3]}
        elif algorithm == "z_algorithm":
            z_array = output[2]
    return {
        "results": results,
        "kmp_lps": lps,
        "rabin_karp_stats": rk_stats,
        "z_array": z_array,
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


@app.post("/api/trace")
def trace(payload: dict) -> dict:
    algorithm = payload.get("algorithm")
    if algorithm in {"naive", "kmp", "rabin_karp"}:
        raw_text = payload.get("text")
        raw_pattern = payload.get("pattern")
        if not isinstance(raw_text, str) or not isinstance(raw_pattern, str):
            raise HTTPException(status_code=422, detail="text and pattern must be strings")
        text = validate_sequence(raw_text, "text")
        pattern = validate_sequence(raw_pattern, "pattern")
        if len(text) > 300 or len(pattern) > 30:
            raise HTTPException(status_code=422, detail="trace search limits are 300 text and 30 pattern characters")
        result = trace_search(algorithm, text, pattern)
        if len(result["steps"]) > 5000:
            raise HTTPException(status_code=422, detail="trace exceeds the 5000 step limit")
        return result

    if algorithm == "edit_distance":
        raw_a = payload.get("seq_a")
        raw_b = payload.get("seq_b")
        if not isinstance(raw_a, str) or not isinstance(raw_b, str):
            raise HTTPException(status_code=422, detail="seq_a and seq_b must be strings")
        seq_a = validate_sequence(raw_a, "seq_a")
        seq_b = validate_sequence(raw_b, "seq_b")
        if len(seq_a) > 40 or len(seq_b) > 40:
            raise HTTPException(status_code=422, detail="trace edit-distance inputs must be at most 40 characters each")
        return trace_edit_distance(seq_a, seq_b)

    raise HTTPException(status_code=422, detail="algorithm must be naive, kmp, rabin_karp, or edit_distance")


@app.post("/api/align")
def align(request: AlignmentRequest) -> dict:
    seq_a = validate_sequence(request.seq_a, "seq_a")
    seq_b = validate_sequence(request.seq_b, "seq_b")
    m, n = len(seq_a), len(seq_b)
    if request.method == "full" and m * n > 4_000_000:
        raise HTTPException(status_code=422, detail="full alignment requires sequence length product at most 4000000")
    if request.method == "hirschberg" and (m > 3_000 or n > 3_000):
        raise HTTPException(status_code=422, detail="Hirschberg inputs must each be at most 3000 characters")

    if request.method == "hirschberg":
        result = hirschberg_align(seq_a, seq_b, request.match, request.mismatch, request.gap_open)
    elif request.mode == "global":
        result = global_align(seq_a, seq_b, request.match, request.mismatch, request.gap_open, request.gap_extend)
    else:
        result = local_align(seq_a, seq_b, request.match, request.mismatch, request.gap_open, request.gap_extend)
    return {**result, "mode": request.mode, "method": request.method}


@app.post("/api/dotplot")
def dotplot(request: DotplotRequest) -> dict:
    seq_a = validate_sequence(request.seq_a, "seq_a")
    seq_b = validate_sequence(request.seq_b, "seq_b")
    if len(seq_a) > 1_000 or len(seq_b) > 1_000:
        raise HTTPException(status_code=422, detail="dot plot sequences must each be at most 1000 characters")
    if request.window > min(len(seq_a), len(seq_b)):
        raise HTTPException(status_code=422, detail="window must not exceed either sequence length")
    try:
        return compute_dotplot(seq_a, seq_b, request.window, request.threshold)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


@app.post("/api/revcomp")
def revcomp(request: ReverseComplementRequest) -> dict:
    sequence = validate_sequence(request.sequence, "sequence")
    return {"sequence": sequence, "reverse_complement": reverse_complement(sequence)}


@app.post("/api/multisearch")
def multisearch(request: MultiSearchRequest) -> dict:
    text = validate_sequence(request.text, "text")
    if len(request.patterns) < 1 or len(request.patterns) > 100:
        raise HTTPException(status_code=422, detail="patterns must contain between 1 and 100 entries")

    patterns = []
    seen = set()
    for raw_pattern in request.patterns:
        pattern = validate_sequence(raw_pattern, "pattern")
        if len(pattern) > 100:
            raise HTTPException(status_code=422, detail="patterns must each be at most 100 characters")
        if pattern not in seen:
            patterns.append(pattern)
            seen.add(pattern)

    indexed_matches, comparisons, node_count = aho_corasick_search(text, patterns)
    counts = {pattern: 0 for pattern in patterns}
    matches = []
    for start, pattern_index in indexed_matches:
        pattern = patterns[pattern_index]
        matches.append({"pattern": pattern, "start": start})
        counts[pattern] += 1
    return {"matches": matches, "counts": counts, "node_count": node_count, "comparisons": comparisons}
