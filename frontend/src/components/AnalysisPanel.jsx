import React, { useState } from "react";
import {
  AlertTriangle,
  HelpCircle,
  Link2,
  FileCheck,
  Scale,
  Sparkles,
  Calendar,
  DollarSign,
  Users,
  ShieldAlert,
  ArrowRight,
  Info,
} from "lucide-react";
import AttentionBadge from "./AttentionBadge";
import ConfidenceBadge from "./ConfidenceBadge";

export default function AnalysisPanel({
  clause,
  readingLevel = "general",
  onSelectClause,
  allEdges = [],
}) {
  const [activeReadingLevel, setActiveReadingLevel] = useState(readingLevel);

  if (!clause) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-slate-400">
        <Scale className="w-12 h-12 text-slate-600 mb-3" />
        <h3 className="text-base font-medium text-slate-200">No Clause Selected</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm">
          Select any clause from the left document pane or click an evidence citation in Q&A to view deep legal reasoning.
        </p>
      </div>
    );
  }

  // Find graph edges connected to this clause
  const connectedEdges = allEdges.filter(
    (e) => e.source === clause.id || e.target === clause.id
  );

  const plainLanguageText =
    clause.plain_language?.[activeReadingLevel] ||
    clause.plain_language?.["general"] ||
    "Plain language rewrite in progress...";

  return (
    <div className="flex flex-col h-full overflow-y-auto p-5 space-y-5 text-slate-100">
      {/* Top Banner: Attention & Confidence */}
      <div className="bg-slate-900/90 rounded-2xl p-4 border border-slate-800 shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-md bg-indigo-950 text-indigo-300 border border-indigo-500/40">
              {clause.id}
            </span>
            <h2 className="text-base font-bold text-slate-100">{clause.title}</h2>
          </div>
          <div className="flex items-center gap-2">
            <AttentionBadge level={clause.attention_level} />
            <ConfidenceBadge
              level={clause.confidence}
              reasoning={clause.verification_reasoning}
            />
          </div>
        </div>

        {/* Disclaimer per requirement */}
        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800/80">
          <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
          <span>{clause.disclaimer}</span>
        </div>
      </div>

      {/* Why Flagged (Explicit Reasoning) */}
      <div className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800/80 space-y-2.5">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-300">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span>Why Flagged (Evidence-Grounded Reasoning)</span>
        </div>

        <ul className="space-y-2 text-xs text-slate-200">
          {clause.attention_reasons?.map((reason, idx) => (
            <li key={idx} className="flex items-start gap-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-900">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-1.5 shrink-0"></span>
              <span className="leading-relaxed">{reason}</span>
            </li>
          ))}
        </ul>

        {/* Entailment Verification Note */}
        {clause.verification_reasoning && (
          <div className="mt-2 text-[11px] text-slate-400 bg-slate-950/50 p-2 rounded-lg border border-slate-800 flex items-center justify-between">
            <span className="italic">Verification Pass: {clause.verification_reasoning}</span>
            <ConfidenceBadge level={clause.confidence} inline />
          </div>
        )}
      </div>

      {/* Reference Corpus Deviation Check */}
      {clause.deviation_check && (
        <div className="bg-indigo-950/30 rounded-2xl p-4 border border-indigo-500/30 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-300">
            <FileCheck className="w-4 h-4 text-indigo-400" />
            <span>Reference Corpus Benchmark (CUAD Baseline)</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/50 p-3 rounded-xl border border-indigo-950">
            {clause.deviation_check}
          </p>
        </div>
      )}

      {/* Plain Language Rewrite with Reading Level Tabs */}
      <div className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-300">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>Plain-Language Synthesis</span>
          </div>

          {/* Reading Level Pills */}
          <div className="flex bg-slate-950 p-0.5 rounded-lg border border-slate-800 text-[11px]">
            <button
              onClick={() => setActiveReadingLevel("general")}
              className={`px-2.5 py-1 rounded-md transition font-medium ${
                activeReadingLevel === "general"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              8th Grade
            </button>
            <button
              onClick={() => setActiveReadingLevel("executive")}
              className={`px-2.5 py-1 rounded-md transition font-medium ${
                activeReadingLevel === "executive"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Executive
            </button>
            <button
              onClick={() => setActiveReadingLevel("technical")}
              className={`px-2.5 py-1 rounded-md transition font-medium ${
                activeReadingLevel === "technical"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Paralegal
            </button>
          </div>
        </div>

        <div className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-200 leading-relaxed">
          {plainLanguageText}
        </div>
      </div>

      {/* Connected Clause Graph Edges */}
      {connectedEdges.length > 0 && (
        <div className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800/80 space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-300">
            <Link2 className="w-4 h-4 text-cyan-400" />
            <span>Clause Graph Connections ({connectedEdges.length})</span>
          </div>

          <div className="space-y-2">
            {connectedEdges.map((edge, idx) => {
              const otherId = edge.source === clause.id ? edge.target : edge.source;
              const isOutgoing = edge.source === clause.id;
              return (
                <div
                  key={idx}
                  onClick={() => onSelectClause(otherId)}
                  className="flex items-center justify-between p-2.5 bg-slate-950/50 hover:bg-slate-800/60 rounded-xl border border-slate-800 transition cursor-pointer group"
                >
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-mono font-semibold px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-800/40">
                      {edge.relation}
                    </span>
                    <span className="text-slate-300 group-hover:text-cyan-200 transition">
                      {edge.description}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-cyan-400 shrink-0">
                    <span>Jump</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Structured Entities Extracted */}
      <div className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800/80 space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Structured Clause Entities
        </h4>

        <div className="grid grid-cols-2 gap-3 text-xs">
          {/* Parties */}
          <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-900">
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1 font-semibold">
              <Users className="w-3.5 h-3.5 text-indigo-400" />
              <span>Parties Involved</span>
            </div>
            <div className="text-slate-200 font-medium">
              {clause.fields?.parties_involved?.join(", ") || "Both Parties"}
            </div>
          </div>

          {/* Dates */}
          <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-900">
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1 font-semibold">
              <Calendar className="w-3.5 h-3.5 text-emerald-400" />
              <span>Dates & Timeframes</span>
            </div>
            <div className="text-slate-200 font-medium">
              {clause.fields?.dates?.join(", ") || "Standard / None specified"}
            </div>
          </div>

          {/* Monetary */}
          <div className="bg-slate-950/50 p-2.5 rounded-xl border border-slate-900 col-span-2">
            <div className="flex items-center gap-1.5 text-slate-400 text-[11px] mb-1 font-semibold">
              <DollarSign className="w-3.5 h-3.5 text-amber-400" />
              <span>Financial Figures & Penalties</span>
            </div>
            <div className="text-slate-200 font-medium">
              {clause.fields?.monetary_amounts?.join(", ") || "No explicit amounts stated"}
            </div>
          </div>
        </div>
      </div>

      {/* Questions for Your Lawyer */}
      <div className="bg-slate-900/80 rounded-2xl p-4 border border-slate-800/80 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-300">
          <HelpCircle className="w-4 h-4 text-amber-400" />
          <span>Questions for Your Lawyer</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-900">
          "What is the enforceable market radius and severance compensation standard for covenants in {clause.title} under governing state law?"
        </p>
      </div>
    </div>
  );
}
