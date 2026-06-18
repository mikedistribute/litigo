import Link from "next/link"
import {
  ArrowRight,
  BadgeCheck,
  BrainCircuit,
  Building2,
  FileSearch,
  Scale,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react"

import { Button } from "@/components/ui/button"

const proof = [
  ["Decision in", "Upload PDF, DOCX, or TXT rulings"],
  ["Memo out", "Investment-ready DOCX and PDF exports"],
  ["Agents inside", "Extraction, sourcing, research, ranking, writing"],
]

const workflow = [
  {
    title: "Legal signal extraction",
    body: "Litigo reads the decision, isolates the legal theory, affected markets, jurisdictions, and commercial facts.",
    icon: FileSearch,
  },
  {
    title: "Claimant universe mapping",
    body: "The system sources companies likely affected by the conduct and structures the first diligence view.",
    icon: Workflow,
  },
  {
    title: "Funding memo generation",
    body: "Your team receives a concise memo with thesis, targets, risks, and exportable material for review.",
    icon: BadgeCheck,
  },
]

const capabilities = [
  "Antitrust and regulatory decision intake",
  "Affected market and claimant category extraction",
  "Target company sourcing and research",
  "Investment committee memo generation",
]

export default function Home() {
  return (
    <main className="min-h-svh bg-white text-slate-950">
      <section className="relative overflow-hidden border-b border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#eef6ff_52%,#ffffff_100%)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(37,99,235,0.16),transparent_36%)]" />
        <div className="relative mx-auto flex min-h-svh max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
          <nav className="flex items-center justify-between rounded-md border border-slate-200 bg-white/82 px-4 py-3 shadow-sm shadow-blue-950/5 backdrop-blur-xl">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="grid size-8 place-items-center rounded-md bg-blue-600 text-white shadow-lg shadow-blue-600/25">
                <Scale className="size-4" />
              </span>
              <span className="text-base font-semibold tracking-tight">Litigo</span>
            </Link>
            <div className="hidden items-center gap-7 text-sm font-medium text-slate-600 md:flex">
              <a href="#platform" className="transition hover:text-blue-700">
                Platform
              </a>
              <a href="#workflow" className="transition hover:text-blue-700">
                Workflow
              </a>
              <a href="#security" className="transition hover:text-blue-700">
                Security
              </a>
            </div>
            <Button
              asChild
              className="h-9 rounded-md bg-slate-950 px-4 text-white hover:bg-blue-700"
            >
              <Link href="/app">
                Open app
                <ArrowRight className="size-4" />
              </Link>
            </Button>
          </nav>

          <div className="grid flex-1 items-center gap-12 py-16 lg:grid-cols-[0.92fr_1.08fr] lg:py-20">
            <div className="max-w-3xl">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-800">
                <Sparkles className="size-4" />
                AI agents for litigation finance workflows
              </div>
              <h1 className="max-w-4xl text-5xl font-semibold leading-[0.96] tracking-normal text-slate-950 sm:text-6xl lg:text-7xl">
                Turn legal decisions into fundable claim intelligence.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
                Litigo automates the first pass of TPLF diligence: read the ruling,
                identify affected markets, source potential claimants, and generate
                a memo for investment review.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button
                  asChild
                  className="h-11 rounded-md bg-blue-600 px-5 text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700"
                >
                  <Link href="/app">
                    Analyze a decision
                    <ArrowRight className="size-4" />
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="h-11 rounded-md border-slate-300 bg-white px-5 text-slate-900 hover:bg-slate-50"
                >
                  <a href="#platform">See platform</a>
                </Button>
              </div>
            </div>

            <div id="platform" className="relative">
              <div className="rounded-md border border-slate-200 bg-white p-3 shadow-2xl shadow-blue-950/12">
                <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
                  <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="size-2 rounded-full bg-red-400" />
                      <span className="size-2 rounded-full bg-amber-400" />
                      <span className="size-2 rounded-full bg-emerald-500" />
                    </div>
                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Live diligence workspace
                    </div>
                  </div>
                  <div className="grid gap-0 lg:grid-cols-[0.86fr_1.14fr]">
                    <div className="border-b border-slate-200 bg-[linear-gradient(180deg,#f8fbff,#eef6ff)] p-5 lg:border-b-0 lg:border-r">
                      <div className="mb-4 flex items-center justify-between">
                        <div className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-700">
                          Source document
                        </div>
                        <span className="rounded-full bg-white px-2.5 py-1 text-xs font-medium text-slate-600 shadow-sm">
                          PDF
                        </span>
                      </div>
                      <div className="rounded-md border border-blue-100 bg-white p-4 shadow-sm">
                        <div className="mb-12 flex items-center gap-3">
                          <div className="grid size-10 place-items-center rounded-md bg-blue-600 text-white">
                            <FileSearch className="size-5" />
                          </div>
                          <div>
                            <div className="text-sm font-semibold">Competition ruling</div>
                            <div className="text-xs text-slate-500">1,234 characters extracted</div>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="h-2 w-11/12 rounded-full bg-slate-200" />
                          <div className="h-2 w-8/12 rounded-full bg-slate-200" />
                          <div className="h-2 w-10/12 rounded-full bg-slate-200" />
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-3">
                        <div className="rounded-md border border-blue-100 bg-white p-3 shadow-sm">
                          <div className="text-2xl font-semibold text-slate-950">14</div>
                          <div className="text-xs text-slate-500">markets parsed</div>
                        </div>
                        <div className="rounded-md border border-blue-100 bg-white p-3 shadow-sm">
                          <div className="text-2xl font-semibold text-slate-950">38</div>
                          <div className="text-xs text-slate-500">targets found</div>
                        </div>
                      </div>
                    </div>
                    <div className="p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-blue-700">
                            Investment memo
                          </div>
                          <h2 className="mt-2 max-w-sm text-3xl font-semibold leading-tight text-slate-950">
                            Ranked claim opportunities for underwriting.
                          </h2>
                        </div>
                        <span className="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">
                          Ready
                        </span>
                      </div>
                      <div className="mt-7 space-y-3">
                        {[
                          ["Exposure", "Commercial harm mapped to claimant categories"],
                          ["Markets", "Procurement, logistics, and downstream buyers"],
                          ["Priority", "Targets ranked by value, evidence, and recoverability"],
                        ].map(([label, text]) => (
                          <div key={label} className="rounded-md border border-slate-200 bg-white p-3 shadow-sm">
                            <div className="text-xs font-semibold text-blue-700">{label}</div>
                            <div className="mt-1 text-sm text-slate-600">{text}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-3 border-t border-slate-200 py-6 md:grid-cols-3">
            {proof.map(([value, label]) => (
              <div key={label} className="rounded-md border border-slate-200 bg-white/78 p-4 shadow-sm shadow-blue-950/4">
                <div className="text-sm font-semibold text-blue-700">{value}</div>
                <div className="mt-1 text-sm text-slate-600">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.78fr_1.22fr]">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1 text-sm text-white">
              <BrainCircuit className="size-4 text-blue-300" />
              End-to-end agent workflow
            </div>
            <h2 className="max-w-xl text-4xl font-semibold leading-tight text-slate-950 sm:text-5xl">
              Not another document viewer. A claim-screening workflow.
            </h2>
            <p className="mt-5 text-lg leading-8 text-slate-600">
              The first version focuses on one high-value path: transform a legal
              decision into structured funding intelligence your team can review.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {workflow.map((step) => {
              const Icon = step.icon
              return (
                <article key={step.title} className="rounded-md border border-slate-200 bg-white p-5 shadow-sm shadow-blue-950/5">
                  <div className="mb-8 grid size-10 place-items-center rounded-md bg-blue-50 text-blue-700">
                    <Icon className="size-5" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-950">{step.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{step.body}</p>
                </article>
              )
            })}
          </div>
        </div>
      </section>

      <section id="security" className="border-y border-slate-200 bg-slate-950 text-white">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[0.95fr_1.05fr] lg:px-8">
          <div>
            <div className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-blue-300">
              Built for diligence teams
            </div>
            <h2 className="max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
              Legal finance work needs speed, evidence, and clean handoff.
            </h2>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">
              Litigo gives analysts a first-pass operating layer for claim discovery,
              not a generic chat surface.
            </p>
          </div>
          <div className="grid gap-3">
            {capabilities.map((capability) => (
              <div key={capability} className="flex items-center gap-3 rounded-md border border-white/10 bg-white/5 p-4">
                <ShieldCheck className="size-5 text-blue-300" />
                <span className="text-base text-slate-100">{capability}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_auto] lg:items-center lg:px-8">
        <div>
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-blue-700">
            <Building2 className="size-4" />
            Litigo for funds
          </div>
          <h2 className="text-4xl font-semibold text-slate-950">Start with one decision.</h2>
          <p className="mt-3 max-w-2xl text-slate-600">
            Upload a file, run the analysis, and download a memo your team can use
            as the first pass for underwriting.
          </p>
        </div>
        <Button
          asChild
          className="h-11 rounded-md bg-blue-600 px-5 text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700"
        >
          <Link href="/app">
            Open Litigo
            <ArrowRight className="size-4" />
          </Link>
        </Button>
      </section>
    </main>
  )
}
