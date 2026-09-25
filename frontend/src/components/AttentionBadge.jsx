import React from "react";
import { AlertOctagon, AlertTriangle, ShieldCheck } from "lucide-react";

/**
 * Accessible AttentionBadge
 * Follows accessibility guidelines: uses explicit textual labels,
 * ARIA roles, strong contrast, and avoids relying on colors/emoji alone.
 */
export default function AttentionBadge({ level = "🟢 Normal", size = "normal" }) {
  const isHigh = level.includes("High") || level.includes("🔴");
  const isReview = level.includes("Review") || level.includes("🟠");

  if (isHigh) {
    return (
      <span
        role="status"
        aria-label="Attention Level: High Attention"
        title="Informational Attention Flag — Not a legal determination or risk score."
        className="inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-md px-2.5 py-1 text-[11px] bg-rose-950/80 text-rose-200 border border-rose-500/60 shadow-sm"
      >
        <AlertOctagon className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" />
        <span>HIGH ATTENTION</span>
      </span>
    );
  }

  if (isReview) {
    return (
      <span
        role="status"
        aria-label="Attention Level: Review Recommended"
        title="Informational Attention Flag — Not a legal determination or risk score."
        className="inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-md px-2.5 py-1 text-[11px] bg-amber-950/80 text-amber-200 border border-amber-500/60 shadow-sm"
      >
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
        <span>REVIEW RECOMMENDED</span>
      </span>
    );
  }

  return (
    <span
      role="status"
      aria-label="Attention Level: Normal Baseline"
      title="Informational Attention Flag — Standard commercial terms."
      className="inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider rounded-md px-2 py-0.5 text-[10px] bg-emerald-950/60 text-emerald-200 border border-emerald-500/40"
    >
      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
      <span>NORMAL</span>
    </span>
  );
}
