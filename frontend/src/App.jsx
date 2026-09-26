import React, { useState, useEffect } from "react";
import {
  FileText,
  Network,
  Clock,
  GitCompare,
  BookOpen,
  MessageSquare,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import Header from "./components/Header";
import DocumentViewer from "./components/DocumentViewer";
import AnalysisPanel from "./components/AnalysisPanel";
import TimelineView from "./components/TimelineView";
import ComparisonView from "./components/ComparisonView";
import GraphVisualizer from "./components/GraphVisualizer";
import ReferenceCorpusView from "./components/ReferenceCorpusView";
import VerifiedQAView from "./components/VerifiedQAView";
import BottomQABar from "./components/BottomQABar";
import { fetchSamples, loadSample, uploadDocument, checkHealth } from "./services/api";
import { INITIAL_DOC_DATA, DEFAULT_SAMPLES } from "./services/defaultData";

export default function App() {
  const [samples, setSamples] = useState(DEFAULT_SAMPLES || []);
  const [selectedSampleId, setSelectedSampleId] = useState("sample_employment");
  const [docData, setDocData] = useState(INITIAL_DOC_DATA);
  const [selectedClauseId, setSelectedClauseId] = useState("SEC-12");
  const [activeTab, setActiveTab] = useState("analysis");
  const [jurisdiction, setJurisdiction] = useState("General / Unspecified");
  const [healthData, setHealthData] = useState({
    status: "healthy",
    gemini_connected: false,
    gemini_model: "Offline Verified Legal Engine",
    service: "LexPilot Evidence-Grounded Legal Reasoning Pipeline"
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleLoadSample = async (sampleId) => {
    setIsLoading(true);
    setSelectedSampleId(sampleId);
    try {
      const data = await loadSample(sampleId);
      setDocData(data);
      if (data?.clauses?.length > 0) {
        // Default select first high attention clause or first clause
        const highClause = data.clauses.find((c) => String(c.attention_level || "").toLowerCase().includes("high"));
        setSelectedClauseId(highClause ? highClause.id : data.clauses[0].id);
      }
    } catch (err) {
      console.error("Failed to load sample contract:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize and sync with live backend
  useEffect(() => {
    checkHealth().then(setHealthData).catch(console.error);

    fetchSamples()
      .then((data) => {
        if (data && data.length > 0) {
          setSamples(data);
          handleLoadSample(data[0].id);
        }
      })
      .catch((err) => {
        console.warn("Using offline bundled samples:", err);
      });
  }, []);

  const handleUploadFile = async (file) => {
    setIsLoading(true);
    try {
      const data = await uploadDocument(file);
      setDocData(data);
      if (data.clauses?.length > 0) {
        setSelectedClauseId(data.clauses[0].id);
      }
    } catch (err) {
      alert("Failed to upload document: " + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedClause = docData?.clauses?.find((c) => c.id === selectedClauseId) || docData?.clauses?.[0];

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Skip to Main Content Link for Keyboard and Screen Reader Users (WCAG 2.4.1) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-3.5 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-xl focus:text-xs focus:font-semibold focus:shadow-xl focus:ring-2 focus:ring-white"
      >
        Skip to main content
      </a>

      {/* Top Navigation & Controls */}
      <Header
        samples={samples}
        selectedSampleId={selectedSampleId}
        onSelectSample={handleLoadSample}
        jurisdiction={jurisdiction}
        onSelectJurisdiction={setJurisdiction}
        healthData={healthData}
        onRefreshHealth={() => checkHealth().then(setHealthData)}
      />

      {/* Guided Hackathon Demo Tour Bar */}
      <nav aria-label="Guided Demo Flow" className="bg-slate-900/90 border-b border-slate-800/80 px-4 py-1.5 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center gap-2">
          <span className="font-bold text-indigo-400 text-[11px] uppercase tracking-wider flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" aria-hidden="true" />
            Live Demo Flow:
          </span>
          <div className="flex items-center gap-1.5 overflow-x-auto" role="group" aria-label="Demo tour steps">
            <button
              onClick={() => {
                handleLoadSample("sample_employment");
                setActiveTab("analysis");
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-[11px] transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              1. Scanned Contract
            </button>
            <button
              onClick={() => {
                setSelectedClauseId("SEC-12");
                setActiveTab("analysis");
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-[11px] transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              2. Attention & Deviation
            </button>
            <button
              onClick={() => setActiveTab("qa")}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-cyan-300 hover:text-white border border-slate-800 text-[11px] transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              3. Multi-Hop Reasoning (2 Citations)
            </button>
            <button
              onClick={() => {
                handleLoadSample("sample_lease");
                setActiveTab("graph");
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-rose-300 hover:text-white border border-slate-800 text-[11px] transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              4. Cross-Clause Conflict (Notice Clashes)
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-emerald-300 hover:text-white border border-slate-800 text-[11px] transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              5. Obligation Timeline
            </button>
            <button
              onClick={() => setActiveTab("compare")}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-indigo-300 hover:text-white border border-slate-800 text-[11px] transition font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
            >
              6. Semantic Comparison
            </button>
          </div>
        </div>
        <span className="text-[11px] text-slate-500 font-mono hidden xl:inline">
          Evidence-Grounded Legal Pipeline
        </span>
      </nav>

      {/* Main Split-Pane Workspace Landmark */}
      <main id="main-content" className="flex-1 flex overflow-hidden">
        {/* Left Pane: Source Document (50% Width on desktop) */}
        <section aria-label="Source Document Pane" className="w-1/2 min-w-[380px] h-full flex flex-col border-r border-slate-800">
          <DocumentViewer
            docData={docData}
            selectedClauseId={selectedClauseId}
            onSelectClause={(cid) => {
              setSelectedClauseId(cid);
              setActiveTab("analysis");
            }}
            onUploadFile={handleUploadFile}
            isLoading={isLoading}
          />
        </section>

        {/* Right Pane: AI Legal Reasoning & Feature Tabs (50% Width) */}
        <section aria-label="Legal Reasoning and Verification Pane" className="w-1/2 flex flex-col h-full bg-slate-900/40 overflow-hidden">
          {/* Right Pane Navigation Tabs */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/90 shrink-0">
            <div
              role="tablist"
              aria-label="Legal Analysis Feature Views"
              className="flex items-center gap-1.5 overflow-x-auto"
            >
              <button
                role="tab"
                id="tab-analysis"
                aria-selected={activeTab === "analysis"}
                aria-controls="tabpanel-analysis"
                onClick={() => setActiveTab("analysis")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                  activeTab === "analysis"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <FileText className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Clause Intelligence</span>
              </button>

              <button
                role="tab"
                id="tab-graph"
                aria-selected={activeTab === "graph"}
                aria-controls="tabpanel-graph"
                onClick={() => setActiveTab("graph")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                  activeTab === "graph"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Network className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Clause Graph & Conflicts</span>
                {docData?.conflicts?.length > 0 && (
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" aria-label="Conflicts detected"></span>
                )}
              </button>

              <button
                role="tab"
                id="tab-timeline"
                aria-selected={activeTab === "timeline"}
                aria-controls="tabpanel-timeline"
                onClick={() => setActiveTab("timeline")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                  activeTab === "timeline"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Clock className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Obligation Timeline</span>
              </button>

              <button
                role="tab"
                id="tab-compare"
                aria-selected={activeTab === "compare"}
                aria-controls="tabpanel-compare"
                onClick={() => setActiveTab("compare")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                  activeTab === "compare"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <GitCompare className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Contract Comparison</span>
              </button>

              <button
                role="tab"
                id="tab-qa"
                aria-selected={activeTab === "qa"}
                aria-controls="tabpanel-qa"
                onClick={() => setActiveTab("qa")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                  activeTab === "qa"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" aria-hidden="true" />
                <span>Verified Q&A</span>
              </button>

              <button
                role="tab"
                id="tab-corpus"
                aria-selected={activeTab === "corpus"}
                aria-controls="tabpanel-corpus"
                onClick={() => setActiveTab("corpus")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 ${
                  activeTab === "corpus"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
                <span>CUAD Benchmarks</span>
              </button>
            </div>
          </div>

          {/* Right Pane Tab Content Panel */}
          <div
            role="tabpanel"
            id={`tabpanel-${activeTab}`}
            aria-labelledby={`tab-${activeTab}`}
            className="flex-1 overflow-hidden"
          >
            {activeTab === "analysis" && (
              <AnalysisPanel
                clause={selectedClause}
                onSelectClause={(cid) => setSelectedClauseId(cid)}
                allEdges={docData?.graph_edges || []}
                conflicts={docData?.conflicts || []}
              />
            )}

            {activeTab === "graph" && (
              <GraphVisualizer
                clauses={docData?.clauses || []}
                edges={docData?.graph_edges || []}
                conflicts={docData?.conflicts || []}
                onSelectClause={(cid) => {
                  setSelectedClauseId(cid);
                  setActiveTab("analysis");
                }}
              />
            )}

            {activeTab === "timeline" && (
              <TimelineView
                timeline={docData?.timeline || []}
                onSelectClause={(cid) => {
                  setSelectedClauseId(cid);
                  setActiveTab("analysis");
                }}
              />
            )}

            {activeTab === "compare" && (
              <ComparisonView
                onSelectClause={(cid) => {
                  if (cid) {
                    setSelectedClauseId(cid);
                    setActiveTab("analysis");
                  }
                }}
              />
            )}

            {activeTab === "qa" && (
              <VerifiedQAView
                docId={docData?.document_id}
                jurisdiction={jurisdiction}
                onSelectClause={(cid) => {
                  setSelectedClauseId(cid);
                  setActiveTab("analysis");
                }}
              />
            )}

            {activeTab === "corpus" && <ReferenceCorpusView />}
          </div>
        </section>
      </main>

      {/* Always Visible Bottom Bar */}
      <BottomQABar
        docId={docData?.document_id}
        jurisdiction={jurisdiction}
        onSelectClause={(cid) => {
          setSelectedClauseId(cid);
          setActiveTab("analysis");
        }}
        onOpenQATab={() => setActiveTab("qa")}
      />
    </div>
  );
}
