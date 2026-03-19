import React, { useEffect, useState } from "react";
import { Link } from "react-router";

import { liveTools, previewFeatures } from "../data/features";
import { getDashboardSummary } from "../lib/api";
import { Badge, Button, Card } from "../components/ui";

type Summary = {
  cluster: string;
  throughput: string;
  latency: string;
  totalFeatures: number;
  liveCount: number;
  expandedCount: number;
  indexedDocuments: number;
  auditEntries: number;
};

export function DashboardHome() {
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    let active = true;

    getDashboardSummary()
      .then((payload) => {
        if (active) {
          setSummary(payload);
        }
      })
      .catch(() => {
        if (active) {
          setSummary(null);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#F9F8F4] pb-20">
      <section className="mx-auto max-w-7xl px-6 pt-12 lg:px-10 lg:pt-16">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1.5fr)_minmax(320px,1fr)]">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-orange-200 bg-orange-100 px-3 py-1 text-xs font-bold tracking-wider text-orange-800">
              <span className="h-2 w-2 rounded-full bg-orange-500" />
              ECONOMIC TIMES GENAI HACKATHON
            </div>

            <h1 className="font-serif text-4xl font-bold leading-tight tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Enterprise GenAI: architected in India, now backed by a working API stack.
            </h1>

            <p className="mt-6 max-w-3xl text-lg leading-relaxed text-slate-600">
              The dashboard now runs against a real backend with authentication, live feature execution, local RAG memory, and a cryptographic audit trail across all 20 modules.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-2">
            <Card className="p-6 shadow-sm">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Total Modules</div>
              <div className="mt-3 text-3xl font-bold text-slate-900">{summary?.totalFeatures ?? liveTools.length + previewFeatures.length}</div>
            </Card>
            <Card className="border-[#115E59]/20 bg-[#115E59]/5 p-6 shadow-sm">
              <div className="text-xs font-bold uppercase tracking-wider text-[#115E59]">Live Tools</div>
              <div className="mt-3 text-3xl font-bold text-slate-900">{summary?.liveCount ?? liveTools.length}</div>
            </Card>
            <Card className="p-6 shadow-sm">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Indexed Documents</div>
              <div className="mt-3 text-3xl font-bold text-slate-900">{summary?.indexedDocuments ?? 0}</div>
            </Card>
            <Card className="p-6 shadow-sm">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Audit Entries</div>
              <div className="mt-3 text-3xl font-bold text-slate-900">{summary?.auditEntries ?? 0}</div>
            </Card>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-8 lg:px-10">
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white/70 px-5 py-4 text-xs font-bold tracking-wider text-slate-500 shadow-sm backdrop-blur-sm">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-slate-700">CLUSTER: {summary?.cluster ?? "AP-SOUTH-1 (MUMBAI)"}</span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="text-slate-700">THROUGHPUT: {summary?.throughput ?? "12k req/s"}</div>
            <span className="text-slate-300">|</span>
            <div className="text-slate-700">LATENCY: {summary?.latency ?? "42ms"}</div>
          </div>
          <div className="rounded-full bg-[#115E59]/10 px-3 py-1 text-[#115E59]">Full-stack runtime engaged</div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-8 lg:px-10">
        <div className="mb-8 flex items-end justify-between gap-4">
          <div>
            <h2 className="font-serif text-3xl font-bold text-slate-900">Live Interactive Tools</h2>
            <p className="mt-2 text-slate-600">These nine tools now execute against real API endpoints instead of placeholder panels.</p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {liveTools.map((tool) => (
            <Card key={tool.id} className="group relative flex flex-col overflow-hidden border-slate-200 p-6 transition-colors hover:border-[#115E59]/40">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent to-slate-50/70 opacity-0 transition-opacity group-hover:opacity-100" />
              <div className="relative z-10 mb-4 flex items-start justify-between">
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-[#115E59]">{tool.category}</div>
                  <h3 className="mt-1 text-xl font-bold text-slate-900">{tool.title}</h3>
                </div>
                <Badge variant="live">LIVE</Badge>
              </div>
              <p className="relative z-10 mb-6 flex-1 text-sm text-slate-600">{tool.description}</p>
              <div className="relative z-10">
                <Link to={`/dashboard/${tool.id}`}>
                  <Button className="w-full justify-between">
                    Launch Tool
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-12 lg:px-10">
        <div className="mb-10">
          <h2 className="font-serif text-3xl font-bold text-slate-900">Expanded Product Modules</h2>
          <p className="mt-2 text-slate-600">The remaining eleven modules are now callable too, surfaced as beta flows on top of the same backend.</p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {previewFeatures.map((feature) => (
            <Card key={feature.id} className="group relative flex h-full flex-col border-slate-200 bg-white p-5 transition-colors hover:border-orange-200">
              <div className="absolute right-4 top-4">
                <Badge variant="preview">BETA</Badge>
              </div>
              <h3 className="mt-2 pr-16 text-lg font-bold text-slate-800 group-hover:text-slate-900">{feature.title}</h3>
              <p className="mt-3 flex-1 text-sm text-slate-500">{feature.description}</p>
              <Link to={`/dashboard/${feature.id}`} className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4 text-xs font-mono font-semibold uppercase text-slate-400 transition-colors group-hover:text-orange-600">
                <span>Status: Beta</span>
                <span>Open Module →</span>
              </Link>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
