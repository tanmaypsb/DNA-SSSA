import { useEffect, useMemo, useRef, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type Tab = 'search' | 'similarity' | 'benchmark' | 'visualizer' | 'alignment'
type Algorithm = 'naive' | 'kmp' | 'rabin_karp' | 'boyer_moore' | 'z_algorithm'
type SearchResult = { matches: number[]; match_count: number; time_ms: number; comparisons: number; reverse_matches: number[] | null }
type SearchResponse = {
  results: Partial<Record<Algorithm, SearchResult>>
  kmp_lps: number[] | null
  rabin_karp_stats: { hash_hits: number; spurious_hits: number } | null
  z_array: number[] | null
  text_length: number
  pattern_length: number
}
type SimilarityResponse = {
  edit_distance: number
  edit_similarity: number
  aligned_a: string | null
  aligned_b: string | null
  operations: ('match' | 'substitute' | 'insert' | 'delete')[] | null
  lcs_length: number
  lcs_sequence: string | null
  lcs_similarity: number
  alignment_skipped: boolean
}
type BenchmarkItem = { time_ms: number; comparisons: number; match_count: number }
type BenchmarkRow = { text_size: number } & Record<Algorithm, BenchmarkItem>
type BenchmarkResponse = { preset: string; series: BenchmarkRow[] }
type TraceSearch = { algorithm: string; text: string; pattern: string; matches: number[]; lps: number[] | null; steps: Record<string, unknown>[] }
type TraceCell = { i: number; j: number; value: number; source: string }
type TraceEdit = { seq_a: string; seq_b: string; distance: number; matrix: number[][]; cells: TraceCell[]; traceback: [number, number][] }
type TraceResponse = TraceSearch | TraceEdit
type AlignResponse = { score: number; aligned_a: string; aligned_b: string; operations: ('match' | 'mismatch' | 'insert' | 'delete')[]; identity: number; a_start?: number; a_end?: number; b_start?: number; b_end?: number; mode: 'global' | 'local'; method: 'full' | 'hirschberg' }
type DotplotResponse = { rows: number; cols: number; points: [number, number][] }
type MultiSearchResponse = { matches: { pattern: string; start: number }[]; counts: Record<string, number>; node_count: number; comparisons: number }

const algorithms: { id: Algorithm; label: string; color: string }[] = [
  { id: 'naive', label: 'Naive', color: '#d18a4b' },
  { id: 'kmp', label: 'KMP', color: '#4d8564' },
  { id: 'rabin_karp', label: 'Rabin–Karp', color: '#7880c5' },
  { id: 'boyer_moore', label: 'Boyer–Moore', color: '#c25764' },
  { id: 'z_algorithm', label: 'Z-algorithm', color: '#308c9a' },
]

async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
  const response = await fetch(`${API_BASE_URL}${url}`, init)
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = body && typeof body.detail === 'string' ? body.detail : `Request failed (${response.status})`
    throw new Error(detail)
  }
  return body as T
}

function App() {
  const [tab, setTab] = useState<Tab>('search')
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [text, setText] = useState('ATGCGATACGCTTACG')
  const [pattern, setPattern] = useState('GCT')
  const [selected, setSelected] = useState<Algorithm[]>(['naive', 'kmp', 'rabin_karp', 'boyer_moore', 'z_algorithm'])
  const [bothStrands, setBothStrands] = useState(false)
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null)
  const [multiPatterns, setMultiPatterns] = useState('ACG\nCGT')
  const [multiResult, setMultiResult] = useState<MultiSearchResponse | null>(null)
  const [generateLength, setGenerateLength] = useState('1000')
  const [seqA, setSeqA] = useState('ACGTACGT')
  const [seqB, setSeqB] = useState('ACGTCGT')
  const [similarity, setSimilarity] = useState<SimilarityResponse | null>(null)
  const [patternLength, setPatternLength] = useState('10')
  const [textSizes, setTextSizes] = useState('1000, 5000, 10000, 50000, 100000')
  const [preset, setPreset] = useState<'random' | 'worst_case'>('random')
  const [benchmark, setBenchmark] = useState<BenchmarkResponse | null>(null)
  const [traceAlgorithm, setTraceAlgorithm] = useState<'naive' | 'kmp' | 'rabin_karp' | 'edit_distance'>('naive')
  const [traceText, setTraceText] = useState('ACACACAGT')
  const [tracePattern, setTracePattern] = useState('ACACAG')
  const [traceA, setTraceA] = useState('ACGTAC')
  const [traceB, setTraceB] = useState('AGTAC')
  const [traceResult, setTraceResult] = useState<TraceResponse | null>(null)
  const [traceCursor, setTraceCursor] = useState(-1)
  const [tracePlaying, setTracePlaying] = useState(false)
  const [traceSpeed, setTraceSpeed] = useState(650)
  const [alignA, setAlignA] = useState('ACGTAC')
  const [alignB, setAlignB] = useState('AGTAC')
  const [alignMode, setAlignMode] = useState<'global' | 'local'>('global')
  const [alignMethod, setAlignMethod] = useState<'full' | 'hirschberg'>('full')
  const [matchScore, setMatchScore] = useState('2')
  const [mismatchScore, setMismatchScore] = useState('-1')
  const [gapOpen, setGapOpen] = useState('3')
  const [gapExtend, setGapExtend] = useState('1')
  const [alignResult, setAlignResult] = useState<AlignResponse | null>(null)
  const [dotWindow, setDotWindow] = useState('1')
  const [dotThreshold, setDotThreshold] = useState('1')
  const [dotplotResult, setDotplotResult] = useState<DotplotResponse | null>(null)

  async function run<T>(key: string, action: () => Promise<T>, done: (value: T) => void) {
    setLoading((current) => ({ ...current, [key]: true }))
    setErrors((current) => ({ ...current, [key]: '' }))
    try {
      done(await action())
    } catch (error) {
      setErrors((current) => ({ ...current, [key]: error instanceof Error ? error.message : 'Something went wrong' }))
    } finally {
      setLoading((current) => ({ ...current, [key]: false }))
    }
  }

  function uploadFile(file: File, key: string, onSequence: (sequence: string) => void) {
    const form = new FormData()
    form.append('file', file)
    void run(key, () => api<{ sequence: string; length: number }>('/api/upload', { method: 'POST', body: form }), (data) => onSequence(data.sequence))
  }

  function executeSearch() {
    void run('search', () => api<SearchResponse>('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, pattern, algorithms: selected, both_strands: bothStrands }),
    }), setSearchResult)
  }

  function executeMultiSearch() {
    const patterns = multiPatterns.split(/\r?\n/).map((item) => item.trim()).filter(Boolean)
    void run('multisearch', () => api<MultiSearchResponse>('/api/multisearch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, patterns }),
    }), setMultiResult)
  }

  function generateSequence() {
    const length = Number(generateLength)
    void run('generate', () => api<{ sequence: string }>(`/api/generate?length=${encodeURIComponent(String(length))}`), (data) => {
      setText(data.sequence)
      setSearchResult(null)
      setMultiResult(null)
    })
  }

  function compareSequences() {
    void run('similarity', () => api<SimilarityResponse>('/api/similarity', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seq_a: seqA, seq_b: seqB }),
    }), setSimilarity)
  }

  function executeBenchmark() {
    const sizes = textSizes.split(/[\s,]+/).filter(Boolean).map(Number)
    void run('benchmark', () => api<BenchmarkResponse>('/api/benchmark', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pattern_length: Number(patternLength), text_sizes: sizes, preset }),
    }), setBenchmark)
  }

  function loadTrace() {
    const payload = traceAlgorithm === 'edit_distance'
      ? { algorithm: traceAlgorithm, seq_a: traceA, seq_b: traceB }
      : { algorithm: traceAlgorithm, text: traceText, pattern: tracePattern }
    void run('trace', () => api<TraceResponse>('/api/trace', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }), (data) => {
      setTraceResult(data)
      setTraceCursor(-1)
      setTracePlaying(false)
    })
  }

  function runAlignment() {
    void run('alignment', () => api<AlignResponse>('/api/align', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        seq_a: alignA, seq_b: alignB, mode: alignMode, method: alignMethod,
        match: Number(matchScore), mismatch: Number(mismatchScore),
        gap_open: Number(gapOpen), gap_extend: Number(gapExtend),
      }),
    }), setAlignResult)
  }

  function runDotplot() {
    void run('dotplot', () => api<DotplotResponse>('/api/dotplot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ seq_a: alignA, seq_b: alignB, window: Number(dotWindow), threshold: Number(dotThreshold) }),
    }), setDotplotResult)
  }

  const traceSteps = traceResult && 'steps' in traceResult ? traceResult.steps : traceResult?.cells ?? []
  useEffect(() => {
    if (!tracePlaying) return
    const timer = window.setInterval(() => {
      setTraceCursor((current) => Math.min(traceSteps.length - 1, current + 1))
    }, traceSpeed)
    return () => window.clearInterval(timer)
  }, [tracePlaying, traceSteps.length, traceSpeed])
  useEffect(() => {
    if (tracePlaying && traceCursor >= 0 && traceCursor >= traceSteps.length - 1) setTracePlaying(false)
  }, [tracePlaying, traceCursor, traceSteps.length])

  const previewRuns = useMemo(() => {
    const previewLength = Math.min(text.length, 5000)
    const highlighted = new Uint8Array(previewLength)
    const mark = (start: number, length: number, kind: number) => {
      const end = Math.min(start + length, previewLength)
      for (let index = Math.max(0, start); index < end; index += 1) {
        if (highlighted[index] === 0) highlighted[index] = kind
      }
    }
    if (searchResult) {
      for (const result of Object.values(searchResult.results)) {
        for (const start of result?.matches ?? []) mark(start, pattern.length, 1)
      }
      if (bothStrands) {
        for (const result of Object.values(searchResult.results)) {
          for (const start of result?.reverse_matches ?? []) mark(start, pattern.length, 2)
        }
      }
    }
    if (multiResult) for (const match of multiResult.matches) mark(match.start, match.pattern.length, 3)
    const runs: { value: string; marked: number }[] = []
    const shown = text.slice(0, previewLength)
    let cursor = 0
    while (cursor < shown.length) {
      const marked = highlighted[cursor]
      let end = cursor + 1
      while (end < shown.length && highlighted[end] === marked) end += 1
      runs.push({ value: shown.slice(cursor, end), marked })
      cursor = end
    }
    return runs
  }, [text, pattern.length, searchResult, bothStrands, multiResult])

  const benchmarkRows = benchmark?.series ?? []

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto max-w-[1200px] px-4 pb-10 sm:px-6">
        <header className="flex h-12 items-center border-b border-line">
          <a className="text-[15px] font-semibold" href="#top" aria-label="DNA Sequence Analyzer home">DNA Sequence Analyzer</a>
        </header>

        <main id="top">
          <nav className="mb-4 flex gap-6 overflow-x-auto border-b border-line" aria-label="Analysis tools">
            {([
              ['search', 'Search'],
              ['similarity', 'Similarity'],
              ['benchmark', 'Benchmark'],
              ['visualizer', 'Visualizer'],
              ['alignment', 'Alignment'],
            ] as [Tab, string][]).map(([id, label]) => (
              <button key={id} onClick={() => setTab(id)} className={`shrink-0 border-b-2 px-1 py-3 text-sm font-medium ${tab === id ? 'border-forest text-ink' : 'border-transparent text-muted hover:text-ink'}`}>
                {label}
              </button>
            ))}
          </nav>

          {tab === 'search' && <section className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="panel">
                <SectionHeading number="01" title="Find a pattern" description="Scan a DNA sequence and compare matching strategies." />
                <div className="mt-6 grid gap-5">
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <label htmlFor="search-text" className="field-label">Text sequence</label>
                      <span className="text-xs text-muted">{text.length.toLocaleString()} bases</span>
                    </div>
                    <textarea id="search-text" className="sequence-input h-36" value={text} onChange={(event) => { setText(event.target.value); setSearchResult(null); setMultiResult(null) }} spellCheck={false} placeholder="Paste a sequence or upload a FASTA file" />
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <UploadButton busy={loading['search-upload']} onFile={(file) => uploadFile(file, 'search-upload', (sequence) => { setText(sequence); setSearchResult(null); setMultiResult(null) })} />
                      <span className="text-xs text-muted">or</span>
                      <input aria-label="Generated sequence length" className="mini-input w-24" type="number" min="1" max="1000000" value={generateLength} onChange={(event) => setGenerateLength(event.target.value)} />
                      <button className="quiet-button" onClick={generateSequence} disabled={loading.generate}>{loading.generate ? <Spinner /> : 'Generate random'}</button>
                      {errors['search-upload'] && <ErrorText message={errors['search-upload']} />}
                      {errors.generate && <ErrorText message={errors.generate} />}
                    </div>
                  </div>
                  <div>
                    <label htmlFor="search-pattern" className="field-label mb-2 block">Pattern</label>
                    <textarea id="search-pattern" className="sequence-input h-20" value={pattern} onChange={(event) => { setPattern(event.target.value); setSearchResult(null) }} spellCheck={false} placeholder="Enter the sequence to find" />
                  </div>
                  <div className="flex flex-wrap items-center gap-x-5 gap-y-3 border-t border-line pt-4">
                    <span className="field-label mr-1">Algorithms</span>
                    {algorithms.map((algorithm) => <label key={algorithm.id} className="flex cursor-pointer items-center gap-2 text-sm font-medium text-ink">
                      <input type="checkbox" className="accent-forest" checked={selected.includes(algorithm.id)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, algorithm.id] : current.filter((item) => item !== algorithm.id))} />
                      {algorithm.label}
                    </label>)}
                    <label className="flex cursor-pointer items-center gap-2 text-sm font-semibold text-forest"><input type="checkbox" className="accent-forest" checked={bothStrands} onChange={(event) => { setBothStrands(event.target.checked); setSearchResult(null) }} />Search both strands</label>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <button className="primary-button" onClick={executeSearch} disabled={loading.search}>{loading.search ? <><Spinner light /> Searching sequence</> : <>Run search</>}</button>
                    {errors.search && <ErrorText message={errors.search} />}
                  </div>
                </div>
              </div>

              <div className="result-panel panel flex min-h-[430px] flex-col">
                <SectionHeading number="02" title="Search results" description="Matches and algorithm performance at a glance." />
                {searchResult ? <>
                  <div className="mt-6 overflow-x-auto">
                    <table className="data-table">
                      <thead><tr><th>Algorithm</th><th>Forward</th>{bothStrands && <th>Reverse complement</th>}<th>Time (ms)</th><th>Comparisons</th></tr></thead>
                      <tbody>{algorithms.filter(({ id }) => searchResult.results[id]).map(({ id, label, color }) => {
                        const result = searchResult.results[id]!
                        return <tr key={id}><td><span className="mr-2 inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />{label}</td><td className="font-mono">{result.match_count.toLocaleString()}</td>{bothStrands && <td className="font-mono">{result.reverse_matches?.length.toLocaleString() ?? 0}</td>}<td className="font-mono">{result.time_ms.toFixed(4)}</td><td className="font-mono">{result.comparisons.toLocaleString()}</td></tr>
                      })}</tbody>
                    </table>
                  </div>
                  {searchResult.kmp_lps && <div className="mt-5"><p className="field-label mb-2">KMP · LPS array</p><div className="flex flex-wrap gap-1.5">{searchResult.kmp_lps.map((value, index) => <span key={index} title={`Pattern position ${index}`} className="grid h-8 min-w-8 place-items-center rounded-lg border border-line bg-paper px-2 font-mono text-xs">{value}</span>)}</div></div>}
                  {searchResult.z_array && <div className="mt-5"><p className="field-label mb-2">Z-algorithm · pattern Z array</p><div className="flex flex-wrap gap-1.5">{searchResult.z_array.map((value, index) => <span key={index} title={`Pattern position ${index}`} className="grid h-8 min-w-8 place-items-center rounded-lg border border-line bg-paper px-2 font-mono text-xs">{value}</span>)}</div></div>}
                  {searchResult.rabin_karp_stats && <div className="mt-4 flex flex-wrap gap-2"><MetricPill label="Hash hits" value={searchResult.rabin_karp_stats.hash_hits} /><MetricPill label="Spurious hits" value={searchResult.rabin_karp_stats.spurious_hits} /></div>}
                </> : <EmptyState icon="⌕" title="Results will appear here" text="Choose one or more algorithms and run a search to see matching positions and performance." />}
              </div>
            </div>
            <div className="panel">
              <div className="flex flex-wrap items-end justify-between gap-3"><SectionHeading number="03" title="Multi-pattern search" description="Find many motifs in one pass with Aho–Corasick." /><span className="text-xs text-muted">One pattern per line · up to 100</span></div>
              <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_auto] lg:items-end">
                <label><span className="field-label mb-2 block">Patterns</span><textarea className="sequence-input h-28" value={multiPatterns} onChange={(event) => { setMultiPatterns(event.target.value); setMultiResult(null) }} placeholder={'ACG\nCGT\n...'} spellCheck={false} /></label>
                <button className="primary-button" onClick={executeMultiSearch} disabled={loading.multisearch}>{loading.multisearch ? <><Spinner light /> Searching patterns</> : <>Run multi-search</>}</button>
              </div>
              {errors.multisearch && <div className="mt-3"><ErrorText message={errors.multisearch} /></div>}
              {multiResult && <div className="mt-5">
                <div className="mb-3 flex flex-wrap gap-2"><MetricPill label="Trie nodes" value={multiResult.node_count} /><MetricPill label="Transitions" value={multiResult.comparisons} /></div>
                <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Pattern</th><th>Matches</th><th>Positions</th></tr></thead><tbody>{Object.entries(multiResult.counts).map(([item, count]) => <tr key={item}><td className="font-mono font-semibold">{item}</td><td className="font-mono">{count}</td><td className="font-mono">{multiResult.matches.filter((match) => match.pattern === item).map((match) => match.start).join(', ') || '—'}</td></tr>)}</tbody></table></div>
              </div>}
            </div>
            {(searchResult || multiResult) && <div className="result-panel panel">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <SectionHeading number="04" title="Sequence preview" description="Forward, reverse-complement, and multi-pattern matches use distinct colors." />
                <span className="rounded-full bg-paper px-3 py-1.5 font-mono text-[11px] text-muted">0 — {Math.min(text.length, 5000).toLocaleString()}</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-muted">{searchResult && <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#bfe1cb]" />Forward matches</span>}{searchResult && bothStrands && <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#d9d6f5]" />Reverse complement</span>}{multiResult && <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-[#f4d8a9]" />Multi-pattern</span>}</div>
              <div className="mt-5 max-h-56 overflow-auto rounded-xl border border-line bg-[#fbfcfa] p-4 font-mono text-sm leading-7 tracking-[0.06em] scrollbar-thin">
                {previewRuns.map((run, index) => <span key={index} className={run.marked === 1 ? 'rounded bg-[#dcefe2] text-[#24573c]' : run.marked === 2 ? 'rounded bg-[#e5e2fa] text-[#514d8f]' : run.marked === 3 ? 'rounded bg-[#f9e8c9] text-[#78511b]' : ''}>{run.value}</span>)}
              </div>
              {text.length > 5000 && <p className="mt-2 text-xs text-muted">Preview limited to the first 5,000 characters of {text.length.toLocaleString()}.</p>}
            </div>}
          </section>}

          {tab === 'similarity' && <section className="space-y-6">
            <div className="panel">
              <SectionHeading number="01" title="Compare two sequences" description="Measure edit distance and recover a longest common subsequence." />
              <div className="mt-6 grid gap-5 md:grid-cols-2">
                <SequenceEditor label="Sequence A" value={seqA} onChange={(value) => { setSeqA(value); setSimilarity(null) }} busy={loading['similarity-a-upload']} error={errors['similarity-a-upload']} onFile={(file) => uploadFile(file, 'similarity-a-upload', (sequence) => { setSeqA(sequence); setSimilarity(null) })} />
                <SequenceEditor label="Sequence B" value={seqB} onChange={(value) => { setSeqB(value); setSimilarity(null) }} busy={loading['similarity-b-upload']} error={errors['similarity-b-upload']} onFile={(file) => uploadFile(file, 'similarity-b-upload', (sequence) => { setSeqB(sequence); setSimilarity(null) })} />
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button className="primary-button" onClick={compareSequences} disabled={loading.similarity}>{loading.similarity ? <><Spinner light /> Comparing sequences</> : <>Compare sequences</>}</button>
                {errors.similarity && <ErrorText message={errors.similarity} />}
              </div>
            </div>

            {similarity && <>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <ScoreCard label="Edit distance" value={similarity.edit_distance.toLocaleString()} note="minimum edits" tint="amber" />
                <ScoreCard label="Edit similarity" value={`${(similarity.edit_similarity * 100).toFixed(1)}%`} note="normalized score" tint="green" />
                <ScoreCard label="LCS length" value={similarity.lcs_length.toLocaleString()} note="shared bases" tint="violet" />
                <ScoreCard label="LCS similarity" value={`${(similarity.lcs_similarity * 100).toFixed(1)}%`} note="normalized score" tint="blue" />
              </div>
              <div className="panel">
                <div className="flex flex-wrap items-end justify-between gap-3"><SectionHeading number="02" title="Alignment" description="Position-by-position edit operations." /><div className="flex gap-3 text-xs text-muted"><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-500" />match</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-amber-500" />change</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-rose-500" />gap</span></div></div>
                {similarity.alignment_skipped || !similarity.operations ? <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">Alignment was skipped for this input size to keep memory use manageable.</div> : <Alignment result={similarity} />}
                {similarity.lcs_sequence !== null && <div className="mt-5 border-t border-line pt-4"><p className="field-label mb-2">Longest common subsequence <span className="ml-1 font-mono text-muted">{similarity.lcs_length} bp</span></p><p className="rounded-xl bg-mint px-4 py-3 font-mono text-sm tracking-wider text-forest break-all">{similarity.lcs_sequence || 'No common bases'}</p></div>}
              </div>
            </>}
          </section>}

          {tab === 'benchmark' && <section className="space-y-6">
            <div className="panel">
              <SectionHeading number="01" title="Benchmark the matchers" description="Compare median runtime and comparison counts across input sizes." />
              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-[0.7fr_1.4fr_0.9fr_auto] lg:items-end">
                <label><span className="field-label mb-2 block">Pattern length</span><input className="form-input" type="number" min="2" max="1000" value={patternLength} onChange={(event) => setPatternLength(event.target.value)} /></label>
                <label><span className="field-label mb-2 block">Text sizes</span><input className="form-input font-mono text-xs" value={textSizes} onChange={(event) => setTextSizes(event.target.value)} /><span className="mt-1 block text-[11px] text-muted">Comma or space separated · up to 8 sizes</span></label>
                <label><span className="field-label mb-2 block">Preset</span><select className="form-input" value={preset} onChange={(event) => setPreset(event.target.value as 'random' | 'worst_case')}><option value="random">Random DNA</option><option value="worst_case">Worst case</option></select></label>
                <button className="primary-button whitespace-nowrap" onClick={executeBenchmark} disabled={loading.benchmark}>{loading.benchmark ? <><Spinner light /> Running</> : <>Run benchmark</>}</button>
              </div>
              {errors.benchmark && <div className="mt-4"><ErrorText message={errors.benchmark} /></div>}
            </div>
            {benchmark ? <>
              <div className="grid gap-6 xl:grid-cols-2">
                <ChartPanel title="Execution time" unit="milliseconds" data={benchmarkRows} metric="time_ms" />
                <ChartPanel title="Character comparisons" unit="count" data={benchmarkRows} metric="comparisons" />
              </div>
              <div className="panel">
                <div className="flex flex-wrap items-end justify-between gap-2"><SectionHeading number="02" title="Benchmark data" description={`Five runs per algorithm · ${benchmark.preset === 'random' ? 'reproducible random DNA' : 'worst-case inputs'}`} /><span className="text-xs text-muted">Lower is better</span></div>
                <div className="mt-5 overflow-x-auto"><table className="data-table benchmark-table"><thead><tr><th rowSpan={2}>Text size</th>{algorithms.map((item) => <th key={item.id} colSpan={3}>{item.label}</th>)}</tr><tr>{algorithms.flatMap((item) => [<th key={`${item.id}-time`}>Time (ms)</th>, <th key={`${item.id}-comp`}>Comparisons</th>, <th key={`${item.id}-match`}>Matches</th>])}</tr></thead><tbody>{benchmarkRows.map((row) => <tr key={row.text_size}><td className="font-mono font-semibold">{row.text_size.toLocaleString()}</td>{algorithms.flatMap((item) => [<td key={`${item.id}-time`} className="font-mono">{row[item.id].time_ms.toFixed(3)}</td>, <td key={`${item.id}-comp`} className="font-mono">{row[item.id].comparisons.toLocaleString()}</td>, <td key={`${item.id}-match`} className="font-mono">{row[item.id].match_count.toLocaleString()}</td>])}</tr>)}</tbody></table></div>
              </div>
            </> : <div className="panel"><EmptyState icon="⌁" title="Your benchmark will appear here" text="Choose input sizes and a preset, then run the benchmark to compare all three algorithms." /></div>}
          </section>}

          {tab === 'visualizer' && <section className="space-y-6">
            <div className="panel">
              <SectionHeading number="01" title="Algorithm visualizer" description="Load a short example and step through the algorithm's decisions." />
              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1.2fr_1.2fr_auto] lg:items-end">
                <label><span className="field-label mb-2 block">Algorithm</span><select className="form-input" value={traceAlgorithm} onChange={(event) => { setTraceAlgorithm(event.target.value as typeof traceAlgorithm); setTraceResult(null); setTraceCursor(-1) }}><option value="naive">Naive search</option><option value="kmp">KMP</option><option value="rabin_karp">Rabin–Karp</option><option value="edit_distance">Edit distance</option></select></label>
                {traceAlgorithm === 'edit_distance' ? <>
                  <label><span className="field-label mb-2 block">Sequence A</span><input className="form-input font-mono" value={traceA} onChange={(event) => setTraceA(event.target.value)} /></label>
                  <label><span className="field-label mb-2 block">Sequence B</span><input className="form-input font-mono" value={traceB} onChange={(event) => setTraceB(event.target.value)} /></label>
                </> : <>
                  <label><span className="field-label mb-2 block">Text sequence</span><input className="form-input font-mono" value={traceText} onChange={(event) => setTraceText(event.target.value)} /></label>
                  <label><span className="field-label mb-2 block">Pattern</span><input className="form-input font-mono" value={tracePattern} onChange={(event) => setTracePattern(event.target.value)} /></label>
                </>}
                <button className="primary-button" onClick={loadTrace} disabled={loading.trace}>{loading.trace ? <><Spinner light /> Loading trace</> : <>Load trace</>}</button>
              </div>
              {errors.trace && <div className="mt-4"><ErrorText message={errors.trace} /></div>}
            </div>
            {traceResult && <>
              <div className="result-panel panel">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div><p className="field-label">Playback</p><p className="mt-1 text-xs text-muted">{traceCursor < 0 ? 'Ready to begin' : `Step ${traceCursor + 1} of ${traceSteps.length}`}</p></div>
                  <div className="flex flex-wrap items-center gap-2">
                    <button className="quiet-button" onClick={() => setTracePlaying((playing) => !playing)} disabled={traceSteps.length === 0}>{tracePlaying ? 'Ⅱ Pause' : '▶ Play'}</button>
                    <button className="quiet-button" onClick={() => { setTracePlaying(false); setTraceCursor((index) => Math.min(traceSteps.length - 1, index + 1)) }} disabled={traceCursor >= traceSteps.length - 1}>Step forward</button>
                    <button className="quiet-button" onClick={() => { setTracePlaying(false); setTraceCursor((index) => Math.max(-1, index - 1)) }} disabled={traceCursor < 0}>Step back</button>
                    <button className="quiet-button" onClick={() => { setTracePlaying(false); setTraceCursor(-1) }}>Reset</button>
                  </div>
                  <label className="flex items-center gap-3 text-xs text-muted">Speed <input aria-label="Playback speed" type="range" min="100" max="1500" step="50" value={traceSpeed} onChange={(event) => setTraceSpeed(Number(event.target.value))} /><span className="w-14 font-mono">{(traceSpeed / 1000).toFixed(2)}s</span></label>
                </div>
                <div className="mt-5 h-2 overflow-hidden rounded-full bg-paper"><div className="h-full rounded-full bg-forest transition-all" style={{ width: `${traceSteps.length ? ((traceCursor + 1) / traceSteps.length) * 100 : 0}%` }} /></div>
              </div>
              {'steps' in traceResult ? <TraceSearchView trace={traceResult} cursor={traceCursor} /> : <TraceEditView trace={traceResult} cursor={traceCursor} />}
            </>}
          </section>}

          {tab === 'alignment' && <section className="space-y-6">
            <div className="panel">
              <SectionHeading number="01" title="Sequence alignment" description="Align two sequences globally or find their best matching local segments." />
              <div className="mt-6 grid gap-5 md:grid-cols-2">
                <SequenceEditor label="Sequence A" value={alignA} onChange={(value) => { setAlignA(value); setAlignResult(null); setDotplotResult(null) }} busy={loading['align-a-upload']} error={errors['align-a-upload']} onFile={(file) => uploadFile(file, 'align-a-upload', (sequence) => { setAlignA(sequence); setAlignResult(null); setDotplotResult(null) })} />
                <SequenceEditor label="Sequence B" value={alignB} onChange={(value) => { setAlignB(value); setAlignResult(null); setDotplotResult(null) }} busy={loading['align-b-upload']} error={errors['align-b-upload']} onFile={(file) => uploadFile(file, 'align-b-upload', (sequence) => { setAlignB(sequence); setAlignResult(null); setDotplotResult(null) })} />
              </div>
              <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <label><span className="field-label mb-2 block">Mode</span><select className="form-input" value={alignMode} onChange={(event) => { const mode = event.target.value as 'global' | 'local'; setAlignMode(mode); if (mode === 'local' && alignMethod === 'hirschberg') setAlignMethod('full'); setAlignResult(null) }}><option value="global">Global</option><option value="local">Local</option></select></label>
                <label><span className="field-label mb-2 block">Method</span><select className="form-input" value={alignMethod} onChange={(event) => { const method = event.target.value as 'full' | 'hirschberg'; setAlignMethod(method); if (method === 'hirschberg') { setAlignMode('global'); setGapExtend(gapOpen) } setAlignResult(null) }}><option value="full">Full matrix</option><option value="hirschberg">Hirschberg · linear space</option></select></label>
                <label><span className="field-label mb-2 block">Match score</span><input className="form-input" type="number" value={matchScore} onChange={(event) => setMatchScore(event.target.value)} /></label>
                <label><span className="field-label mb-2 block">Mismatch score</span><input className="form-input" type="number" value={mismatchScore} onChange={(event) => setMismatchScore(event.target.value)} /></label>
                <label><span className="field-label mb-2 block">Gap open</span><input className="form-input" type="number" min="1" value={gapOpen} onChange={(event) => { setGapOpen(event.target.value); if (alignMethod === 'hirschberg') setGapExtend(event.target.value) }} /></label>
                <label><span className="field-label mb-2 block">Gap extend</span><input className="form-input" type="number" min="1" value={gapExtend} disabled={alignMethod === 'hirschberg'} onChange={(event) => setGapExtend(event.target.value)} /></label>
                {alignMethod === 'hirschberg' && <p className="self-center text-xs text-muted sm:col-span-2">Hirschberg uses linear gaps, so gap extend follows gap open.</p>}
              </div>
              <div className="mt-5 flex flex-wrap items-center gap-3"><button className="primary-button" onClick={runAlignment} disabled={loading.alignment}>{loading.alignment ? <><Spinner light /> Aligning</> : <>Run alignment</>}</button>{errors.alignment && <ErrorText message={errors.alignment} />}</div>
            </div>
            {alignResult && <div className="result-panel panel">
              <div className="flex flex-wrap items-center justify-between gap-3"><SectionHeading number="02" title={`${alignResult.mode === 'global' ? 'Global' : 'Local'} alignment`} description={`${alignResult.method === 'full' ? 'Full Gotoh matrix' : 'Hirschberg linear-space method'}.`} /><div className="flex gap-2"><ScoreCard label="Alignment score" value={String(alignResult.score)} note="optimal score" tint="green" /><ScoreCard label="Identity" value={`${(alignResult.identity * 100).toFixed(1)}%`} note="exact matches" tint="blue" /></div></div>
              {alignResult.mode === 'local' && <p className="mt-5 rounded-lg bg-paper px-3 py-2 text-xs text-muted">Sequence A: {alignResult.a_start}–{alignResult.a_end} <span className="mx-2">·</span> Sequence B: {alignResult.b_start}–{alignResult.b_end} <span className="ml-1">(0-based, end-exclusive)</span></p>}
              <ColoredAlignment alignedA={alignResult.aligned_a} alignedB={alignResult.aligned_b} operations={alignResult.operations} />
            </div>}
            <div className="panel">
              <div className="flex flex-wrap items-end justify-between gap-3"><SectionHeading number="03" title="Dot plot" description="Compare matching diagonal windows between the two sequences." /><span className="text-xs text-muted">Sequence A × Sequence B</span></div>
              <div className="mt-5 grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
                <label><span className="field-label mb-2 block">Window</span><input className="form-input" type="number" min="1" max="20" value={dotWindow} onChange={(event) => setDotWindow(event.target.value)} /></label>
                <label><span className="field-label mb-2 block">Minimum matches</span><input className="form-input" type="number" min="1" max={dotWindow} value={dotThreshold} onChange={(event) => setDotThreshold(event.target.value)} /></label>
                <button className="primary-button" onClick={runDotplot} disabled={loading.dotplot}>{loading.dotplot ? <><Spinner light /> Plotting</> : <>Generate dot plot</>}</button>
              </div>
              {errors.dotplot && <div className="mt-4"><ErrorText message={errors.dotplot} /></div>}
              {dotplotResult && <DotplotCanvas result={dotplotResult} seqALength={alignA.length} seqBLength={alignB.length} />}
            </div>
          </section>}
        </main>

      </div>
    </div>
  )
}

function SectionHeading({ title }: { number: string; title: string; description: string }) {
  return <h2 className="text-[15px] font-semibold">{title}</h2>
}

function UploadButton({ busy, onFile }: { busy?: boolean; onFile: (file: File) => void }) {
  return <label className="quiet-button cursor-pointer">{busy ? <><Spinner /> Uploading</> : <>Upload FASTA</>}<input className="sr-only" type="file" accept=".fasta,.fa,.txt" disabled={busy} onChange={(event) => { const file = event.target.files?.[0]; if (file) onFile(file); event.target.value = '' }} /></label>
}

function SequenceEditor({ label, value, onChange, busy, error, onFile }: { label: string; value: string; onChange: (value: string) => void; busy: boolean; error?: string; onFile: (file: File) => void }) {
  return <div><div className="mb-2 flex items-center justify-between"><label className="field-label">{label}</label><span className="text-xs text-muted">{value.length.toLocaleString()} bases</span></div><textarea className="sequence-input h-40" value={value} onChange={(event) => onChange(event.target.value)} spellCheck={false} /><div className="mt-2 flex flex-wrap items-center gap-2"><UploadButton busy={busy} onFile={onFile} />{error && <ErrorText message={error} />}</div></div>
}

function EmptyState(_props: { icon: string; title: string; text: string }) {
  return <p className="py-6 text-sm text-muted">No results yet.</p>
}

function ErrorText({ message }: { message: string }) {
  return <span role="alert" className="text-xs font-medium text-rose-700">{message}</span>
}

function Spinner({ light = false }: { light?: boolean }) {
  return <span className={`inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-r-transparent ${light ? 'text-white' : 'text-forest'}`} aria-label="Loading" />
}

function MetricPill({ label, value }: { label: string; value: number }) {
  return <span className="rounded-lg border border-line bg-white px-3 py-2 text-xs text-muted">{label} <b className="ml-1 font-mono text-ink">{value.toLocaleString()}</b></span>
}

function ScoreCard({ label, value }: { label: string; value: string; note: string; tint: 'amber' | 'green' | 'violet' | 'blue' }) {
  return <div className="min-w-28"><p className="text-xs font-medium text-muted">{label}</p><p className="mt-1 font-mono text-lg font-semibold">{value}</p></div>
}

function Alignment({ result }: { result: SimilarityResponse }) {
  const operations = result.operations ?? []
  const alignedA = result.aligned_a ?? ''
  const alignedB = result.aligned_b ?? ''
  return <div className="mt-5 overflow-x-auto rounded-xl border border-line bg-[#fbfcfa] p-4 font-mono text-sm leading-8 tracking-wider scrollbar-thin"><div className="min-w-max">{operations.map((operation, index) => {
    const color = operation === 'match' ? 'text-emerald-700' : operation === 'substitute' ? 'text-amber-700' : 'text-rose-600'
    return <span key={index} className={color}>{alignedA[index]}</span>
  })}<br />{operations.map((operation, index) => <span key={index} className={operation === 'match' ? 'text-emerald-500' : operation === 'substitute' ? 'text-amber-500' : 'text-rose-400'}>{operation === 'match' ? '|' : operation === 'substitute' ? '·' : ' '}</span>)}<br />{operations.map((operation, index) => {
    const color = operation === 'match' ? 'text-emerald-700' : operation === 'substitute' ? 'text-amber-700' : 'text-rose-600'
    return <span key={index} className={color}>{alignedB[index]}</span>
  })}</div></div>
}

function TraceSearchView({ trace, cursor }: { trace: TraceSearch; cursor: number }) {
  const step = cursor >= 0 ? trace.steps[cursor] : undefined
  const type = String(step?.type ?? '')
  const numeric = (key: string): number | undefined => typeof step?.[key] === 'number' ? step[key] as number : undefined
  let shift = 0
  if (numeric('shift') !== undefined) shift = numeric('shift')!
  else if (trace.algorithm === 'kmp' && type === 'compare') shift = (numeric('text_index') ?? 0) - (numeric('pattern_index') ?? 0)
  else if (trace.algorithm === 'kmp' && type === 'fallback') {
    const prior = [...trace.steps.slice(0, cursor)].reverse().find((item) => item.type === 'compare')
    const textIndex = typeof prior?.text_index === 'number' ? prior.text_index : 0
    const fullMatch = numeric('from') === trace.pattern.length
    shift = textIndex + (fullMatch ? 1 : 0) - (numeric('to') ?? 0)
  }
  shift = Math.max(0, shift)
  const patternIndex = numeric('pattern_index')
  const textIndex = numeric('text_index')
  const result = String(step?.result ?? '')
  let explanation = 'Press Step forward or Play to begin the trace.'
  if (type === 'compare') {
    const textChar = trace.text[textIndex ?? 0]
    const patternChar = trace.pattern[patternIndex ?? 0]
    explanation = `Compare text ${textIndex} (${textChar}) with pattern ${patternIndex} (${patternChar}): ${result}.`
  } else if (type === 'fallback') explanation = `KMP keeps the prefix of length ${numeric('to')} after falling back from ${numeric('from')}.`
  else if (type === 'hash') explanation = `Window ${numeric('shift')} has hash ${numeric('window_hash')}; pattern hash is ${numeric('pattern_hash')}, so they ${step?.equal ? 'match' : 'differ'}.`
  else if (type === 'verify') explanation = `Hash equality at shift ${numeric('shift')} is verified character by character: ${result}.`
  else if (type === 'match_found') explanation = `The pattern occurs at text position ${numeric('shift')}.`

  const fallbackFrom = type === 'fallback' ? (numeric('from') ?? 0) - 1 : -1
  const compareColor = result === 'match' ? 'bg-emerald-200 text-emerald-950' : result === 'mismatch' ? 'bg-rose-200 text-rose-950' : ''
  const visibleRange = trace.algorithm === 'rabin_karp' && type === 'hash' ? trace.pattern.length : 1

  return <div className="panel">
    <SectionHeading number="02" title={trace.algorithm === 'rabin_karp' ? 'Rolling hash trace' : 'Search trace'} description={`${trace.matches.length} match${trace.matches.length === 1 ? '' : 'es'} in ${trace.text.length} bases.`} />
    <div className="mt-5 overflow-auto rounded-xl border border-line bg-[#fbfcfa] p-4 font-mono text-sm leading-8 scrollbar-thin">
      <div className="min-w-max whitespace-pre">{[...trace.text].map((character, index) => {
        const currentCompare = textIndex === index
        const inHashWindow = type === 'hash' && index >= shift && index < shift + visibleRange
        const bg = currentCompare ? compareColor : inHashWindow ? (step?.equal ? 'bg-emerald-100' : 'bg-[#f2f1eb]') : ''
        return <span key={index} className={bg}>{character}</span>
      })}</div>
      <div className="min-w-max whitespace-pre text-forest" style={{ marginLeft: `${shift * 0.57}rem` }}>{[...trace.pattern].map((character, index) => {
        const active = index === patternIndex
        const lpsActive = trace.algorithm === 'kmp' && index === fallbackFrom
        return <span key={index} className={`${active ? compareColor : ''} ${lpsActive ? 'rounded bg-amber-200 text-amber-950' : ''}`}>{character}</span>
      })}</div>
    </div>
    {trace.lps && <div className="mt-4"><p className="field-label mb-2">KMP · LPS array</p><div className="flex flex-wrap gap-1.5">{trace.lps.map((value, index) => <span key={index} className={`grid h-8 min-w-8 place-items-center rounded-lg border px-2 font-mono text-xs ${index === fallbackFrom ? 'border-amber-400 bg-amber-100 text-amber-950' : 'border-line bg-white'}`}>{value}</span>)}</div></div>}
    <div className="mt-4 rounded-xl bg-mint px-4 py-3 text-sm text-forest">{explanation}</div>
    {trace.algorithm === 'rabin_karp' && step?.type === 'hash' && <div className="mt-3 flex gap-2"><MetricPill label="Window hash" value={Number(step.window_hash)} /><MetricPill label="Pattern hash" value={Number(step.pattern_hash)} /></div>}
    <div className="mt-3 text-xs text-muted">Matches: <span className="font-mono text-ink">{trace.matches.length ? trace.matches.join(', ') : 'none'}</span></div>
  </div>
}

function TraceEditView({ trace, cursor }: { trace: TraceEdit; cursor: number }) {
  const active = cursor >= 0 ? trace.cells[cursor] : undefined
  const completed = cursor >= trace.cells.length - 1
  const path = new Set(completed ? trace.traceback.map(([i, j]) => `${i},${j}`) : [])
  const explanation = active
    ? `Cell (${active.i}, ${active.j}) = ${active.value}${active.source === 'init' ? ' from the initial row or column.' : ` using ${active.source}.`}`
    : 'Press Step forward or Play to fill the edit-distance matrix.'
  return <div className="panel">
    <div className="flex flex-wrap items-end justify-between gap-3"><SectionHeading number="02" title="Edit-distance matrix" description={`Distance between ${trace.seq_a} and ${trace.seq_b}.`} /><span className="rounded-full bg-mint px-3 py-1.5 text-xs font-semibold text-forest">Distance {trace.distance}</span></div>
    <div className="mt-5 max-h-[520px] overflow-auto rounded-xl border border-line bg-[#fbfcfa] p-3 scrollbar-thin">
      <table className="border-separate border-spacing-1 font-mono text-xs"><thead><tr><th className="sticky left-0 bg-[#fbfcfa] p-2">·</th><th className="p-2">∅</th>{[...trace.seq_b].map((character, index) => <th key={index} className="p-2 text-muted">{character}</th>)}</tr></thead><tbody>{trace.matrix.map((row, i) => <tr key={i}><th className="sticky left-0 bg-[#fbfcfa] p-2 text-muted">{i === 0 ? '∅' : trace.seq_a[i - 1]}</th>{row.map((value, j) => {
        const isVisible = i * (trace.seq_b.length + 1) + j <= cursor
        const isActive = active?.i === i && active.j === j
        const isPath = path.has(`${i},${j}`)
        return <td key={j} title={isVisible ? `(${i}, ${j})${i && j ? ` · ${trace.cells[i * (trace.seq_b.length + 1) + j].source}` : ' · init'}` : undefined} className={`h-9 min-w-9 rounded-lg border text-center ${isActive ? 'border-forest bg-forest font-bold text-white' : isPath ? 'border-emerald-300 bg-emerald-100 text-forest' : 'border-line bg-white'} ${!isVisible ? 'text-transparent' : ''}`}>{isVisible ? value : '·'}</td>
      })}</tr>)}</tbody></table>
    </div>
    <div className="mt-4 rounded-xl bg-mint px-4 py-3 text-sm text-forest">{explanation}{completed && <span className="ml-1">Traceback path is highlighted.</span>}</div>
  </div>
}

function ChartPanel({ title, data, metric }: { title: string; unit: string; data: BenchmarkRow[]; metric: 'time_ms' | 'comparisons' }) {
  const chartData = data.map((row) => ({ text_size: row.text_size, ...Object.fromEntries(algorithms.map((algorithm) => [algorithm.id, row[algorithm.id][metric]])) }))
  return <div className="result-panel panel"><h3 className="mb-3 text-[15px] font-semibold">{title}</h3><div className="h-64 w-full"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 4, left: 2 }}><CartesianGrid stroke="#e5e5e5" vertical={false} /><XAxis dataKey="text_size" tick={{ fontSize: 10, fill: '#666', fontFamily: 'ui-monospace, Menlo, monospace' }} tickLine={false} axisLine={{ stroke: '#d9d9d9' }} tickFormatter={(value: number) => value >= 1000 ? `${value / 1000}k` : String(value)} /><YAxis width={metric === 'time_ms' ? 48 : 64} tick={{ fontSize: 10, fill: '#666', fontFamily: 'ui-monospace, Menlo, monospace' }} tickLine={false} axisLine={false} tickFormatter={(value: number) => value >= 1000 ? `${(value / 1000).toFixed(0)}k` : String(value)} /><Tooltip contentStyle={{ border: '1px solid #d9d9d9', borderRadius: 4, boxShadow: 'none', fontSize: 12, fontFamily: 'ui-monospace, Menlo, monospace' }} labelFormatter={(value) => `Text size: ${Number(value).toLocaleString()}`} /><Legend iconType="plainline" wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />{algorithms.map((algorithm) => <Line key={algorithm.id} type="monotone" dataKey={algorithm.id} name={algorithm.label} stroke={algorithm.color} strokeWidth={1.5} dot={false} activeDot={{ r: 3 }} />)}</LineChart></ResponsiveContainer></div></div>
}

function ColoredAlignment({ alignedA, alignedB, operations }: { alignedA: string; alignedB: string; operations: AlignResponse['operations'] }) {
  const colorFor = (operation: AlignResponse['operations'][number]) => operation === 'match' ? 'text-emerald-700' : operation === 'mismatch' ? 'text-amber-700' : 'text-rose-600'
  return <div className="mt-5 overflow-x-auto rounded-xl border border-line bg-[#fbfcfa] p-4 font-mono text-sm leading-8 tracking-wider scrollbar-thin"><div className="min-w-max">{operations.map((operation, index) => <span key={index} className={colorFor(operation)}>{alignedA[index]}</span>)}<br />{operations.map((operation, index) => <span key={index} className={operation === 'match' ? 'text-emerald-500' : operation === 'mismatch' ? 'text-amber-500' : 'text-rose-400'}>{operation === 'match' ? '|' : operation === 'mismatch' ? '·' : ' '}</span>)}<br />{operations.map((operation, index) => <span key={index} className={colorFor(operation)}>{alignedB[index]}</span>)}</div></div>
}

function DotplotCanvas({ result, seqALength, seqBLength }: { result: DotplotResponse; seqALength: number; seqBLength: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas?.getContext('2d')
    if (!canvas || !context || result.rows === 0 || result.cols === 0) return
    context.clearRect(0, 0, canvas.width, canvas.height)
    context.fillStyle = '#28624a'
    const blockWidth = canvas.width / result.cols
    const blockHeight = canvas.height / result.rows
    for (const [row, column] of result.points) {
      context.fillRect(column * blockWidth, row * blockHeight, Math.max(1, blockWidth), Math.max(1, blockHeight))
    }
  }, [result])
  return <div className="mt-5">
    <p className="mb-2 text-xs text-muted">{result.points.length.toLocaleString()} matching points <span className="mx-1">·</span> {result.rows} × {result.cols} windows</p>
    <div className="overflow-auto rounded-xl border border-line bg-[#fbfcfa] p-3 scrollbar-thin">
      <canvas ref={canvasRef} width={Math.max(1, result.cols)} height={Math.max(1, result.rows)} className="block max-h-[520px] max-w-full" style={{ width: 'auto', height: 'auto', imageRendering: 'pixelated' }} aria-label={`Dot plot: sequence A length ${seqALength}, sequence B length ${seqBLength}`} />
    </div>
    <div className="mt-2 flex justify-between text-[11px] text-muted"><span>Sequence A · {seqALength} bases</span><span>Sequence B · {seqBLength} bases</span></div>
  </div>
}

export default App
