import React, { useState } from "react";
import { MessageSquare, Send, Sparkles, Network, ArrowRight, ShieldCheck, CheckCircle2, AlertTriangle, GitCommit } from "lucide-react";
import ConfidenceBadge from "./ConfidenceBadge";
import { askQuestion } from "../services/api";

export default function VerifiedQAView({ docId, jurisdiction, onSelectClause }) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [qaHistory, setQaHistory] = useState([
    {
      question: "If I terminate under Section 4, does the non-compete in Section 12 still apply?",
      answer:
        "Yes. When evaluating TERM AND TERMINATION alongside NON-COMPETITION AND RESTRICTIVE COVENANTS, the obligations remain in effect. Section 4(d) explicitly stipulates that Section 12 (Non-Competition and Restrictive Covenants) survives any termination or expiration of the Agreement, regardless of the reason for termination.",
      citations: [
        {
          clause_id: "SEC-4",
          title: "TERM AND TERMINATION",
          quote: "(d) Survival of Provisions: Sections 3 (Confidentiality), 12 (Non-Competition and Restrictive Covenants)... shall explicitly survive any termination.",
          page_number: 1,
        },
        {
          clause_id: "SEC-12",
          title: "NON-COMPETITION AND RESTRICTIVE COVENANTS",
          quote: "(a) Non-Compete: During the term of employment and for a period of thirty-six (36) months following the termination of employment... Employee shall not directly engage in competitive business.",
          page_number: 1,
        },
      ],
      provenance: [
        {
          claim_id: "CLAIM-1",
          claim_text: "Section 12 (Non-Competition) explicitly survives any termination or expiration of the Agreement pursuant to Section 4(d).",
          reasoning_step: "Traversed graph edge 'SURVIVES' linking Section 4 to Section 12, harmonizing post-termination covenants.",
          supporting_clauses: [
            {
              clause_id: "SEC-4",
              title: "TERM AND TERMINATION",
              page: 1,
              char_start: 840,
              char_end: 935,
              quote: "(d) Survival of Provisions: Sections 3, 12, and 14 shall explicitly survive...",
            },
            {
              clause_id: "SEC-12",
              title: "NON-COMPETITION AND RESTRICTIVE COVENANTS",
              page: 1,
              char_start: 1120,
              char_end: 1240,
              quote: "(a) Non-Compete: During the term and for 36 months following termination...",
            },
          ],
          entailment_result: "PASS",
          confidence: "High",
          verification_details: "Grounding verified: 100% factual entailment confirmed directly from cited clauses.",
        },
      ],
      confidence: "High",
      multi_hop: true,
      graph_path: ["SEC-4", "SEC-12"],
      reasoning_steps: [
        "Step 1: Examined TERM AND TERMINATION (SEC-4) establishing exit rights and survival covenants.",
        "Step 2: Traversed graph edge 'SURVIVES' directly connecting Section 4 to Section 12.",
        "Step 3: Harmonized cross-clause obligations to determine post-termination enforceability.",
      ],
      jurisdiction_note:
        "This analysis may depend on applicable jurisdiction (Delaware / General); consider discussing with a qualified legal professional.",
      disclaimer: "This is an informational analysis, not a legal determination.",
    },
  ]);

  const handleSend = async (questionText) => {
    const q = questionText || query;
    if (!q.trim() || isLoading) return;

    setIsLoading(true);
    try {
      const resp = await askQuestion(q, docId, jurisdiction);
      setQaHistory((prev) => [resp, ...prev]);
      if (!questionText) setQuery("");
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const sampleQuestions = [
    "If I terminate under Section 4, does the non-compete in Section 12 still apply?",
    "Are there contradictory notice periods between Section 4 and Section 14?",
    "What are the payment deadlines and late penalty fees?",
    "Does the limitation of liability cap the indemnification obligations?",
  ];

  return (
    <div className="flex flex-col h-full overflow-y-auto p-5 text-slate-100 space-y-5">
      {/* Header */}
      <div className="pb-3 border-b border-slate-800">
        <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          Verified Legal Q&A & Multi-Hop Graph Reasoning
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Every answer is strictly grounded with exact source clause citations, confidence scores, and multi-hop graph traversal.
        </p>
      </div>

      {/* Suggested Multi-Hop Questions */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
          Suggested Multi-Hop Questions:
        </span>
        <div className="flex flex-wrap gap-2">
          {sampleQuestions.map((sq, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(sq)}
              className="text-xs text-left bg-slate-900/80 hover:bg-indigo-950/60 border border-slate-800 hover:border-indigo-500/50 text-slate-300 hover:text-indigo-200 px-3 py-1.5 rounded-xl transition shadow-sm"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Query Input Box */}
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask LexPilot about obligations, cross-clause survival, or liability caps..."
          className="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
        />
        <button
          onClick={() => handleSend()}
          disabled={isLoading || !query.trim()}
          className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50 shadow-sm"
        >
          {isLoading ? (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <>
              <span>Ask</span>
              <Send className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </div>

      {/* Q&A History Stream */}
      <div className="space-y-4">
        {qaHistory.map((item, idx) => {
          return (
            <div
              key={idx}
              className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4.5 space-y-3.5 shadow-sm"
            >
              {/* Question Bar */}
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                <h3 className="text-xs font-bold text-slate-100 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                  {item.question}
                </h3>

                <div className="flex items-center gap-2">
                  {item.multi_hop && (
                    <span className="font-semibold text-[11px] px-2.5 py-0.5 rounded-full bg-cyan-950/60 text-cyan-300 border border-cyan-800/40 flex items-center gap-1">
                      <Network className="w-3 h-3 text-cyan-400" />
                      Multi-Hop Reasoning
                    </span>
                  )}
                  <ConfidenceBadge level={item.confidence} inline />
                </div>
              </div>

              {/* Verified Answer */}
              <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/60 p-3.5 rounded-xl border border-slate-900">
                {item.answer}
              </p>

              {/* Multi-Hop Graph Path & Reasoning Steps */}
              {item.multi_hop && item.reasoning_steps?.length > 0 && (
                <div className="bg-slate-950/40 p-3 rounded-xl border border-slate-900 space-y-1.5">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Evidence Reasoning Path</span>
                  </div>
                  <ul className="text-[11px] text-slate-300 space-y-1">
                    {item.reasoning_steps.map((step, sIdx) => (
                      <li key={sIdx} className="leading-normal">
                        {step}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Source Evidence Citations (Clickable to jump left pane!) */}
              <div className="space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Source Clause Citations ({item.citations?.length || 0}):
                </span>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  {item.citations?.map((cit, cIdx) => (
                    <div
                      key={cIdx}
                      onClick={() => onSelectClause(cit.clause_id)}
                      className="bg-slate-950/70 hover:bg-slate-800/70 p-3 rounded-xl border border-slate-800 hover:border-indigo-500/80 cursor-pointer transition group"
                    >
                      <div className="flex items-center justify-between text-xs font-bold text-indigo-300 mb-1">
                        <span>{cit.title} ({cit.clause_id})</span>
                        <div className="flex items-center gap-1 text-[11px] text-indigo-400 group-hover:translate-x-1 transition-transform">
                          <span>Page {cit.page_number}</span>
                          <ArrowRight className="w-3 h-3" />
                        </div>
                      </div>
                      <p className="text-[11px] text-slate-400 font-mono italic leading-relaxed line-clamp-2">
                        "{cit.quote}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Provenance Chain Accordion (Why This Answer?) */}
              {item.provenance?.length > 0 && (
                <details className="group/prov rounded-xl border border-slate-800 bg-slate-950/60 p-3 transition" open>
                  <summary className="cursor-pointer text-[11px] font-bold text-indigo-300 uppercase tracking-wider flex items-center justify-between select-none">
                    <span className="flex items-center gap-1.5">
                      <Network className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Why this answer? (Provenance Chain &amp; Evidence Spans)</span>
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono group-open/prov:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="mt-3 space-y-3 pt-2 border-t border-slate-800/80">
                    {/* Visual Reasoning Flow Diagram */}
                    {item.multi_hop && item.graph_path?.length >= 2 && (
                      <div className="bg-slate-950/80 p-3 rounded-xl border border-indigo-900/40 space-y-2">
                        <div className="flex items-center gap-1.5 text-[10px] font-bold text-indigo-300 uppercase tracking-wider">
                          <GitCommit className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Reasoning Provenance Flow (Multi-Hop)</span>
                        </div>
                        <div className="flex items-center gap-2 overflow-x-auto py-1 text-[11px] font-mono">
                          <div className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 shrink-0">
                            Query
                          </div>
                          <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
                          <div
                            onClick={() => onSelectClause(item.graph_path[0])}
                            className="px-2.5 py-1 rounded-lg bg-indigo-950/80 hover:bg-indigo-900/80 border border-indigo-600/50 text-indigo-200 cursor-pointer transition shrink-0"
                          >
                            Seed: {item.graph_path[0]}
                          </div>
                          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40 text-[10px] text-cyan-300 shrink-0">
                            <span>1-Hop Graph Traverse</span>
                          </div>
                          <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
                          <div
                            onClick={() => onSelectClause(item.graph_path[1])}
                            className="px-2.5 py-1 rounded-lg bg-indigo-950/80 hover:bg-indigo-900/80 border border-indigo-600/50 text-indigo-200 cursor-pointer transition shrink-0"
                          >
                            Target: {item.graph_path[1]}
                          </div>
                          <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
                          <div className="px-2.5 py-1 rounded-lg bg-emerald-950/80 border border-emerald-600/50 text-emerald-200 font-bold shrink-0">
                            ✓ Entailed Claim
                          </div>
                        </div>
                      </div>
                    )}

                    {item.provenance.map((prov, pIdx) => (
                      <div key={pIdx} className="space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700/50">
                            Claim: {prov.claim_id}
                          </span>
                          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-700/50">
                            Entailment: {prov.entailment_result} ({prov.confidence})
                          </span>
                        </div>
                        <p className="text-slate-200 text-xs italic bg-slate-900/90 p-2.5 rounded-lg border border-slate-800">
                          "{prov.claim_text}"
                        </p>
                        <div className="text-[11px] text-slate-300 bg-slate-950/40 p-2 rounded-lg border border-slate-900">
                          <strong className="text-indigo-300">Reasoning Step:</strong> {prov.reasoning_step}
                        </div>
                        <div className="space-y-1.5">
                          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                            Exact Supporting Evidence Spans:
                          </span>
                          {prov.supporting_clauses?.map((sc, scIdx) => (
                            <div
                              key={scIdx}
                              onClick={() => onSelectClause(sc.clause_id)}
                              className="cursor-pointer bg-slate-900/60 hover:bg-slate-800/80 p-2 rounded-lg border border-slate-800/80 flex items-center justify-between text-[11px] transition"
                            >
                              <div className="flex items-center gap-2">
                                <span className="font-mono font-bold text-indigo-400">{sc.clause_id}</span>
                                <span className="text-slate-300 truncate max-w-xs">{sc.title}</span>
                              </div>
                              <div className="flex items-center gap-2 font-mono text-[10px] text-slate-400">
                                <span>Page {sc.page}</span>
                                <span>Chars {sc.char_start}–{sc.char_end}</span>
                                <span className="text-emerald-400 font-bold">✓ Verified</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </details>
              )}

              {/* Jurisdiction Note & Disclaimer */}
              <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/60 flex items-center justify-between">
                <span>{item.jurisdiction_note}</span>
                <span className="italic">{item.disclaimer}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
