"use client";

import React, { useState } from "react";
import {
  Brain,
  Search,
  RefreshCw,
  FileText,
  Shield,
  FolderOpen,
  MapPin,
  Calendar,
  Layers,
  ChevronDown
} from "lucide-react";
import { useInvestigation } from "@/context/InvestigationContext";

const PRESET_CASES = [
  { id: "1042", label: "Case 1042", category: "Armed Robbery", location: "Noida Sector 18" },
  { id: "1088", label: "Case 1088", category: "Commercial Robbery", location: "Lajpat Nagar" },
  { id: "CR-2026-014", label: "CR-2026-014", category: "Burglary", location: "Indiranagar" },
];

export default function InvestigationHeader() {
  const {
    selectedCaseId,
    caseContext,
    loadingCase,
    loadCase,
    generateReport,
    generatingReport,
    openSearchModal,
    refreshWorkspace,
  } = useInvestigation();

  const [inputCaseId, setInputCaseId] = useState<string>("");
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);

  const handleCaseSelect = (caseId: string) => {
    setDropdownOpen(false);
    loadCase(caseId);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputCaseId.trim()) {
      handleCaseSelect(inputCaseId.trim());
      setInputCaseId("");
    }
  };

  return (
    <header className="flex flex-col gap-4 border-b border-white/10 bg-midnight/90 pb-4 pt-2">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand/30 bg-brand/10 text-brand shadow-inner">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold uppercase tracking-[0.2em] text-brand">
                ConnectDots
              </span>
              <span className="rounded bg-brand/20 px-1.5 py-0.5 text-[0.65rem] font-mono font-semibold text-brand-accent">
                COMMAND CENTER
              </span>
            </div>
            <h1 className="text-xl font-black uppercase tracking-tight text-white font-mono">
              Investigation Workspace
            </h1>
          </div>
        </div>

        {/* Global Controls & Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Global Search Trigger */}
          <button
            onClick={openSearchModal}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3.5 py-2 text-xs font-mono text-white/70 hover:bg-white/[0.08] hover:text-white transition"
          >
            <Search className="h-3.5 w-3.5 text-white/40" />
            <span>Search Workspace...</span>
            <kbd className="ml-1 rounded bg-black/40 px-1.5 py-0.5 text-[0.6rem] text-white/40">
              ⌘K
            </kbd>
          </button>

          {/* Refresh / Sync Button */}
          <button
            onClick={refreshWorkspace}
            disabled={loadingCase}
            title="Refresh active case workspace"
            className="rounded-xl border border-white/10 bg-white/[0.04] p-2 text-white/70 hover:bg-white/[0.08] hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${loadingCase ? "animate-spin text-brand" : ""}`} />
          </button>

          {/* Generate Investigation Report */}
          <button
            onClick={generateReport}
            disabled={generatingReport || loadingCase}
            className="btn-metallic inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold uppercase tracking-wider text-slate-900 shadow-lg shadow-brand/10 disabled:opacity-50 hover:brightness-105 transition"
          >
            <FileText className="h-3.5 w-3.5" />
            {generatingReport ? "Generating Report..." : "Investigation Report"}
          </button>
        </div>
      </div>

      {/* Case Selector & Active Scope Ribbon */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/40 px-4 py-2 text-xs font-mono">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-white/50">
            <FolderOpen className="h-3.5 w-3.5 text-brand" />
            <span>ACTIVE CASE:</span>
          </div>

          {/* Dropdown Presets */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 rounded-lg border border-brand/40 bg-brand/10 px-2.5 py-1 font-bold text-white hover:bg-brand/20 transition"
            >
              <span>{caseContext?.record_id || selectedCaseId}</span>
              <ChevronDown className="h-3 w-3 text-brand-accent" />
            </button>

            {dropdownOpen && (
              <div className="absolute left-0 top-full mt-1.5 z-50 w-64 rounded-xl border border-white/10 bg-midnight/95 p-1.5 shadow-2xl backdrop-blur-xl">
                <div className="px-2 py-1 text-[0.65rem] font-bold uppercase tracking-wider text-white/40">
                  Select Benchmark Case
                </div>
                {PRESET_CASES.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => handleCaseSelect(preset.id)}
                    className={`flex w-full flex-col rounded-lg px-2.5 py-1.5 text-left text-xs transition ${
                      selectedCaseId === preset.id
                        ? "bg-brand/20 text-white font-bold"
                        : "text-white/70 hover:bg-white/5 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span>{preset.label}</span>
                      <span className="text-[0.65rem] text-brand-accent">{preset.category}</span>
                    </div>
                    <span className="text-[0.65rem] text-white/40">{preset.location}</span>
                  </button>
                ))}

                {/* Custom Case Input */}
                <form onSubmit={handleCustomSubmit} className="mt-1.5 border-t border-white/10 pt-1.5">
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      placeholder="Custom Case ID..."
                      value={inputCaseId}
                      onChange={(e) => setInputCaseId(e.target.value)}
                      className="w-full rounded bg-white/5 px-2 py-1 text-xs text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-brand"
                    />
                    <button
                      type="submit"
                      className="rounded bg-brand px-2 py-1 text-[0.65rem] font-bold text-white"
                    >
                      GO
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>

          {/* Active Case Meta Badges */}
          {caseContext && (
            <>
              <div className="hidden sm:flex items-center gap-1.5 text-white/70">
                <span className="h-1.5 w-1.5 rounded-full bg-brand animate-pulse" />
                <span className="font-bold text-white">{caseContext.category}</span>
              </div>
              <div className="hidden md:flex items-center gap-1.5 text-white/50">
                <MapPin className="h-3 w-3 text-emerald-400" />
                <span>{caseContext.location_name}</span>
              </div>
              {caseContext.occurred_at && (
                <div className="hidden lg:flex items-center gap-1.5 text-white/50">
                  <Calendar className="h-3 w-3 text-amber-400" />
                  <span>{new Date(caseContext.occurred_at).toLocaleDateString()}</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Investigator Auth Badge */}
        <div className="flex items-center gap-2 text-[0.7rem] text-white/50">
          <Shield className="h-3 w-3 text-emerald-400" />
          <span>INVESTIGATOR: SPECIAL CRIMES UNIT</span>
        </div>
      </div>
    </header>
  );
}
