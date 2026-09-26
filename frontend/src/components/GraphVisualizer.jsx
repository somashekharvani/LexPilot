import React, { useState } from "react";
import { Network, Link2, AlertTriangle, ArrowRight, ShieldCheck, Zap } from "lucide-react";
import AttentionBadge from "./AttentionBadge";
import ConfidenceBadge from "./ConfidenceBadge";

export default function GraphVisualizer({ clauses = [], edges = [], conflicts = [], onSelectClause }) {
  const [selectedRelation, setSelectedRelation] = useState("all");

  const filteredEdges = edges.filter((e) => {
    if (selectedRelation === "all") return true;
    return e.relation === selectedRelation;
  });

  return (
    <div className="flex flex-col h-full overflow-y-auto p-5 text-slate-100 space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Network className="w-4 h-4 text-cyan-400" />
            In-Memory Clause Graph & Multi-Hop Network ({clauses.length} Nodes, {edges.length} Edges)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Inter-clause references, survival mandates, conditional dependencies, and detected conflicts.
          </p>
        </div>

        {/* Filter by relation */}
        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setSelectedRelation("all")}
            className={`px-3 py-1 rounded-lg transition font-medium ${
              selectedRelation === "all" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            All Edges ({edges.length})
          </button>
          <button
            onClick={() => setSelectedRelation("SURVIVES")}
            className={`px-3 py-1 rounded-lg transition font-medium ${
              selectedRelation === "SURVIVES" ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Survives ({edges.filter((e) => e.relation === "SURVIVES").length})
          </button>
          <button
            onClick={() => setSelectedRelation("CONFLICTS_WITH")}
            className={`px-3 py-1 rounded-lg transition font-medium ${
              selectedRelation === "CONFLICTS_WITH" ? "bg-rose-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            ⚠️ Conflicts ({edges.filter((e) => e.relation === "CONFLICTS_WITH").length})
          </button>
          <button
            onClick={() => setSelectedRelation("REFERENCES")}
            className={`px-3 py-1 rounded-lg transition font-medium ${
              selectedRelation === "REFERENCES" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            References ({edges.filter((e) => e.relation === "REFERENCES").length})
          </button>
        </div>
      </div>

      {/* Cross-Clause Conflicts Callout (Feature 4) */}
      {conflicts.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-rose-300">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>⚠️ Potential Contract Conflicts Detected ({conflicts.length})</span>
          </div>

          {conflicts.map((conf) => (
            <div
              key={conf.id}
              className="bg-rose-950/20 border border-rose-500/40 rounded-2xl p-4 shadow-sm space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs text-rose-300">{conf.conflict_type}</span>
                  {conf.typed_category && (
                    <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-rose-900/70 border border-rose-500/50 text-rose-200 uppercase tracking-wider">
                      {conf.typed_category}
                    </span>
                  )}
                </div>
                <ConfidenceBadge level={conf.confidence} inline />
              </div>

              <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/70 p-3 rounded-xl border border-rose-900/40">
                {conf.explanation}
              </p>

              {/* Side-by-Side Conflicting Excerpts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div
                  onClick={() => onSelectClause(conf.clause_a_id)}
                  className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 hover:border-indigo-500 cursor-pointer transition group"
                >
                  <div className="flex items-center justify-between text-[11px] font-bold text-indigo-400 mb-1">
                    <span>{conf.clause_a_title} ({conf.clause_a_id})</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </div>
                  <p className="text-slate-300 italic text-[11px]">"{conf.clause_a_excerpt}"</p>
                </div>

                <div
                  onClick={() => onSelectClause(conf.clause_b_id)}
                  className="bg-slate-950/80 p-3 rounded-xl border border-slate-800 hover:border-rose-500 cursor-pointer transition group"
                >
                  <div className="flex items-center justify-between text-[11px] font-bold text-rose-400 mb-1">
                    <span>{conf.clause_b_title} ({conf.clause_b_id})</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </div>
                  <p className="text-slate-300 italic text-[11px]">"{conf.clause_b_excerpt}"</p>
                </div>
              </div>

              <div className="text-[11px] text-amber-300/90 font-medium">
                💡 Suggested Question for Counsel: {conf.suggested_question}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Graph Edges Directory */}
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
          Connected Cross-Clause Relationships
        </h3>

        {filteredEdges.length === 0 ? (
          <div className="text-center py-10 text-xs text-slate-500">
            No edges found for the selected relationship filter.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-2.5">
            {filteredEdges.map((edge, idx) => {
              const srcClause = clauses.find((c) => c.id === edge.source);
              const tgtClause = clauses.find((c) => c.id === edge.target);

              const isSurvival = edge.relation === "SURVIVES";
              const isConflict = edge.relation === "CONFLICTS_WITH";

              return (
                <div
                  key={idx}
                  className={`p-3.5 rounded-xl border transition-all duration-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 ${
                    isConflict
                      ? "bg-rose-950/20 border-rose-500/30"
                      : isSurvival
                      ? "bg-cyan-950/20 border-cyan-500/30"
                      : "bg-slate-900/60 border-slate-800"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    {/* Source Clause Pill */}
                    <button
                      onClick={() => onSelectClause(edge.source)}
                      className="text-left group"
                    >
                      <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-slate-950 text-indigo-300 border border-slate-800 group-hover:border-indigo-400 transition">
                        {edge.source}
                      </span>
                      <div className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 transition truncate max-w-[140px]">
                        {srcClause?.title || edge.source}
                      </div>
                    </button>

                    {/* Relation Badge */}
                    <div className="flex flex-col items-center px-2">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider border ${
                          isConflict
                            ? "bg-rose-950 text-rose-300 border-rose-500"
                            : isSurvival
                            ? "bg-cyan-950 text-cyan-300 border-cyan-500"
                            : "bg-indigo-950 text-indigo-300 border-indigo-500"
                        }`}
                      >
                        {edge.relation}
                      </span>
                      <ArrowRight className="w-4 h-4 text-slate-500 mt-1" />
                    </div>

                    {/* Target Clause Pill */}
                    <button
                      onClick={() => onSelectClause(edge.target)}
                      className="text-left group"
                    >
                      <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-slate-950 text-indigo-300 border border-slate-800 group-hover:border-indigo-400 transition">
                        {edge.target}
                      </span>
                      <div className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 transition truncate max-w-[140px]">
                        {tgtClause?.title || edge.target}
                      </div>
                    </button>
                  </div>

                  {/* Description */}
                  <div className="text-xs text-slate-300 flex-1 md:text-right">
                    <span className="leading-relaxed">{edge.description}</span>
                    <ConfidenceBadge level={edge.confidence} inline />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
