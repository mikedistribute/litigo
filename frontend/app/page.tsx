"use client"

import * as React from "react"
import {
  Activity,
  AlertCircle,
  ArrowDownToLine,
  CheckCircle2,
  ClipboardList,
  FileText,
  Gavel,
  Loader2,
  Radio,
  Scale,
  Search,
  ShieldCheck,
  UploadCloud,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const DEFAULT_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"

const STEPS = [
  {
    key: "document_analyzer",
    status: "analyzing_document",
    label: "Decision",
    detail: "Judicial extraction",
    icon: FileText,
  },
  {
    key: "company_sourcing",
    status: "sourcing_companies",
    label: "Market map",
    detail: "Candidate sourcing",
    icon: Search,
  },
  {
    key: "company_research",
    status: "researching_companies",
    label: "Diligence",
    detail: "Company research",
    icon: ClipboardList,
  },
  {
    key: "selection_agent",
    status: "selecting_companies",
    label: "Ranking",
    detail: "TPLF selection",
    icon: Scale,
  },
  {
    key: "report_writer",
    status: "writing_report",
    label: "Memo",
    detail: "Investment writing",
    icon: Gavel,
  },
  {
    key: "document_generator",
    status: "generating_document",
    label: "Export",
    detail: "DOCX generation",
    icon: ArrowDownToLine,
  },
] as const

type HealthResponse = {
  status: string
  app: string
  version: string
  gemini_configured: boolean
  model: string
}

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
  content_hash?: string | null
}

type EventPayload = {
  status?: string
  message?: string
  progress?: number
  node?: string | null
  error?: string
}

type RunLog = {
  time: string
  title: string
  detail: string
  tone?: "normal" | "error" | "success"
}

function absoluteUrl(apiBaseUrl: string, path?: string | null) {
  if (!path) return null
  try {
    return new URL(path, apiBaseUrl).toString()
  } catch {
    return path
  }
}

function getStepIndex(status?: string, node?: string | null) {
  if (!status && !node) return -1
  const byNode = node ? STEPS.findIndex((step) => step.key === node) : -1
  if (byNode >= 0) return byNode
  return STEPS.findIndex((step) => step.status === status)
}

function formatClock() {
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date())
}

function safeRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}
}

function extractSnapshot(result: ResultResponse | null) {
  const snapshot = safeRecord(result?.snapshot)
  const documentNode = safeRecord(snapshot.document_analyzer)
  const contract = safeRecord(documentNode.judicial_contract)
  const infraction = safeRecord(contract.infraction)
  const metadata = safeRecord(contract.metadata)
  const sourcing = safeRecord(snapshot.company_sourcing)
  const research = safeRecord(snapshot.company_research)
  const selection = safeRecord(snapshot.selection_agent)
  const writer = safeRecord(snapshot.report_writer)

  return {
    caseReference:
      typeof metadata.case_reference === "string" ? metadata.case_reference : "Pending",
    jurisdiction:
      typeof metadata.jurisdiction === "string" ? metadata.jurisdiction : "Unknown",
    infractionType:
      typeof infraction.type === "string" ? infraction.type : "Not extracted yet",
    affectedMarkets: Array.isArray(infraction.affected_markets)
      ? infraction.affected_markets.map(String).slice(0, 4)
      : [],
    candidates: Array.isArray(sourcing.candidate_companies)
      ? sourcing.candidate_companies.map(String)
      : [],
    reports: Array.isArray(research.company_reports)
      ? research.company_reports.length
      : 0,
    selected: Array.isArray(selection.selected_companies)
      ? selection.selected_companies.length
      : 0,
    hasReport: Boolean(writer.report_content),
  }
}

export default function Page() {
  const [apiBaseUrl, setApiBaseUrl] = React.useState(DEFAULT_API_BASE_URL)
  const [health, setHealth] = React.useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = React.useState<string | null>(null)
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null)
  const [upload, setUpload] = React.useState<UploadResponse | null>(null)
  const [job, setJob] = React.useState<StartResponse | null>(null)
  const [status, setStatus] = React.useState<StatusResponse | null>(null)
  const [result, setResult] = React.useState<ResultResponse | null>(null)
  const [logs, setLogs] = React.useState<RunLog[]>([])
  const [busy, setBusy] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [dragActive, setDragActive] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement | null>(null)
  const eventSourceRef = React.useRef<EventSource | null>(null)

  const activeIndex = getStepIndex(status?.status, status?.current_node)
  const progress = status?.progress_pct ?? (result ? 100 : 0)
  const snapshot = extractSnapshot(result)
  const docxUrl = absoluteUrl(apiBaseUrl, result?.report_url_docx)
  const pdfUrl = absoluteUrl(apiBaseUrl, result?.report_url_pdf)

  const addLog = React.useCallback((entry: Omit<RunLog, "time">) => {
    setLogs((current) => [{ time: formatClock(), ...entry }, ...current].slice(0, 8))
  }, [])

  const checkHealth = React.useCallback(async () => {
    setHealthError(null)
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/health`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data = (await response.json()) as HealthResponse
      setHealth(data)
    } catch (err) {
      setHealth(null)
      setHealthError(err instanceof Error ? err.message : "Health check failed")
    }
  }, [apiBaseUrl])

  React.useEffect(() => {
    const id = window.setTimeout(() => {
      void checkHealth()
    }, 0)

    return () => {
      window.clearTimeout(id)
    }
  }, [checkHealth])

  React.useEffect(() => {
    return () => {
      eventSourceRef.current?.close()
    }
  }, [])

  async function fetchResult(jobId: string) {
    const response = await fetch(`${apiBaseUrl}/api/v1/analysis/${jobId}/result`)
    if (!response.ok) {
      throw new Error(`Result request failed with HTTP ${response.status}`)
    }
    const data = (await response.json()) as ResultResponse
    setResult(data)
    return data
  }

  function connectStream(jobId: string) {
    eventSourceRef.current?.close()
    const source = new EventSource(`${apiBaseUrl}/api/v1/analysis/${jobId}/stream`)
    eventSourceRef.current = source

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as EventPayload
      if (payload.error) {
        setError(payload.error)
        addLog({ title: "Stream error", detail: payload.error, tone: "error" })
        return
      }

      setStatus((current) => ({
        status: payload.status ?? current?.status ?? "queued",
        current_node: payload.node ?? current?.current_node ?? null,
        progress_pct: payload.progress ?? current?.progress_pct ?? 0,
        message: payload.message ?? current?.message ?? "Running",
      }))

      if (payload.message) {
        addLog({
          title: payload.node ? payload.node.replaceAll("_", " ") : "Pipeline",
          detail: payload.message,
        })
      }

      if (payload.status === "completed") {
        source.close()
        setBusy(false)
        void fetchResult(jobId).then(() => {
          addLog({
            title: "Report ready",
            detail: "The investment memo is available for download.",
            tone: "success",
          })
        })
      }

      if (payload.status === "failed") {
        source.close()
        setBusy(false)
        setError(payload.message ?? "Pipeline failed")
      }
    }

    source.onerror = () => {
      source.close()
      addLog({
        title: "Stream disconnected",
        detail: "Status polling remains available from the result endpoint.",
        tone: "error",
      })
    }
  }

  async function uploadAndStart() {
    if (!selectedFile) {
      setError("Select a document before starting analysis.")
      return
    }

    setBusy(true)
    setError(null)
    setResult(null)
    setJob(null)
    setUpload(null)
    setStatus({ status: "queued", progress_pct: 0, message: "Queued" })
    setLogs([])

    try {
      const form = new FormData()
      form.append("file", selectedFile)

      addLog({
        title: "Upload started",
        detail: selectedFile.name,
      })

      const uploadResponse = await fetch(`${apiBaseUrl}/api/v1/analysis/upload`, {
        method: "POST",
        body: form,
      })
      if (!uploadResponse.ok) {
        throw new Error(`Upload failed with HTTP ${uploadResponse.status}`)
      }
      const uploadData = (await uploadResponse.json()) as UploadResponse
      setUpload(uploadData)
      addLog({
        title: "Document registered",
        detail: uploadData.content_hash.slice(0, 16),
      })

      const startResponse = await fetch(`${apiBaseUrl}/api/v1/analysis/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: uploadData.document_id }),
      })
      if (!startResponse.ok) {
        throw new Error(`Start failed with HTTP ${startResponse.status}`)
      }
      const startData = (await startResponse.json()) as StartResponse
      setJob(startData)
      addLog({
        title: "Analysis queued",
        detail: startData.job_id,
      })
      connectStream(startData.job_id)
    } catch (err) {
      setBusy(false)
      setError(err instanceof Error ? err.message : "Analysis failed")
    }
  }

  function handleFiles(files: FileList | null) {
    const file = files?.[0]
    if (!file) return
    setSelectedFile(file)
    setError(null)
  }

  return (
    <main className="min-h-svh bg-[#f7f5ef] text-[#191817]">
      <div className="grid min-h-svh lg:grid-cols-[304px_minmax(0,1fr)]">
        <aside className="border-r border-[#d8d1c2] bg-[#fbfaf6] px-5 py-5 lg:sticky lg:top-0 lg:h-svh">
          <div className="flex h-full flex-col justify-between gap-8">
            <div className="space-y-7">
              <div className="flex items-center gap-3">
                <div className="grid size-10 place-items-center rounded-md bg-[#20251f] text-[#e9ff8f]">
                  <Scale className="size-5" />
                </div>
                <div>
                  <div className="text-lg font-semibold tracking-normal">Litigo</div>
                  <div className="text-xs font-medium uppercase tracking-[0.16em] text-[#766f63]">
                    TPLF console
                  </div>
                </div>
              </div>

              <section className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[#766f63]">
                    Backend
                  </span>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium",
                      health
                        ? "bg-[#e4efca] text-[#344512]"
                        : "bg-[#f2ded6] text-[#7b2e1e]"
                    )}
                  >
                    <span className="size-1.5 rounded-full bg-current" />
                    {health ? "Online" : "Offline"}
                  </span>
                </div>
                <label className="grid gap-1.5 text-sm">
                  <span className="text-xs text-[#766f63]">API base URL</span>
                  <input
                    value={apiBaseUrl}
                    onChange={(event) => setApiBaseUrl(event.target.value)}
                    className="h-9 rounded-md border border-[#d8d1c2] bg-white px-3 text-sm outline-none transition focus:border-[#7c8d32] focus:ring-3 focus:ring-[#b8cc5d]/30"
                  />
                </label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => void checkHealth()}
                  className="w-full justify-start"
                >
                  <Activity className="size-4" />
                  Check health
                </Button>
                <div className="min-h-14 rounded-md border border-[#d8d1c2] bg-white/70 p-3 text-xs text-[#5e594f]">
                  {health ? (
                    <div className="space-y-1">
                      <div className="font-medium text-[#272620]">{health.app}</div>
                      <div>{health.model}</div>
                      <div>
                        Gemini {health.gemini_configured ? "configured" : "missing key"}
                      </div>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <AlertCircle className="mt-0.5 size-3.5 shrink-0" />
                      <span>{healthError ?? "No health check yet"}</span>
                    </div>
                  )}
                </div>
              </section>
            </div>

            <div className="rounded-md border border-[#d8d1c2] bg-[#f0eee6] p-3 text-xs leading-5 text-[#5e594f]">
              MVP mode: jobs and files live in backend memory/storage for this first
              deployment.
            </div>
          </div>
        </aside>

        <section className="min-w-0 px-4 py-5 sm:px-6 lg:px-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-5">
            <header className="grid gap-4 border-b border-[#d8d1c2] pb-5 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-end">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 rounded-full border border-[#c9c0ae] bg-white/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-[#766f63]">
                  <ShieldCheck className="size-3.5 text-[#7c8d32]" />
                  Investment committee workspace
                </div>
                <h1 className="max-w-4xl text-4xl font-semibold tracking-normal text-[#171713] sm:text-5xl">
                  Antitrust decision to funded-claim memo.
                </h1>
              </div>
              <div className="grid grid-cols-3 overflow-hidden rounded-md border border-[#d8d1c2] bg-white">
                {[
                  ["Progress", `${Math.round(progress)}%`],
                  ["Job", job ? "Active" : "None"],
                  ["Memo", result?.report_url_docx ? "Ready" : "Pending"],
                ].map(([label, value]) => (
                  <div key={label} className="border-r border-[#e5dfd2] p-3 last:border-r-0">
                    <div className="text-xs text-[#766f63]">{label}</div>
                    <div className="mt-1 text-lg font-semibold text-[#20251f]">{value}</div>
                  </div>
                ))}
              </div>
            </header>

            <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
              <section className="space-y-5">
                <div className="rounded-md border border-[#d8d1c2] bg-white p-4 shadow-sm">
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <div>
                      <h2 className="text-base font-semibold text-[#20251f]">Decision intake</h2>
                      <p className="text-sm text-[#766f63]">PDF, DOCX, or text decision file</p>
                    </div>
                    <FileText className="size-5 text-[#8c1d40]" />
                  </div>

                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    onDragEnter={(event) => {
                      event.preventDefault()
                      setDragActive(true)
                    }}
                    onDragOver={(event) => event.preventDefault()}
                    onDragLeave={() => setDragActive(false)}
                    onDrop={(event) => {
                      event.preventDefault()
                      setDragActive(false)
                      handleFiles(event.dataTransfer.files)
                    }}
                    className={cn(
                      "grid min-h-48 w-full place-items-center rounded-md border border-dashed bg-[#fbfaf6] p-5 text-left transition",
                      dragActive
                        ? "border-[#7c8d32] bg-[#f2f6dd]"
                        : "border-[#c9c0ae] hover:border-[#7c8d32]"
                    )}
                  >
                    <div className="flex max-w-sm flex-col items-center text-center">
                      <div className="mb-4 grid size-12 place-items-center rounded-md bg-[#20251f] text-[#e9ff8f]">
                        <UploadCloud className="size-6" />
                      </div>
                      <div className="text-sm font-semibold text-[#20251f]">
                        {selectedFile ? selectedFile.name : "Select decision file"}
                      </div>
                      <div className="mt-1 text-xs text-[#766f63]">
                        {selectedFile
                          ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`
                          : "Drop file here or open file picker"}
                      </div>
                    </div>
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.txt,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    className="hidden"
                    onChange={(event) => handleFiles(event.target.files)}
                  />

                  <div className="mt-4 grid gap-2 sm:grid-cols-[1fr_auto]">
                    <Button
                      type="button"
                      onClick={() => void uploadAndStart()}
                      disabled={busy || !selectedFile}
                      className="h-10 justify-center bg-[#20251f] text-[#fbfaf6] hover:bg-[#394235]"
                    >
                      {busy ? <Loader2 className="size-4 animate-spin" /> : <Radio className="size-4" />}
                      Run analysis
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setSelectedFile(null)
                        setUpload(null)
                        setJob(null)
                        setStatus(null)
                        setResult(null)
                        setError(null)
                        setLogs([])
                        eventSourceRef.current?.close()
                      }}
                      disabled={busy}
                      className="h-10"
                    >
                      Reset
                    </Button>
                  </div>

                  {error ? (
                    <div className="mt-4 flex gap-2 rounded-md border border-[#e1b8aa] bg-[#fff3ef] p-3 text-sm text-[#7b2e1e]">
                      <AlertCircle className="mt-0.5 size-4 shrink-0" />
                      <span>{error}</span>
                    </div>
                  ) : null}
                </div>

                <div className="rounded-md border border-[#d8d1c2] bg-white p-4 shadow-sm">
                  <h2 className="mb-4 text-base font-semibold text-[#20251f]">Run ledger</h2>
                  <div className="space-y-3">
                    {logs.length ? (
                      logs.map((log) => (
                        <div key={`${log.time}-${log.title}`} className="grid grid-cols-[58px_1fr] gap-3 text-sm">
                          <div className="font-mono text-xs text-[#8d8679]">{log.time}</div>
                          <div>
                            <div
                              className={cn(
                                "font-medium",
                                log.tone === "error" && "text-[#8c1d40]",
                                log.tone === "success" && "text-[#526413]",
                                !log.tone && "text-[#20251f]"
                              )}
                            >
                              {log.title}
                            </div>
                            <div className="truncate text-xs text-[#766f63]">{log.detail}</div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-md bg-[#fbfaf6] p-4 text-sm text-[#766f63]">
                        No active analysis.
                      </div>
                    )}
                  </div>
                </div>
              </section>

              <section className="space-y-5">
                <div className="rounded-md border border-[#d8d1c2] bg-white p-4 shadow-sm">
                  <div className="mb-5 flex items-center justify-between gap-4">
                    <div>
                      <h2 className="text-base font-semibold text-[#20251f]">Pipeline</h2>
                      <p className="text-sm text-[#766f63]">
                        {status?.message ?? "Waiting for analysis"}
                      </p>
                    </div>
                    <div className="min-w-20 text-right">
                      <div className="text-2xl font-semibold text-[#20251f]">
                        {Math.round(progress)}%
                      </div>
                      <div className="text-xs text-[#766f63]">{status?.status ?? "idle"}</div>
                    </div>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-[#ebe5d9]">
                    <div
                      className="h-full rounded-full bg-[#8c1d40] transition-all duration-500"
                      style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
                    />
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {STEPS.map((step, index) => {
                      const Icon = step.icon
                      const done = status?.status === "completed" || index < activeIndex
                      const active = index === activeIndex && status?.status !== "completed"
                      return (
                        <div
                          key={step.key}
                          className={cn(
                            "rounded-md border p-3 transition",
                            done && "border-[#c8d99a] bg-[#f4f8e7]",
                            active && "border-[#8c1d40] bg-[#fff7f5]",
                            !done && !active && "border-[#e1dacd] bg-[#fbfaf6]"
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={cn(
                                "grid size-9 place-items-center rounded-md",
                                done && "bg-[#7c8d32] text-white",
                                active && "bg-[#8c1d40] text-white",
                                !done && !active && "bg-[#ebe5d9] text-[#766f63]"
                              )}
                            >
                              {done ? <CheckCircle2 className="size-4" /> : <Icon className="size-4" />}
                            </div>
                            <div className="min-w-0">
                              <div className="truncate text-sm font-semibold text-[#20251f]">
                                {step.label}
                              </div>
                              <div className="truncate text-xs text-[#766f63]">{step.detail}</div>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
                  <div className="rounded-md border border-[#d8d1c2] bg-white p-4 shadow-sm">
                    <div className="mb-4 flex items-center justify-between">
                      <h2 className="text-base font-semibold text-[#20251f]">Case snapshot</h2>
                      <span className="rounded-full bg-[#f0eee6] px-2.5 py-1 text-xs font-medium text-[#766f63]">
                        {snapshot.caseReference}
                      </span>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      {[
                        ["Jurisdiction", snapshot.jurisdiction],
                        ["Infraction", snapshot.infractionType],
                        ["Company reports", String(snapshot.reports)],
                        ["Selected targets", String(snapshot.selected)],
                      ].map(([label, value]) => (
                        <div key={label} className="rounded-md border border-[#e3ddd0] bg-[#fbfaf6] p-3">
                          <div className="text-xs text-[#766f63]">{label}</div>
                          <div className="mt-1 min-h-6 text-sm font-semibold text-[#20251f]">
                            {value}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="mt-4 grid gap-4 md:grid-cols-2">
                      <div>
                        <div className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-[#766f63]">
                          Affected markets
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {snapshot.affectedMarkets.length ? (
                            snapshot.affectedMarkets.map((market) => (
                              <span
                                key={market}
                                className="rounded-full border border-[#d8d1c2] px-2.5 py-1 text-xs text-[#4d493f]"
                              >
                                {market}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-[#766f63]">Pending extraction</span>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-[#766f63]">
                          Candidates
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {snapshot.candidates.length ? (
                            snapshot.candidates.map((company) => (
                              <span
                                key={company}
                                className="rounded-full bg-[#20251f] px-2.5 py-1 text-xs text-[#fbfaf6]"
                              >
                                {company}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-[#766f63]">Pending sourcing</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-md border border-[#d8d1c2] bg-[#20251f] p-4 text-[#fbfaf6] shadow-sm">
                    <h2 className="text-base font-semibold">Memo exports</h2>
                    <p className="mt-1 text-sm text-[#c7c9b8]">
                      {result?.summary ?? "No completed memo yet."}
                    </p>
                    <div className="mt-5 grid gap-2">
                      {docxUrl ? (
                        <Button
                          asChild
                          className="h-10 justify-start bg-[#e9ff8f] text-[#20251f] hover:bg-[#d6ef74]"
                        >
                          <a href={docxUrl} download>
                            <ArrowDownToLine className="size-4" />
                            Download DOCX
                          </a>
                        </Button>
                      ) : (
                        <Button
                          disabled
                          className="h-10 justify-start bg-[#e9ff8f] text-[#20251f] hover:bg-[#e9ff8f]"
                        >
                          <ArrowDownToLine className="size-4" />
                          Download DOCX
                        </Button>
                      )}
                      {pdfUrl ? (
                        <Button
                          asChild
                          variant="outline"
                          className="h-10 justify-start border-[#777d68] bg-transparent text-[#fbfaf6] hover:bg-[#31382f]"
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
                          className="h-10 justify-start border-[#777d68] bg-transparent text-[#fbfaf6] hover:bg-transparent"
                        >
                          <ArrowDownToLine className="size-4" />
                          Download PDF
                        </Button>
                      )}
                    </div>
                    <div className="mt-5 border-t border-[#485040] pt-4 text-xs leading-5 text-[#c7c9b8]">
                      {upload?.content_hash
                        ? `Content hash ${upload.content_hash.slice(0, 24)}`
                        : "Upload hash will appear after intake."}
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
