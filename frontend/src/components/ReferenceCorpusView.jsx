import React, { useState, useEffect } from "react";
import { BookOpen, Scale, CheckCircle2, AlertTriangle, Layers, ExternalLink } from "lucide-react";
import { fetchReferenceCorpus } from "../services/api";

export default function ReferenceCorpusView() {
  const [corpusData, setCorpusData] = useState(null);
  const [selectedType, setSelectedType] = useState("employment");

  useEffect(() => {
    fetchReferenceCorpus().then(setCorpusData).catch(console.error);
  }, []);

  const templates = corpusData?.templates || {};
  const currentTemplates = templates[selectedType] || {};

  return (
    <div className="flex flex-col h-full overflow-y-auto p-5 text-slate-100 space-y-4">
      {/* Header */}
      <div className="pb-3 border-b border-slate-800">
        <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-indigo-400" />
          Reference Corpus & Commercial Benchmarks (CUAD Standard)
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Preloaded standard contract templates used by the Deviation Detector to identify outlier terms.
        </p>
      </div>

      {/* Contract Type Tabs */}
      <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
        <button
          onClick={() => setSelectedType("employment")}
          className={`px-3 py-1.5 rounded-lg transition font-medium ${
            selectedType === "employment" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Employment Agreement
        </button>
        <button
          onClick={() => setSelectedType("nda")}
          className={`px-3 py-1.5 rounded-lg transition font-medium ${
            selectedType === "nda" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Non-Disclosure (NDA)
        </button>
        <button
          onClick={() => setSelectedType("residential_lease")}
          className={`px-3 py-1.5 rounded-lg transition font-medium ${
            selectedType === "residential_lease" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Residential / Commercial Lease
        </button>
        <button
          onClick={() => setSelectedType("msa")}
          className={`px-3 py-1.5 rounded-lg transition font-medium ${
            selectedType === "msa" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Master Services (MSA)
        </button>
      </div>

      {/* Provenance Disclosure Banner per hackathon constraints */}
      <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/80 text-xs text-slate-400 flex items-center gap-2">
        <Scale className="w-4 h-4 text-indigo-400 shrink-0" />
        <span>
          <strong>Provenance:</strong> {corpusData?.provenance || "Derived from publicly available sample contracts and the CUAD dataset. Preloaded locally as baseline benchmarks without model fine-tuning."}
        </span>
      </div>

      {/* Clause Standard Benchmarks Cards */}
      <div className="space-y-3.5">
        {Object.entries(currentTemplates).map(([catKey, val], idx) => (
          <div
            key={idx}
            className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 space-y-2.5"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs uppercase font-bold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/40">
                  {catKey}
                </span>
                <h3 className="text-xs font-bold text-slate-100">{val.standard_title}</h3>
              </div>
              <span className="text-[11px] text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Template Benchmark
              </span>
            </div>

            <p className="text-xs font-mono text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-900">
              "{val.standard_text}"
            </p>

            {/* Benchmark Metrics */}
            <div className="flex flex-wrap gap-2 text-[11px] text-slate-400">
              {val.standard_notice_days && (
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-indigo-300">
                  Standard Notice: {val.standard_notice_days} days
                </span>
              )}
              {val.standard_duration_months && (
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-indigo-300">
                  Standard Non-Compete: {val.standard_duration_months} months
                </span>
              )}
              {val.standard_cap && (
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-indigo-300">
                  Typical Cap: {val.standard_cap}
                </span>
              )}
              {val.standard_grace_days && (
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-indigo-300">
                  Grace Period: {val.standard_grace_days} days
                </span>
              )}
              {val.standard_late_fee_percent && (
                <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-indigo-300">
                  Standard Late Fee: {val.standard_late_fee_percent}%
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
