import React, { useEffect, useRef, useState } from "react";
import { FileText, Search, Upload, BookOpen, Layers, CheckCircle2 } from "lucide-react";
import AttentionBadge from "./AttentionBadge";
import ConfidenceBadge from "./ConfidenceBadge";

export default function DocumentViewer({
  docData,
  selectedClauseId,
  onSelectClause,
  onUploadFile,
  isLoading,
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const clauseRefs = useRef({});
  const containerRef = useRef(null);

  // Programmatically scroll to and highlight clause when selectedClauseId changes
  useEffect(() => {
    if (selectedClauseId && clauseRefs.current[selectedClauseId]) {
      const el = clauseRefs.current[selectedClauseId];
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [selectedClauseId]);

  const clauses = docData?.clauses || [];
  const filteredClauses = clauses.filter((c) => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      (c.title || "").toLowerCase().includes(q) ||
      (c.text || "").toLowerCase().includes(q) ||
      (c.category || "").toLowerCase().includes(q) ||
      (c.id || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex flex-col h-full bg-slate-900/60 border-r border-slate-800 text-slate-100 overflow-hidden">
      {/* Document Header & Search Toolbar */}
      <div className="p-3.5 border-b border-slate-800/80 bg-slate-900/90 flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 overflow-hidden">
            <FileText className="w-5 h-5 text-indigo-400 shrink-0" />
            <div className="truncate">
              <h2 className="text-sm font-semibold text-slate-100 truncate">
                {docData?.document_name || "Source Legal Document"}
              </h2>
              <span className="text-xs text-indigo-300/80 font-medium">
                {docData?.document_type || "Contract"} • {clauses.length} Clauses Extracted
              </span>
            </div>
          </div>

          <label className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-lg text-xs font-medium transition shadow-sm">
            <Upload className="w-3.5 h-3.5" />
            <span>Upload</span>
            <input
              type="file"
              accept=".pdf,.txt,.doc,.docx"
              className="hidden"
              onChange={(e) => {
                if (e.target.files?.[0]) onUploadFile(e.target.files[0]);
              }}
            />
          </label>
        </div>

        {/* Search within document */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search clauses, terms, or covenants in document..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950/70 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 transition"
          />
        </div>
      </div>

      {/* Clause Stream Viewer */}
      <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-4 doc-scroll-pane">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 space-y-3">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs tracking-wide">Executing Layout-Aware Parsing & Classification...</p>
          </div>
        ) : filteredClauses.length === 0 ? (
          <div className="text-center py-16 text-slate-400 text-xs">
            No clauses match your search query.
          </div>
        ) : (
          filteredClauses.map((clause, idx) => {
            const isSelected = selectedClauseId === clause.id;
            return (
              <div
                key={clause.id}
                ref={(el) => (clauseRefs.current[clause.id] = el)}
                onClick={() => onSelectClause(clause.id)}
                className={`group relative rounded-xl p-4 transition-all duration-300 cursor-pointer border ${
                  isSelected
                    ? "bg-slate-800/90 border-indigo-500 shadow-lg shadow-indigo-500/10 ring-2 ring-indigo-500/30"
                    : "bg-slate-950/40 hover:bg-slate-800/40 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                {/* Active marker pill & citation badge */}
                {isSelected && (
                  <div className="flex items-center gap-1.5 mb-2 px-2.5 py-1 rounded-md bg-indigo-500/20 border border-indigo-500/40 text-indigo-200 text-[11px] font-bold tracking-wide w-fit animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                    <span>ACTIVE EVIDENCE CITATION</span>
                  </div>
                )}

                {/* Clause Header Bar */}
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center gap-2">
                    <span className={`font-mono text-xs font-bold px-2 py-0.5 rounded border ${
                      isSelected
                        ? "bg-indigo-600 text-white border-indigo-400"
                        : "bg-slate-800 text-indigo-300 border-slate-700/80"
                    }`}>
                      {clause.id}
                    </span>
                    <span className="text-xs uppercase tracking-wider font-semibold text-slate-400 px-2 py-0.5 rounded bg-slate-900/80 border border-slate-800">
                      {clause.category.replace("_", " ")}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <AttentionBadge level={clause.attention_level} />
                  </div>
                </div>

                {/* Clause Title */}
                <h3 className={`text-sm font-semibold mb-2 transition ${
                  isSelected ? "text-indigo-200 font-bold" : "text-slate-100 group-hover:text-indigo-200"
                }`}>
                  {clause.title}
                </h3>

                {/* Clause Text with active citation highlight */}
                <p className={`text-xs font-mono leading-relaxed whitespace-pre-wrap p-3 rounded-lg border transition ${
                  isSelected
                    ? "bg-slate-900/90 text-slate-100 border-indigo-500/60 border-l-4 border-l-indigo-400 shadow-inner"
                    : "bg-slate-950/60 text-slate-300/90 border-slate-900"
                }`}>
                  {clause.text}
                </p>

                {/* Footer Entity Tags */}
                <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="text-slate-500">Page {clause.page_number}</span>
                  {clause.fields?.obligations?.length > 0 && (
                    <span className="text-slate-400 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
                      {clause.fields.obligations.length} Obligations Detected
                    </span>
                  )}
                  <ConfidenceBadge level={clause.confidence} inline />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
