import React from "react";
import { Clock, Calendar, AlertTriangle, ArrowRight, Shield } from "lucide-react";
import AttentionBadge from "./AttentionBadge";
import ConfidenceBadge from "./ConfidenceBadge";

export default function TimelineView({ timeline = [], onSelectClause }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center text-slate-400">
        <Clock className="w-12 h-12 text-slate-600 mb-3" />
        <h3 className="text-base font-medium text-slate-200">No Timeline Milestones Extracted</h3>
        <p className="text-xs text-slate-400 mt-1">Upload a document with operational deadlines and payment cycles.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-5 text-slate-100 space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-emerald-400" />
            Structured Obligation Timeline ({timeline.length} Milestones)
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological sequence of extracted deadlines, cure periods, and operational covenants.
          </p>
        </div>
      </div>

      {/* Visual Timeline Track */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-gradient-to-b before:from-indigo-500 before:via-emerald-500 before:to-slate-700">
        {timeline.map((event, idx) => {
          return (
            <div key={event.id || idx} className="relative group">
              {/* Timeline Node Dot */}
              <div className="absolute -left-6 top-1.5 w-4 h-4 rounded-full border-2 border-slate-900 bg-emerald-400 shadow-md shadow-emerald-500/20 group-hover:scale-125 transition-transform duration-200"></div>

              {/* Event Card */}
              <div className="bg-slate-900/80 hover:bg-slate-800/80 border border-slate-800 rounded-2xl p-4 transition-all duration-200 shadow-sm">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/40">
                      {event.timeframe_or_date}
                    </span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-950 text-slate-300 border border-slate-800">
                      Party: {event.party}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <AttentionBadge level={event.attention_level} />
                    <ConfidenceBadge level={event.confidence} inline />
                  </div>
                </div>

                {/* Obligation Content */}
                <p className="text-xs text-slate-200 font-medium leading-relaxed bg-slate-950/50 p-3 rounded-xl border border-slate-900 mb-3">
                  {event.obligation}
                </p>

                {/* Source Citation & Jump Button */}
                <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/60">
                  <span className="text-slate-400 text-[11px]">
                    Category: <strong className="text-slate-300 uppercase">{event.category}</strong>
                  </span>

                  <button
                    onClick={() => onSelectClause(event.clause_id)}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-950/40 hover:bg-indigo-900/40 px-2.5 py-1 rounded-lg border border-indigo-500/30 transition"
                  >
                    <span>Cite: {event.citation}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
