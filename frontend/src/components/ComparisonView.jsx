import React, { useState } from "react";
import { GitCompare, ArrowRight, Check, AlertOctagon, PlusCircle, MinusCircle, RefreshCw } from "lucide-react";
import AttentionBadge from "./AttentionBadge";
import ConfidenceBadge from "./ConfidenceBadge";
import { compareContracts } from "../services/api";

export default function ComparisonView({ onSelectClause }) {
  const [filter, setFilter] = useState("all");
  const [comparisonData, setComparisonData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRunSampleComparison = async () => {
    setIsLoading(true);
    try {
      // Runs comparison between pre-loaded MSA V1 (Original) and MSA V2 (Revised Draft)
      const data = await compareContracts(null, null, null, null);
      setComparisonData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const items = comparisonData?.items || [];

  const filteredItems = items.filter((item) => {
    if (filter === "material") return item.change_flag.includes("Material");
    if (filter === "minor") return item.change_flag.includes("Minor");
    if (filter === "added") return item.change_flag.includes("Added");
    if (filter === "removed") return item.change_flag.includes("Removed");
    return true;
  });

  return (
    <div className="flex flex-col h-full overflow-y-auto p-5 text-slate-100 space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-indigo-400" />
            Semantic Contract Comparison (Version A vs. Version B)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Semantic clause-to-clause alignment (not raw text diffing). Handles reordered and reworded covenants.
          </p>
        </div>

        <button
          onClick={handleRunSampleComparison}
          disabled={isLoading}
          aria-label="Compare Sample Master Services Agreement Version 1 versus Version 2"
          className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} aria-hidden="true" />
          <span>{comparisonData ? "Re-Run MSA Comparison" : "Compare Sample MSA V1 vs. V2"}</span>
        </button>
      </div>

      {!comparisonData && !isLoading ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-8 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-indigo-950 flex items-center justify-center mx-auto text-indigo-400 border border-indigo-500/30" aria-hidden="true">
            <GitCompare className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-200">Ready to Compare Contract Versions</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">
              Click above to launch semantic clause-by-clause comparison between Version 1 (Baseline MSA) and Version 2 (Revised Mark-up with altered liability caps and payment terms).
            </p>
          </div>
        </div>
      ) : null}

      {/* Filter Tabs */}
      {comparisonData && (
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div
            role="tablist"
            aria-label="Filter contract comparison clauses by change type"
            className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs"
          >
            <button
              role="tab"
              aria-selected={filter === "all"}
              onClick={() => setFilter("all")}
              className={`px-3 py-1 rounded-lg transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                filter === "all" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              All Clauses ({items.length})
            </button>
            <button
              role="tab"
              aria-selected={filter === "material"}
              onClick={() => setFilter("material")}
              className={`px-3 py-1 rounded-lg transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 ${
                filter === "material" ? "bg-rose-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              🔴 Material Changes ({items.filter((i) => i.change_flag.includes("Material")).length})
            </button>
            <button
              role="tab"
              aria-selected={filter === "added"}
              onClick={() => setFilter("added")}
              className={`px-3 py-1 rounded-lg transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 ${
                filter === "added" ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Added ({items.filter((i) => i.change_flag.includes("Added")).length})
            </button>
            <button
              role="tab"
              aria-selected={filter === "removed"}
              onClick={() => setFilter("removed")}
              className={`px-3 py-1 rounded-lg transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 ${
                filter === "removed" ? "bg-amber-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Removed ({items.filter((i) => i.change_flag.includes("Removed")).length})
            </button>
          </div>

          <span className="text-[11px] text-slate-400 italic">
            {comparisonData.disclaimer}
          </span>
        </div>
      )}

      {/* Comparison Items Grid */}
      <div className="space-y-4">
        {filteredItems.map((item, idx) => {
          const isMaterial = item.change_flag.includes("Material");
          const isAdded = item.change_flag.includes("Added");
          const isRemoved = item.change_flag.includes("Removed");

          return (
            <div
              key={idx}
              className={`rounded-2xl p-4 border transition-all duration-200 ${
                isMaterial
                  ? "bg-slate-900/90 border-rose-500/40 shadow-sm shadow-rose-950/20"
                  : isAdded
                  ? "bg-slate-900/90 border-emerald-500/40"
                  : isRemoved
                  ? "bg-slate-900/90 border-amber-500/40"
                  : "bg-slate-900/60 border-slate-800"
              }`}
            >
              {/* Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-100">{item.title}</h3>
                  <span className="text-[11px] uppercase font-semibold text-slate-400 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                    {item.category}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                      isMaterial
                        ? "bg-rose-950 text-rose-300 border-rose-500/50"
                        : isAdded
                        ? "bg-emerald-950 text-emerald-300 border-emerald-500/50"
                        : isRemoved
                        ? "bg-amber-950 text-amber-300 border-amber-500/50"
                        : "bg-slate-800 text-slate-300 border-slate-700"
                    }`}
                  >
                    {item.change_flag}
                  </span>
                  <ConfidenceBadge level={item.confidence} inline />
                </div>
              </div>

              {/* Semantic Delta Explanation */}
              <div className="bg-slate-950/70 p-3 rounded-xl border border-slate-800 mb-3 text-xs text-slate-200 leading-relaxed">
                <strong className="text-indigo-300 mr-1">Semantic Delta:</strong>
                {item.semantic_delta}
              </div>

              {/* Side-by-Side Clause Texts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                {/* Version A (Original) */}
                <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                  <div className="flex items-center justify-between mb-1.5 text-[11px] text-slate-400 font-sans font-bold">
                    <span>Version A (Original)</span>
                    {item.version_a_clause_id && (
                      <span className="text-indigo-400">{item.version_a_clause_id}</span>
                    )}
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed whitespace-pre-wrap">
                    {item.version_a_text || "(Clause not present in Version A)"}
                  </p>
                </div>

                {/* Version B (Revised) */}
                <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/80">
                  <div className="flex items-center justify-between mb-1.5 text-[11px] text-slate-400 font-sans font-bold">
                    <span>Version B (Revised Draft)</span>
                    {item.version_b_clause_id && (
                      <span className="text-emerald-400">{item.version_b_clause_id}</span>
                    )}
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed whitespace-pre-wrap">
                    {item.version_b_text || "(Clause deleted in Version B)"}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
