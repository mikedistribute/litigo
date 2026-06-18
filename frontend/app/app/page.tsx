"use client"

import * as React from "react"
import Link from "next/link"
import {
  ArrowDownToLine,
  ArrowLeft,
  CheckCircle2,
  FileText,
  Loader2,
  Scale,
  Search,
  ShieldCheck,
  UploadCloud,
  XCircle,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://litigo-production.up.railway.app"
).replace(/\/$/, "")

const stages = [
  ["document_analyzer", "Read decision"],
  ["company_sourcing", "Find companies"],
  ["company_research", "Research targets"],
  ["selection_agent", "Rank opportunity"],
  ["report_writer", "Write memo"],
  ["document_generator", "Prepare export"],
] as const

type UploadResponse = {
  document_id: string
  filename: string
  content_hash: string
}

type StartResponse = {
  job_id: string
  status: string
}

type StatusResponse = {
  status: string
  current_node?: string | null
  progress_pct: number
  message: string
}

type ResultResponse = {
  report_url_docx?: string | null
  report_url_pdf?: string | null
  summary?: string | null
  snapshot?: Record<string, unknown> | null
}

type EventPayload = {
  status?: string
  message?: string
  progress?: number
  node?: string | null
  error?: string
}

function absoluteUrl(path?: string | null) {
  if (!path) return null
  try {
    return new URL(path, API_BASE_URL).toString()
  } catch {
    return path
  }
}

function safeRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function extractResult(result: ResultResponse | null) {
  const snapshot = safeRecord(result?.snapshot)
  const documentNode = safeRecord(snapshot.document_analyzer)
  const contract = safeRecord(documentNode.judicial_contract)
  const metadata = safeRecord(contract.metadata)
  const infraction = safeRecord(contract.infraction)
  const sourcing = safeRecord(snapshot.company_sourcing)
  const selection = safeRecord(snapshot.selection_agent)

  return {
    caseReference:
      typeof metadata.case_reference === "string" ? metadata.case_reference : "Pending",
    jurisdiction:
      typeof metadata.jurisdiction === "string" ? metadata.jurisdiction : "Not available",
    infraction:
      typeof infraction.type === "string" ? infraction.type : "Pending extraction",
    markets: Array.isArray(infraction.affected_markets)
      ? infraction.affected_markets.map(String).slice(0, 5)
      : [],
    candidates: Array.isArray(sourcing.candidate_companies)
      ? sourcing.candidate_companies.map(String).slice(0, 8)
      : [],
    selected: Array.isArray(selection.selected_companies)
      ? selection.selected_companies.length
      : 0,
  }
}

function stageIndex(status: StatusResponse | null) {
  if (!status?.current_node) return -1
  return stages.findIndex(([key]) => key === status.current_node)
}

export default function AppPage() {
  const [file, setFile] = React.useState<File | null>(null)
  const [upload, setUpload] = React.useState<UploadResponse | null>(null)
  const [job, setJob] = React.useState<StartResponse | null>(null)
  const [status, setStatus] = React.useState<StatusResponse | null>(null)
  const [result, setResult] = React.useState<ResultResponse | null>(null)
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [dragging, setDragging] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement | null>(null)
  const eventSourceRef = React.useRef<EventSource | null>(null)

  const activeStage = stageIndex(status)
  const progress = status?.progress_pct ?? (result ? 100 : 0)
  const memo = extractResult(result)
  const docxUrl = absoluteUrl(result?.report_url_docx)
  const pdfUrl = absoluteUrl(result?.report_url_pdf)

  React.useEffect(() => {
    return () => eventSourceRef.current?.close()
  }, [])

  async function fetchResult(jobId: string) {
    const response = await fetch(`${API_BASE_URL}/api/v1/analysis/${jobId}/result`)
    if (!response.ok) throw new Error(`Result request failed with HTTP ${response.status}`)
    const data = (await response.json()) as ResultResponse
    setResult(data)
  }

  function connectStream(jobId: string) {
    eventSourceRef.current?.close()
    const source = new EventSource(`${API_BASE_URL}/api/v1/analysis/${jobId}/stream`)
    eventSourceRef.current = source

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as EventPayload

      if (payload.error) {
        setError(payload.error)
        setBusy(false)
        return
      }

      setStatus((current) => ({
        status: payload.status ?? current?.status ?? "queued",
        current_node: payload.node ?? current?.current_node ?? null,
        progress_pct: payload.progress ?? current?.progress_pct ?? 0,
        message: payload.message ?? current?.message ?? "Analysis running",
      }))

      if (payload.status === "completed") {
        source.close()
        setBusy(false)
        void fetchResult(jobId)
      }

      if (payload.status === "failed") {
        source.close()
        setBusy(false)
        setError(payload.message ?? "Analysis failed")
      }
    }

    source.onerror = () => {
      source.close()
      setBusy(false)
      setError("Live connection closed. Refresh the page or start a new analysis.")
    }
  }

  async function runAnalysis() {
    if (!file) {
      setError("Select a legal decision first.")
      return
    }

    setBusy(true)
    setError(null)
    setResult(null)
    setUpload(null)
    setJob(null)
    setStatus({ status: "queued", progress_pct: 0, message: "Preparing file" })

    try {
      const form = new FormData()
      form.append("file", file)

      const uploadResponse = await fetch(`${API_BASE_URL}/api/v1/analysis/upload`, {
        method: "POST",
        body: form,
      })
      if (!uploadResponse.ok) throw new Error(`Upload failed with HTTP ${uploadResponse.status}`)

      const uploadData = (await uploadResponse.json()) as UploadResponse
      setUpload(uploadData)

      const startResponse = await fetch(`${API_BASE_URL}/api/v1/analysis/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: uploadData.document_id }),
      })
      if (!startResponse.ok) throw new Error(`Start failed with HTTP ${startResponse.status}`)

      const startData = (await startResponse.json()) as StartResponse
      setJob(startData)
      setStatus({ status: "queued", progress_pct: 5, message: "Analysis queued" })
      connectStream(startData.job_id)
    } catch (err) {
      setBusy(false)
      setError(err instanceof Error ? err.message : "Analysis failed")
    }
  }

  function chooseFile(files: FileList | null) {
    const selected = files?.[0]
    if (!selected) return
    setFile(selected)
    setError(null)
    setResult(null)
  }

  return (
    <main className="min-h-svh bg-white text-slate-950">
      <header className="border-b border-slate-200 bg-white/86 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-800">
            <ArrowLeft className="size-4" />
            Litigo
          </Link>
          <div className="hidden items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-800 sm:flex">
            <span className="size-1.5 rounded-full bg-blue-600" />
            Connected to production API
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[410px_minmax(0,1fr)] lg:px-8">
        <aside className="space-y-4">
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm shadow-blue-950/5">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-700">
                  New screen
                </p>
                <h1 className="mt-2 text-3xl font-semibold leading-tight">
                  Analyze a legal decision.
                </h1>
              </div>
              <Scale className="size-6 text-blue-700" />
            </div>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              onDragEnter={(event) => {
                event.preventDefault()
                setDragging(true)
              }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault()
                setDragging(false)
                chooseFile(event.dataTransfer.files)
              }}
              className={cn(
                "grid min-h-52 w-full place-items-center rounded-md border border-dashed p-5 text-center transition",
                dragging
                  ? "border-blue-500 bg-blue-50"
                  : "border-slate-300 bg-slate-50 hover:border-blue-500 hover:bg-white"
              )}
            >
              <div className="max-w-72">
                <div className="mx-auto mb-4 grid size-11 place-items-center rounded-md bg-blue-600 text-white shadow-lg shadow-blue-600/20">
                  <UploadCloud className="size-5" />
                </div>
                <div className="text-sm font-semibold">
                  {file ? file.name : "Upload PDF, DOCX, or TXT"}
                </div>
                <div className="mt-1 text-xs leading-5 text-slate-500">
                  {file
                    ? `${(file.size / 1024 / 1024).toFixed(2)} MB ready for screening`
                    : "Drop a decision here or open your file picker"}
                </div>
              </div>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              onChange={(event) => chooseFile(event.target.files)}
            />

            <div className="mt-4 grid gap-2">
              <Button
                type="button"
                onClick={() => void runAnalysis()}
                disabled={!file || busy}
                className="h-11 rounded-md bg-blue-600 text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700"
              >
                {busy ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
                Start analysis
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={busy && !result}
                className="h-10 rounded-md border-slate-300 bg-white text-slate-800 hover:bg-slate-50"
                onClick={() => {
                  eventSourceRef.current?.close()
                  setFile(null)
                  setUpload(null)
                  setJob(null)
                  setStatus(null)
                  setResult(null)
                  setError(null)
                  setBusy(false)
                }}
              >
                Clear
              </Button>
            </div>

            {error ? (
              <div className="mt-4 flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                <XCircle className="mt-0.5 size-4 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}
          </div>

          <div className="rounded-md border border-slate-800 bg-slate-950 p-5 text-white shadow-xl shadow-blue-950/15">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-300">
              Progress
            </p>
            <div className="mt-3 flex items-end justify-between">
              <div className="text-4xl font-semibold">{Math.round(progress)}%</div>
              <div className="max-w-44 text-right text-sm text-white/62">
                {status?.message ?? "Waiting for a decision"}
              </div>
            </div>
            <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/12">
              <div
                className="h-full rounded-full bg-blue-400 transition-all duration-500"
                style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
              />
            </div>
          </div>
        </aside>

        <section className="space-y-4">
          <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm shadow-blue-950/5">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-700">
                  Analysis pipeline
                </p>
                <h2 className="mt-2 text-2xl font-semibold">From legal facts to funding memo</h2>
              </div>
              {result ? (
                <span className="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">
                  Memo ready
                </span>
              ) : null}
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              {stages.map(([key, label], index) => {
                const done = result || index < activeStage
                const active = index === activeStage && !result
                return (
                  <div
                    key={key}
                    className={cn(
                      "rounded-md border p-4",
                      done && "border-blue-200 bg-blue-50",
                      active && "border-blue-500 bg-white shadow-md shadow-blue-600/10",
                      !done && !active && "border-slate-200 bg-slate-50"
                    )}
                  >
                    <div className="mb-5 flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-500">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      {done ? (
                        <CheckCircle2 className="size-4 text-blue-700" />
                      ) : (
                        <span className="size-2 rounded-full bg-slate-300" />
                      )}
                    </div>
                    <div className="text-sm font-semibold">{label}</div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1fr_330px]">
            <div className="rounded-md border border-slate-200 bg-white p-5 shadow-sm shadow-blue-950/5">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-700">
                    Output preview
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold">Investment memo snapshot</h2>
                </div>
                <FileText className="size-5 text-blue-700" />
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  ["Case", memo.caseReference],
                  ["Jurisdiction", memo.jurisdiction],
                  ["Infraction", memo.infraction],
                  ["Selected targets", String(memo.selected)],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <div className="text-xs text-slate-500">{label}</div>
                    <div className="mt-1 min-h-6 text-sm font-semibold">{value}</div>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-5 lg:grid-cols-2">
                <div>
                  <div className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Affected markets
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {memo.markets.length ? (
                      memo.markets.map((market) => (
                        <span
                          key={market}
                          className="rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs text-blue-800"
                        >
                          {market}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-slate-500">Available after analysis.</span>
                    )}
                  </div>
                </div>
                <div>
                  <div className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Candidate companies
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {memo.candidates.length ? (
                      memo.candidates.map((company) => (
                        <span
                          key={company}
                          className="rounded-full bg-slate-950 px-2.5 py-1 text-xs text-white"
                        >
                          {company}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-slate-500">Available after sourcing.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-md border border-slate-800 bg-slate-950 p-5 text-white shadow-xl shadow-blue-950/15">
              <ShieldCheck className="mb-6 size-7 text-blue-300" />
              <h2 className="text-2xl font-semibold">Memo exports</h2>
              <p className="mt-3 text-sm leading-6 text-white/62">
                Download the generated memo for partner review, IC prep, or the
                next diligence meeting.
              </p>
              <div className="mt-6 grid gap-2">
                {docxUrl ? (
                  <Button asChild className="h-10 rounded-md bg-blue-500 text-white hover:bg-blue-400">
                    <a href={docxUrl} download>
                      <ArrowDownToLine className="size-4" />
                      Download DOCX
                    </a>
                  </Button>
                ) : (
                  <Button disabled className="h-10 rounded-md bg-blue-500 text-white">
                    <ArrowDownToLine className="size-4" />
                    Download DOCX
                  </Button>
                )}
                {pdfUrl ? (
                  <Button
                    asChild
                    variant="outline"
                    className="h-10 rounded-md border-white/18 bg-transparent text-white hover:bg-white/10 hover:text-white"
                  >
                    <a href={pdfUrl} download>
                      <ArrowDownToLine className="size-4" />
                      Download PDF
                    </a>
                  </Button>
                ) : (
                  <Button
                    disabled
                    variant="outline"
                    className="h-10 rounded-md border-white/18 bg-transparent text-white"
                  >
                    <ArrowDownToLine className="size-4" />
                    Download PDF
                  </Button>
                )}
              </div>
              <div className="mt-6 border-t border-white/12 pt-4 text-xs leading-5 text-white/48">
                {upload?.content_hash
                  ? `Source hash ${upload.content_hash.slice(0, 24)}`
                  : job?.job_id
                    ? `Job ${job.job_id}`
                    : "Source hash appears after upload."}
              </div>
            </div>
          </div>
        </section>
      </section>
    </main>
  )
}
