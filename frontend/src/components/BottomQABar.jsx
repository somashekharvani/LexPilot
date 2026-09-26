import React, { useState } from "react";
import { MessageSquare, Send, Sparkles, X, ArrowRight } from "lucide-react";
import ConfidenceBadge from "./ConfidenceBadge";
import { askQuestion } from "../services/api";

export default function BottomQABar({ docId, jurisdiction, onSelectClause, onOpenQATab }) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [quickResult, setQuickResult] = useState(null);

  const handleAsk = async (e) => {
    e?.preventDefault();
    if (!query.trim() || isLoading) return;

    setIsLoading(true);
    try {
      const resp = await askQuestion(query, docId, jurisdiction);
      setQuickResult(resp);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative border-t border-slate-800 bg-slate-900/95 backdrop-blur px-4 py-2.5 z-20 shadow-lg">
      {/* Pop-up result drawer if quickResult is present */}
      {quickResult && (
        <div
          role="region"
          aria-label="Quick Question Answer"
          aria-live="polite"
          className="absolute bottom-full left-4 right-4 mb-2 bg-slate-900 border border-slate-700/80 rounded-2xl p-4 shadow-2xl max-h-80 overflow-y-auto space-y-2.5 animate-in slide-in-from-bottom-2"
        >
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-100">{quickResult.question}</span>
              <ConfidenceBadge level={quickResult.confidence} inline />
            </div>
            <button
              onClick={() => setQuickResult(null)}
              aria-label="Close answer drawer"
              className="text-slate-400 hover:text-white p-1 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>

          <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800">
            {quickResult.answer}
          </p>

          {/* Citations */}
          {quickResult.citations?.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              {quickResult.citations.map((c, i) => (
                <button
                  key={i}
                  aria-label={`View cited clause ${c.title} (${c.clause_id})`}
                  onClick={() => {
                    onSelectClause(c.clause_id);
                    setQuickResult(null);
                  }}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-300 bg-indigo-950/60 hover:bg-indigo-900/60 px-2.5 py-1 rounded-lg border border-indigo-500/40 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
                >
                  <span>Cite: {c.title} ({c.clause_id})</span>
                  <ArrowRight className="w-3 h-3" aria-hidden="true" />
                </button>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
            <span>{quickResult.jurisdiction_note}</span>
            <button
              onClick={() => {
                onOpenQATab();
                setQuickResult(null);
              }}
              className="text-indigo-400 hover:underline font-medium"
            >
              Open in Full Q&A Panel →
            </button>
          </div>
        </div>
      )}

      {/* Main input form */}
      <form onSubmit={handleAsk} className="flex items-center gap-3 max-w-7xl mx-auto">
        <div className="flex items-center gap-2 text-indigo-400 shrink-0">
          <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
          <span className="text-xs font-bold tracking-wide hidden sm:inline text-slate-200">
            Ask LexPilot:
          </span>
        </div>

        <input
          id="lexpilot-qa-input"
          aria-label="Ask LexPilot a question grounded in contract clauses"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask any question grounded in source clauses (e.g. 'If I terminate under Section 4, does Section 12 still apply?')..."
          className="flex-1 bg-slate-950/70 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
        />

        <button
          type="submit"
          aria-label="Submit question for verification and answer"
          disabled={isLoading || !query.trim()}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50 shrink-0 shadow-sm"
        >
          {isLoading ? (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <>
              <span>Verify & Answer</span>
              <Send className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
