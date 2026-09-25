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

export default function App() {
  const [samples, setSamples] = useState([]);
  const [selectedSampleId, setSelectedSampleId] = useState("sample_employment");
  const [docData, setDocData] = useState(null);
  const [selectedClauseId, setSelectedClauseId] = useState("SEC-4");
  const [activeTab, setActiveTab] = useState("analysis");
  const [jurisdiction, setJurisdiction] = useState("General / Unspecified");
  const [healthData, setHealthData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize
  useEffect(() => {
    checkHealth().then(setHealthData).catch(console.error);

    fetchSamples()
      .then((data) => {
        setSamples(data);
        if (data.length > 0) {
          handleLoadSample(data[0].id);
        }
      })
      .catch(console.error);
  }, []);

  const handleLoadSample = async (sampleId) => {
    setIsLoading(true);
    setSelectedSampleId(sampleId);
    try {
      const data = await loadSample(sampleId);
      setDocData(data);
      if (data.clauses?.length > 0) {
        // Default select first high attention clause or first clause
        const highClause = data.clauses.find((c) => c.attention_level.includes("High"));
        setSelectedClauseId(highClause ? highClause.id : data.clauses[0].id);
      }
    } catch (err) {
      console.error("Failed to load sample contract:", err);
    } finally {
      setIsLoading(false);
    }
  };

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
      <div className="bg-slate-900/90 border-b border-slate-800/80 px-4 py-1.5 flex items-center justify-between text-xs shrink-0">
        <div className="flex items-center gap-2">
          <span className="font-bold text-indigo-400 text-[11px] uppercase tracking-wider flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Live Demo Flow:
          </span>
          <div className="flex items-center gap-1.5 overflow-x-auto">
            <button
              onClick={() => {
                handleLoadSample("sample_employment");
                setActiveTab("analysis");
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-[11px] transition font-medium"
            >
              1. Scanned Contract
            </button>
            <button
              onClick={() => {
                setSelectedClauseId("SEC-12");
                setActiveTab("analysis");
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-[11px] transition font-medium"
            >
              2. Attention & Deviation
            </button>
            <button
              onClick={() => setActiveTab("qa")}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-cyan-300 hover:text-white border border-slate-800 text-[11px] transition font-medium"
            >
              3. Multi-Hop Reasoning (2 Citations)
            </button>
            <button
              onClick={() => {
                handleLoadSample("sample_lease");
                setActiveTab("graph");
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-rose-300 hover:text-white border border-slate-800 text-[11px] transition font-medium"
            >
              4. Cross-Clause Conflict (Notice Clashes)
            </button>
            <button
              onClick={() => setActiveTab("timeline")}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-emerald-300 hover:text-white border border-slate-800 text-[11px] transition font-medium"
            >
              5. Obligation Timeline
            </button>
            <button
              onClick={() => setActiveTab("compare")}
              className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-indigo-300 hover:text-white border border-slate-800 text-[11px] transition font-medium"
            >
              6. Semantic Comparison
            </button>
          </div>
        </div>
        <span className="text-[11px] text-slate-500 font-mono hidden xl:inline">
          Evidence-Grounded Legal Pipeline
        </span>
      </div>

      {/* Main Split-Pane Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane: Source Document (50% Width on desktop) */}
        <div className="w-1/2 min-w-[380px] h-full flex flex-col border-r border-slate-800">
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
        </div>

        {/* Right Pane: AI Legal Reasoning & Feature Tabs (50% Width) */}
        <div className="w-1/2 flex flex-col h-full bg-slate-900/40 overflow-hidden">
          {/* Right Pane Navigation Tabs */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-900/90 shrink-0">
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <button
                onClick={() => setActiveTab("analysis")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "analysis"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Clause Intelligence</span>
              </button>

              <button
                onClick={() => setActiveTab("graph")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "graph"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Network className="w-3.5 h-3.5" />
                <span>Clause Graph & Conflicts</span>
                {docData?.conflicts?.length > 0 && (
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                )}
              </button>

              <button
                onClick={() => setActiveTab("timeline")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "timeline"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Clock className="w-3.5 h-3.5" />
                <span>Obligation Timeline</span>
              </button>

              <button
                onClick={() => setActiveTab("compare")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "compare"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <GitCompare className="w-3.5 h-3.5" />
                <span>Contract Comparison</span>
              </button>

              <button
                onClick={() => setActiveTab("qa")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "qa"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Verified Q&A</span>
              </button>

              <button
                onClick={() => setActiveTab("corpus")}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                  activeTab === "corpus"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <BookOpen className="w-3.5 h-3.5" />
                <span>CUAD Benchmarks</span>
              </button>
            </div>
          </div>

          {/* Right Pane Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === "analysis" && (
              <AnalysisPanel
                clause={selectedClause}
                onSelectClause={(cid) => setSelectedClauseId(cid)}
                allEdges={docData?.graph_edges || []}
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
        </div>
      </div>

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
