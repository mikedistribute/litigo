import Link from "next/link"
import {
  ArrowRight,
  BadgeCheck,
  Building2,
  FileSearch,
  Landmark,
  Layers3,
  Scale,
  Shield,
  Sparkles,
} from "lucide-react"

import { Button } from "@/components/ui/button"

const proof = [
  ["Minutes", "from decision to first memo"],
  ["6 agents", "reading, sourcing, researching, ranking"],
  ["DOCX/PDF", "exports for investment committee review"],
]

const steps = [
  {
    title: "Start with a decision",
    body: "Upload an antitrust ruling, regulatory decision, or claimant-side document.",
    icon: FileSearch,
  },
  {
    title: "Surface fundable exposure",
    body: "Litigo structures the facts, affected markets, and likely commercial harm.",
    icon: Layers3,
  },
  {
    title: "Move to underwriting",
    body: "Receive a concise funding memo with candidate companies and next-step diligence.",
    icon: BadgeCheck,
  },
]

const audiences = [
  "Litigation funders screening claim portfolios",
  "Legal finance analysts mapping affected companies",
  "Investment teams turning public decisions into deal flow",
]

export default function Home() {
  return (
    <main className="min-h-svh bg-[#f5f1e8] text-[#15130f]">
      <section className="relative overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-72 bg-[#15130f]" />
        <div className="relative mx-auto flex min-h-svh max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-8">
          <nav className="flex items-center justify-between rounded-md border border-white/12 bg-[#15130f]/92 px-4 py-3 text-white shadow-2xl shadow-black/20 backdrop-blur">
            <Link href="/" className="flex items-center gap-2.5">
              <span className="grid size-8 place-items-center rounded-md bg-[#d7ff55] text-[#15130f]">
                <Scale className="size-4" />
              </span>
              <span className="text-base font-semibold">Litigo</span>
            </Link>
            <div className="hidden items-center gap-6 text-sm text-white/70 md:flex">
              <a href="#product" className="transition hover:text-white">
                Product
              </a>
              <a href="#intelligence" className="transition hover:text-white">
                Intelligence
              </a>
              <a href="#workflow" className="transition hover:text-white">
                Workflow
              </a>
            </div>
            <Button
              asChild
              className="h-9 rounded-md bg-white px-4 text-[#15130f] hover:bg-[#d7ff55]"
            >
              <Link href="/app">
                Open app
                <ArrowRight className="size-4" />
              </Link>
            </Button>
          </nav>

          <div className="grid flex-1 items-center gap-10 py-14 lg:grid-cols-[minmax(0,0.95fr)_minmax(440px,1fr)] lg:py-20">
            <div className="max-w-3xl pt-10 text-white lg:pt-0">
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/14 bg-white/8 px-3 py-1 text-sm text-white/76">
                <Sparkles className="size-4 text-[#d7ff55]" />
                Legal finance intelligence for TPLF teams
              </div>
              <h1 className="text-5xl font-semibold leading-[0.94] tracking-normal sm:text-6xl lg:text-7xl">
                Turn legal exposure into fundable opportunities.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-white/72">
                Litigo reads high-stakes legal decisions, identifies affected markets,
                sources companies, and prepares an investment memo your fund can
                actually review.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button
                  asChild
                  className="h-11 rounded-md bg-[#d7ff55] px-5 text-[#15130f] hover:bg-[#c7ef42]"
                >
                  <Link href="/app">
                    Analyze a decision
                    <ArrowRight className="size-4" />
                  </Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="h-11 rounded-md border-white/18 bg-transparent px-5 text-white hover:bg-white/10 hover:text-white"
                >
                  <a href="#product">See product</a>
                </Button>
              </div>
            </div>

            <div id="product" className="relative">
              <div className="rounded-md border border-[#dbd3c2] bg-[#fbf8ef] p-3 shadow-2xl shadow-black/22">
                <div className="rounded-md border border-[#27231b]/10 bg-white">
                  <div className="flex items-center justify-between border-b border-[#e8e0d1] px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="size-2 rounded-full bg-[#d54d2a]" />
                      <span className="size-2 rounded-full bg-[#e7b936]" />
                      <span className="size-2 rounded-full bg-[#1b8f61]" />
                    </div>
                    <div className="text-xs font-medium uppercase tracking-[0.16em] text-[#756d60]">
                      Claim screen
                    </div>
                  </div>
                  <div className="grid gap-0 md:grid-cols-[0.9fr_1.1fr]">
                    <div className="border-b border-[#e8e0d1] p-5 md:border-b-0 md:border-r">
                      <div className="text-xs font-semibold uppercase tracking-[0.14em] text-[#756d60]">
                        Uploaded decision
                      </div>
                      <div className="mt-4 rounded-md bg-[#15130f] p-4 text-white">
                        <div className="mb-10 flex items-center justify-between text-xs text-white/54">
                          <span>EU competition ruling</span>
                          <span>PDF</span>
                        </div>
                        <div className="space-y-2">
                          <div className="h-2 w-10/12 rounded-full bg-white/28" />
                          <div className="h-2 w-8/12 rounded-full bg-white/18" />
                          <div className="h-2 w-11/12 rounded-full bg-white/18" />
                        </div>
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-3">
                        <div className="rounded-md border border-[#e1d8c7] bg-[#f8f3e8] p-3">
                          <div className="text-2xl font-semibold">14</div>
                          <div className="text-xs text-[#756d60]">markets parsed</div>
                        </div>
                        <div className="rounded-md border border-[#e1d8c7] bg-[#f8f3e8] p-3">
                          <div className="text-2xl font-semibold">38</div>
                          <div className="text-xs text-[#756d60]">targets found</div>
                        </div>
                      </div>
                    </div>
                    <div className="p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-[0.14em] text-[#756d60]">
                            Investment memo
                          </div>
                          <h2 className="mt-2 max-w-sm text-3xl font-semibold leading-tight">
                            Funding thesis, ranked targets, and diligence notes.
                          </h2>
                        </div>
                        <span className="rounded-full bg-[#d7ff55] px-3 py-1 text-xs font-semibold">
                          Ready
                        </span>
                      </div>
                      <div className="mt-7 space-y-3">
                        {[
                          ["Exposure", "Overcharge theory mapped to claimant categories"],
                          ["Markets", "Public procurement, logistics, downstream buyers"],
                          ["Priority", "High-value companies ranked by harm and recoverability"],
                        ].map(([label, text]) => (
                          <div key={label} className="rounded-md border border-[#e1d8c7] p-3">
                            <div className="text-xs font-semibold text-[#8f2f20]">{label}</div>
                            <div className="mt-1 text-sm text-[#3b372f]">{text}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-[#ded5c5] bg-[#fbf8ef]">
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-6 sm:px-6 md:grid-cols-3 lg:px-8">
          {proof.map(([value, label]) => (
            <div key={label} className="flex items-baseline gap-3">
              <div className="text-3xl font-semibold">{value}</div>
              <div className="max-w-44 text-sm leading-5 text-[#676054]">{label}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="intelligence" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-[0.82fr_1.18fr]">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-[#15130f] px-3 py-1 text-sm text-white">
              <Landmark className="size-4 text-[#d7ff55]" />
              Built for legal finance
            </div>
            <h2 className="text-4xl font-semibold leading-tight sm:text-5xl">
              Most litigation tools arrive after the opportunity is obvious.
            </h2>
            <p className="mt-5 text-lg leading-8 text-[#676054]">
              Litigo works upstream: it turns public legal decisions into structured
              funding intelligence before a claim pipeline becomes crowded.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {steps.map((step) => {
              const Icon = step.icon
              return (
                <article
                  key={step.title}
                  className="rounded-md border border-[#ded5c5] bg-[#fbf8ef] p-5"
                >
                  <div className="mb-8 grid size-10 place-items-center rounded-md bg-[#15130f] text-[#d7ff55]">
                    <Icon className="size-5" />
                  </div>
                  <h3 className="text-xl font-semibold">{step.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-[#676054]">{step.body}</p>
                </article>
              )
            })}
          </div>
        </div>
      </section>

      <section id="workflow" className="bg-[#15130f] text-white">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[1fr_0.9fr] lg:px-8">
          <div>
            <div className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-[#d7ff55]">
              Who it serves
            </div>
            <h2 className="max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
              A cleaner front door for the work your analysts already do manually.
            </h2>
          </div>
          <div className="space-y-3">
            {audiences.map((audience) => (
              <div key={audience} className="flex items-center gap-3 border-b border-white/12 py-4">
                <Shield className="size-5 text-[#d7ff55]" />
                <span className="text-lg text-white/82">{audience}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_auto] lg:items-center lg:px-8">
        <div>
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#8f2f20]">
            <Building2 className="size-4" />
            Litigo for funds
          </div>
          <h2 className="text-4xl font-semibold">Start with one decision.</h2>
          <p className="mt-3 max-w-2xl text-[#676054]">
            Upload a file, run the analysis, and get a memo your team can use as
            the first pass for underwriting.
          </p>
        </div>
        <Button
          asChild
          className="h-11 rounded-md bg-[#15130f] px-5 text-white hover:bg-[#2c281f]"
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
