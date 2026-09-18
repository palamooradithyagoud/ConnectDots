"use client";

import React from "react";
import { GraphNode, GraphEdge } from "@/types/investigation";
import {
  ShieldAlert,
  Info,
  ExternalLink,
  Zap,
  CheckCircle2,
  Sparkles,
  Layers,
  ArrowRight
} from "lucide-react";

interface EvidencePanelProps {
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  onDrillDownCrime?: (crimeId: string) => void;
  onClose?: () => void;
}

export default function EvidencePanel({
  selectedNode,
  selectedEdge,
  onDrillDownCrime,
  onClose,
}: EvidencePanelProps) {
  if (!selectedNode && !selectedEdge) {
    return (
      <div className="flex h-full flex-col justify-center items-center rounded-xl border border-white/10 bg-midnight/60 p-6 text-center text-white/50 backdrop-blur-md">
        <Info className="h-6 w-6 text-white/30 mb-2" />
        <h4 className="text-sm font-semibold text-white/80">Evidence Inspector</h4>
        <p className="mt-1 text-xs text-white/40 max-w-xs">
          Select any node or relationship on the graph to inspect provenance, analytical confidence, and underlying crime records.
        </p>
      </div>
    );
  }

  // Edge Inspection View
  if (selectedEdge) {
    const isExplicit = selectedEdge.properties?.confidence_type === "explicit";
    const confidence = selectedEdge.properties?.confidence ?? (isExplicit ? 1.0 : 0.85);
    const source = selectedEdge.properties?.source || "knowledge_graph";
    const entityName = selectedEdge.properties?.entity_name || selectedEdge.properties?.intermediate_entity;

    return (
      <div className="flex flex-col gap-4 rounded-xl border border-white/10 bg-midnight/90 p-5 backdrop-blur-xl shadow-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-white/10 p-1.5 text-white/80">
              <Zap className="h-4 w-4 text-cyan-400" />
            </span>
            <div>
              <span className="text-[0.65rem] font-mono uppercase tracking-wider text-white/40">Relationship</span>
              <h4 className="text-sm font-bold font-mono text-white tracking-wide">
                {selectedEdge.relation}
              </h4>
            </div>
          </div>

          <span
            className={`rounded-full px-2.5 py-0.5 text-[0.65rem] font-bold font-mono uppercase tracking-wider ${
              isExplicit
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                : "bg-cyan-500/20 text-cyan-400 border border-cyan-500/40"
            }`}
          >
            {isExplicit ? "Explicit Fact" : "Derived Connection"}
          </span>
        </div>

        {/* Confidence Meter */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-mono">
            <span className="text-white/50">Confidence Score</span>
            <span className="font-bold text-white">{(confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
            <div
              className={`h-full transition-all duration-500 ${
                isExplicit ? "bg-emerald-400" : "bg-cyan-400"
              }`}
              style={{ width: `${Math.min(confidence * 100, 100)}%` }}
            />
          </div>
        </div>

        {/* Provenance Details */}
        <div className="space-y-2 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-xs">
          <div className="flex justify-between border-b border-white/5 pb-1.5">
            <span className="text-white/40">Source Attribution</span>
            <span className="font-mono text-white/80">{source}</span>
          </div>

          {entityName && (
            <div className="flex justify-between border-b border-white/5 pb-1.5">
              <span className="text-white/40">Shared Entity</span>
              <span className="font-mono font-bold text-amber-300">{entityName}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-1.5 text-white/70 font-mono text-[0.7rem]">
              <span>{selectedEdge.source.replace("crime:", "")}</span>
              <ArrowRight className="h-3 w-3 text-white/40" />
              <span>{selectedEdge.target.replace("crime:", "")}</span>
            </div>
          </div>
        </div>

        {/* Explanatory Note */}
        <div className="text-[0.7rem] text-white/50 italic leading-relaxed">
          {isExplicit
            ? "This connection was directly documented in the primary incident report narrative."
            : "This analytical relationship was discovered through cross-incident entity overlap and Phase 3 clustering models."}
        </div>
      </div>
    );
  }

  // Node Inspection View
  if (selectedNode) {
    const p = selectedNode.properties || {};
    const isCrime = selectedNode.label === "Crime";
    const title = p.record_id || p.name || p.pattern || p.description || selectedNode.id;

    return (
      <div className="flex flex-col gap-4 rounded-xl border border-white/10 bg-midnight/90 p-5 backdrop-blur-xl shadow-xl">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <span className="rounded-md bg-white/10 p-1.5 text-white/80">
              <ShieldAlert className="h-4 w-4 text-brand" />
            </span>
            <div>
              <span className="text-[0.65rem] font-mono uppercase tracking-wider text-white/40">Entity Node</span>
              <h4 className="text-sm font-bold text-white tracking-wide">{title}</h4>
            </div>
          </div>

          <span className="rounded-full bg-brand/20 border border-brand/40 px-2.5 py-0.5 text-[0.65rem] font-bold font-mono text-brand-glow uppercase">
            {selectedNode.label}
          </span>
        </div>

        {/* Properties Table */}
        <div className="space-y-2 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-xs max-h-44 overflow-y-auto">
          {Object.entries(p).map(([k, val]) => {
            if (["x", "y", "vx", "vy"].includes(k) || val === null || val === undefined) return null;
            return (
              <div key={k} className="flex justify-between border-b border-white/5 pb-1 last:border-0 last:pb-0">
                <span className="text-white/40 font-mono text-[0.7rem]">{k}</span>
                <span className="font-mono text-[0.7rem] text-white/80 max-w-[180px] truncate text-right">
                  {typeof val === "object" ? JSON.stringify(val) : String(val)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Drill-down Button if Crime */}
        {isCrime && onDrillDownCrime && (
          <button
            onClick={() => onDrillDownCrime(p.record_id || selectedNode.id.replace("crime:", ""))}
            className="btn-metallic flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-bold uppercase tracking-wider text-white shadow-md hover:scale-[1.02] transition-transform"
          >
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            Investigate Incident Connections
          </button>
        )}
      </div>
    );
  }

  return null;
}
