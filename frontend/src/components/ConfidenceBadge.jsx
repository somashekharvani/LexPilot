import React from "react";
import { CheckCircle2, AlertCircle, AlertTriangle } from "lucide-react";

/**
 * Accessible ConfidenceBadge
 * Complies with accessibility guidelines: includes explicit readable text,
 * ARIA roles, accessible contrast, and avoids color-only indicators.
 */
export default function ConfidenceBadge({ level = "High", reasoning = "", inline = false }) {
  const normLevel = (level || "High").toLowerCase();

  if (normLevel === "high") {
    return (
      <span
        role="status"
        aria-label="Verification Confidence: High"
        title={reasoning || "Direct textual entailment verified against cited clause."}
        className={`inline-flex items-center gap-1.5 font-bold uppercase tracking-wide rounded-full px-2.5 py-0.5 text-[10px] bg-emerald-950/70 text-emerald-200 border border-emerald-500/50 shadow-sm ${
          inline ? "" : "ml-2"
        }`}
      >
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
        <span>HIGH CONFIDENCE</span>
      </span>
    );
  }

  if (normLevel === "medium") {
    return (
      <span
        role="status"
        aria-label="Verification Confidence: Medium"
        title={reasoning || "Contextual paraphrasing; verified with secondary legal inference."}
        className={`inline-flex items-center gap-1.5 font-bold uppercase tracking-wide rounded-full px-2.5 py-0.5 text-[10px] bg-amber-950/70 text-amber-200 border border-amber-500/50 shadow-sm ${
          inline ? "" : "ml-2"
        }`}
      >
        <AlertCircle className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
        <span>MEDIUM CONFIDENCE</span>
      </span>
    );
  }

  // Low Confidence - visually distinguished per prompt specification:
  // "Low-confidence claims must be visually distinguished in the UI (muted color, '⚠️ Lower confidence — review carefully' label) instead of a green checkmark"
  return (
    <span
      role="status"
      aria-label="Verification Confidence: Lower confidence — review carefully"
      title={reasoning || "Requires careful manual review; partial or indirect textual support."}
      className={`inline-flex items-center gap-1.5 font-bold uppercase tracking-wide rounded-full px-2.5 py-0.5 text-[10px] bg-amber-900/50 text-amber-100 border border-amber-600/60 shadow-sm ${
        inline ? "" : "ml-2"
      }`}
    >
      <AlertTriangle className="w-3.5 h-3.5 text-amber-300" aria-hidden="true" />
      <span>⚠️ LOWER CONFIDENCE — REVIEW CAREFULLY</span>
    </span>
  );
}
