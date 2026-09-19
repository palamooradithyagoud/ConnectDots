"use client";

import React, { useState } from "react";
import {
  Brain,
  Clock,
  Compass,
  FileCheck,
  Users,
  ShieldCheck,
  Bot,
  Layers,
  Sparkles,
  Maximize2,
  ChevronRight,
  Info,
} from "lucide-react";
import {
  InvestigationProvider,
  useInvestigation,
} from "@/context/InvestigationContext";

import InvestigationHeader from "@/components/investigation/InvestigationHeader";
import CaseContextPanel from "@/components/investigation/CaseContextPanel";
import InteractiveGraph from "@/components/investigation/InteractiveGraph";
import { AgentConsole } from "@/components/investigation/AgentConsole";
import InvestigationTimeline from "@/components/investigation/InvestigationTimeline";
import EvidenceWorkspace from "@/components/investigation/EvidenceWorkspace";
import GeographicIntelligencePanel from "@/components/investigation/GeographicIntelligencePanel";
import InvestigationReportModal from "@/components/investigation/InvestigationReportModal";
import GlobalSearchModal from "@/components/investigation/GlobalSearchModal";
import NetworkIntelligence from "@/components/investigation/NetworkIntelligence";
import InvestigatorReviewQueue from "@/components/investigation/InvestigatorReviewQueue";

function CommandCenterWorkspace() {
  const {
    graphNodes,
    graphEdges,
    loadingGraph,
    selectedNodeId,
    selectedEdge,
    selectNode,
    selectEdge,
    highlightedNodeIds,
    highlightedEdgeIds,
    selectedCaseId,
    runAgentInvestigation,
  } = useInvestigation();

  const [lowerTab, setLowerTab] = useState<"timeline_map" | "evidence" | "reviews" | "network">("timeline_map");

  return (
    <div className="flex flex-col gap-5 pb-16 font-mono">
      {/* Top Persistent Operational Header */}
      <InvestigationHeader />

      {/* Main Upper Deck: Tri-Pane Operational Command Center */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (3 cols): Persistent Case Context Dossier */}
        <div className="lg:col-span-3 flex flex-col">
          <CaseContextPanel />
        </div>

        {/* Center Column (6 cols): Investigation Graph Canvas */}
        <div className="lg:col-span-6 flex flex-col">
          <div className="relative rounded-2xl border border-white/10 bg-midnight/80 p-2.5 backdrop-blur-xl shadow-2xl flex-1 min-h-[560px]">
            {loadingGraph ? (
              <div className="flex h-[540px] w-full flex-col items-center justify-center text-center text-white/50">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand border-t-transparent mb-2" />
                <p className="text-xs">Traversing Knowledge Graph Neighborhood...</p>
              </div>
            ) : (
              <InteractiveGraph
                nodes={graphNodes}
                edges={graphEdges}
                selectedNodeId={selectedNodeId}
                selectedEdge={selectedEdge}
                onSelectNode={selectNode}
                onSelectEdge={selectEdge}
                highlightedNodeIds={highlightedNodeIds}
                highlightedEdgeIds={highlightedEdgeIds}
                onLaunchInvestigation={(id, label) => {
                  runAgentInvestigation(`Investigate ${label} ${id} and retrieve connected criminal evidence.`);
                }}
              />
            )}
          </div>
        </div>

        {/* Right Column (3 cols): AI Investigation Agent Console */}
        <div className="lg:col-span-3 flex flex-col">
          <div className="rounded-2xl border border-white/10 bg-midnight/80 p-3.5 backdrop-blur-xl shadow-2xl flex-1 max-h-[580px] overflow-y-auto">
            <AgentConsole />
          </div>
        </div>
      </div>

      {/* Lower Deck View Switcher Ribbon */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3 pt-2">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <button
            onClick={() => setLowerTab("timeline_map")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold uppercase tracking-wider transition ${
              lowerTab === "timeline_map"
                ? "bg-brand text-white shadow-lg shadow-brand/20"
                : "bg-white/[0.04] text-white/60 hover:text-white hover:bg-white/[0.08]"
            }`}
          >
            <Clock className="h-3.5 w-3.5" />
            <span>Timeline & PostGIS Map</span>
          </button>

          <button
            onClick={() => setLowerTab("evidence")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold uppercase tracking-wider transition ${
              lowerTab === "evidence"
                ? "bg-brand text-white shadow-lg shadow-brand/20"
                : "bg-white/[0.04] text-white/60 hover:text-white hover:bg-white/[0.08]"
            }`}
          >
            <FileCheck className="h-3.5 w-3.5" />
            <span>Evidence Workspace</span>
          </button>

          <button
            onClick={() => setLowerTab("reviews")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold uppercase tracking-wider transition ${
              lowerTab === "reviews"
                ? "bg-brand text-white shadow-lg shadow-brand/20"
                : "bg-white/[0.04] text-white/60 hover:text-white hover:bg-white/[0.08]"
            }`}
          >
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span>Human Validation Queue</span>
          </button>

          <button
            onClick={() => setLowerTab("network")}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-xl font-bold uppercase tracking-wider transition ${
              lowerTab === "network"
                ? "bg-brand text-white shadow-lg shadow-brand/20"
                : "bg-white/[0.04] text-white/60 hover:text-white hover:bg-white/[0.08]"
            }`}
          >
            <Users className="h-3.5 w-3.5 text-purple-400" />
            <span>Network Centrality (Phase 5)</span>
          </button>
        </div>

        <div className="flex items-center gap-2 text-[0.7rem] text-white/40">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Workspace Synchronized (Case {selectedCaseId})</span>
        </div>
      </div>

      {/* Lower Deck Active View Panels */}
      {lowerTab === "timeline_map" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-6">
            <InvestigationTimeline />
          </div>
          <div className="lg:col-span-6">
            <GeographicIntelligencePanel />
          </div>
        </div>
      ) : lowerTab === "evidence" ? (
        <EvidenceWorkspace />
      ) : lowerTab === "reviews" ? (
        <InvestigatorReviewQueue />
      ) : (
        <NetworkIntelligence />
      )}

      {/* Modals */}
      <InvestigationReportModal />
      <GlobalSearchModal />
    </div>
  );
}

export default function InvestigationPage() {
  return (
    <InvestigationProvider>
      <CommandCenterWorkspace />
    </InvestigationProvider>
  );
}
