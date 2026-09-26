import React, { useState } from "react";
import { Scale, ShieldCheck, Key, Globe, FileText, Check, AlertCircle, Info } from "lucide-react";
import { updateApiKey } from "../services/api";

export default function Header({
  samples = [],
  selectedSampleId,
  onSelectSample,
  jurisdiction,
  onSelectJurisdiction,
  healthData,
  onRefreshHealth,
}) {
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [keyInput, setKeyInput] = useState("");
  const [keyStatus, setKeyStatus] = useState(null);

  const handleSaveKey = async () => {
    if (!keyInput.trim()) return;
    try {
      const res = await updateApiKey(keyInput.trim());
      setKeyStatus("API Key configured successfully!");
      if (onRefreshHealth) onRefreshHealth();
      setTimeout(() => setShowKeyModal(false), 1200);
    } catch (e) {
      setKeyStatus("Failed to update API Key");
    }
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-slate-100 px-4 py-2.5 flex flex-col gap-2 shrink-0">
      {/* Top row */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center shadow-md shadow-indigo-600/30">
            <Scale className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-white">LexPilot</h1>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-700/50">
                AI for Legal Assistance & Access
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Evidence-Grounded Legal Reasoning & Connected Clause Intelligence
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Sample Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1.5 rounded-xl border border-slate-800 text-xs">
            <FileText className="w-3.5 h-3.5 text-indigo-400" aria-hidden="true" />
            <label htmlFor="sample-contract-select" className="text-slate-400 font-medium cursor-pointer">
              Sample Contract:
            </label>
            <select
              id="sample-contract-select"
              aria-label="Select sample contract"
              value={selectedSampleId}
              onChange={(e) => onSelectSample(e.target.value)}
              className="bg-transparent text-slate-200 font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 rounded cursor-pointer"
            >
              {samples.map((s) => (
                <option key={s.id} value={s.id} className="bg-slate-900 text-slate-100">
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Jurisdiction Selector */}
          <div className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1.5 rounded-xl border border-slate-800 text-xs">
            <Globe className="w-3.5 h-3.5 text-cyan-400" aria-hidden="true" />
            <label htmlFor="jurisdiction-select" className="text-slate-400 font-medium cursor-pointer">
              Jurisdiction:
            </label>
            <select
              id="jurisdiction-select"
              aria-label="Select governing jurisdiction"
              value={jurisdiction}
              onChange={(e) => onSelectJurisdiction(e.target.value)}
              className="bg-transparent text-slate-200 font-semibold focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 rounded cursor-pointer"
            >
              <option value="General / Unspecified" className="bg-slate-900">General / Unspecified</option>
              <option value="Delaware" className="bg-slate-900">Delaware (DE)</option>
              <option value="California" className="bg-slate-900">California (CA)</option>
              <option value="New York" className="bg-slate-900">New York (NY)</option>
              <option value="Texas" className="bg-slate-900">Texas (TX)</option>
            </select>
          </div>

          {/* Engine Status / API Key Button */}
          <button
            onClick={() => setShowKeyModal(true)}
            aria-haspopup="dialog"
            aria-expanded={showKeyModal}
            aria-label={`Engine status: ${healthData?.gemini_connected ? "Gemini 2.5 Active" : "Offline Verified Engine"}. Configure API Key.`}
            className="flex items-center gap-1.5 bg-slate-950 hover:bg-slate-800/80 px-2.5 py-1.5 rounded-xl border border-slate-800 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
          >
            <Key className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" />
            <span className="text-slate-300">
              {healthData?.gemini_connected ? "Gemini 2.5 Active" : "Offline Verified Engine"}
            </span>
            <span
              className={`w-2 h-2 rounded-full ${
                healthData?.gemini_connected ? "bg-emerald-400" : "bg-cyan-400"
              }`}
              aria-hidden="true"
            ></span>
          </button>
        </div>
      </div>

      {/* Mandatory Regulatory / Hackathon Disclaimer Banner */}
      <div className="flex items-center justify-between text-[11px] bg-slate-950/70 border border-slate-800/80 rounded-lg px-3 py-1 text-slate-400">
        <div className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-indigo-400 shrink-0" aria-hidden="true" />
          <span>
            <strong>Informational Notice:</strong> LexPilot produces informational evidence flags and connected clause maps, not legal advice or determinations. Always consult an attorney.
          </span>
        </div>
        <span className="hidden md:inline font-mono text-slate-500">Constraint: Assistance, not replacement for professional advice</span>
      </div>

      {/* API Key Modal */}
      {showKeyModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="api-key-modal-title"
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 id="api-key-modal-title" className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Key className="w-4 h-4 text-indigo-400" aria-hidden="true" />
                Configure Gemini API Key
              </h3>
              <button
                onClick={() => setShowKeyModal(false)}
                aria-label="Close API Key dialog"
                className="text-slate-400 hover:text-white text-xs font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 rounded px-1"
              >
                Close
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              LexPilot operates in dual mode: with an official Google Gemini API key or with its offline legal NLP rule engine. Enter your Gemini API key below to enable live generative analysis.
            </p>

            <div>
              <label htmlFor="gemini-api-key-input" className="block text-[11px] font-semibold text-slate-300 mb-1">
                Gemini API Key:
              </label>
              <input
                id="gemini-api-key-input"
                aria-label="Google Gemini API Key"
                type="password"
                placeholder="AIzaSy..."
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500 focus-visible:ring-2 focus-visible:ring-indigo-400"
              />
            </div>

            {keyStatus && (
              <div role="status" aria-live="polite" className="text-xs text-emerald-400 font-semibold">{keyStatus}</div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-3.5 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-300 hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveKey}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
              >
                Save & Connect
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
