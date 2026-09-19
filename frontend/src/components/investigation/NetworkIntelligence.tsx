"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  Award,
  Share2,
  TrendingUp,
  Shield,
  PhoneCall,
  FileText,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  Filter,
  RefreshCw,
  Info,
  Clock,
  Sparkles,
  MapPin
} from "lucide-react";
import { KeyIndividual, ScopeOption, PersonProfile } from "@/types/investigation";

interface NetworkIntelligenceProps {
  onFocusPersonOnGraph?: (personId: string) => void;
}

export default function NetworkIntelligence({ onFocusPersonOnGraph }: NetworkIntelligenceProps) {
  const [scopes, setScopes] = useState<ScopeOption[]>([]);
  const [selectedScope, setSelectedScope] = useState<string>("all:all");
  const [sortBy, setSortBy] = useState<string>("degree_centrality");
  const [individuals, setIndividuals] = useState<KeyIndividual[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
  const [personProfile, setPersonProfile] = useState<PersonProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // 1. Fetch available investigation scopes
  useEffect(() => {
    async function loadScopes() {
      try {
        const res = await fetch(`${apiUrl}/network/scopes`);
        if (res.ok) {
          const data = await res.json();
          const scopeList = Array.isArray(data) ? data : (data.scope_options || data.items || []);
          setScopes(scopeList);
        }
      } catch (err) {
        console.warn("Could not load scopes:", err);
      }
    }
    loadScopes();
  }, [apiUrl]);

  // 2. Fetch key individuals based on selected scope and sorting
  useEffect(() => {
    async function loadIndividuals() {
      setLoading(true);
      setError(null);
      try {
        const [scopeType, scopeId] = selectedScope.split(":");
        let url = `${apiUrl}/network/key-individuals?scope_type=${scopeType}&sort_by=${sortBy}&limit=20`;
        if (scopeId && scopeId !== "all") {
          url += `&scope_id=${encodeURIComponent(scopeId)}`;
        }

        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`Failed to load key individuals (${res.status})`);
        }
        const data = await res.json();
        setIndividuals(data.items || []);
        if (data.items && data.items.length > 0 && !selectedPersonId) {
          setSelectedPersonId(data.items[0].person_id);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load network intelligence.");
      } finally {
        setLoading(false);
      }
    }
    loadIndividuals();
  }, [apiUrl, selectedScope, sortBy]);

  // 3. Fetch detailed profile when a person is selected
  useEffect(() => {
    if (!selectedPersonId) return;

    async function loadProfile() {
      setProfileLoading(true);
      try {
        const res = await fetch(`${apiUrl}/network/key-individuals/${encodeURIComponent(selectedPersonId!)}`);
        if (res.ok) {
          const data = await res.json();
          setPersonProfile(data);
        }
      } catch (err) {
        console.warn("Could not load person profile:", err);
      } finally {
        setProfileLoading(false);
      }
    }
    loadProfile();
  }, [apiUrl, selectedPersonId]);

  return (
    <div className="space-y-6">
      {/* Neutral Principle Notice */}
      <div className="p-4 rounded-xl border border-blue-500/20 bg-blue-950/20 flex items-start gap-3 text-sm text-blue-300">
        <Info className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-blue-200">Objective Structural Topology:</span>{" "}
          Degree, Betweenness, and PageRank scores quantify mathematical connectivity, shortest path bridge positions,
          and communication topology in the observed records. Metrics reflect network position and do not infer legal guilt
          or criminal responsibility.
        </div>
      </div>

      {/* Control Bar: Scope Selector & Metric Sorter */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div className="flex items-center gap-3">
          <Filter className="h-4 w-4 text-slate-400" />
          <label className="text-xs font-medium text-slate-300">Investigation Scope:</label>
          <select
            value={selectedScope}
            onChange={(e) => setSelectedScope(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            {scopes.map((s) => (
              <option key={`${s.scope_type}:${s.scope_id}`} value={`${s.scope_type}:${s.scope_id}`}>
                {s.display_label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3">
          <TrendingUp className="h-4 w-4 text-slate-400" />
          <label className="text-xs font-medium text-slate-300">Rank By:</label>
          <div className="flex bg-slate-950 border border-slate-800 rounded-lg p-0.5">
            <button
              onClick={() => setSortBy("degree_centrality")}
              className={`px-3 py-1 text-xs rounded-md font-medium transition ${
                sortBy === "degree_centrality" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Degree
            </button>
            <button
              onClick={() => setSortBy("betweenness_centrality")}
              className={`px-3 py-1 text-xs rounded-md font-medium transition ${
                sortBy === "betweenness_centrality" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Betweenness (Bridges)
            </button>
            <button
              onClick={() => setSortBy("pagerank")}
              className={`px-3 py-1 text-xs rounded-md font-medium transition ${
                sortBy === "pagerank" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              PageRank
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Individuals Table (Left) & Person Dossier (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Table View (7 cols) */}
        <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-indigo-400" />
              <h3 className="text-sm font-semibold text-slate-200">Ranked Key Individuals</h3>
              <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">
                {individuals.length} identified
              </span>
            </div>
          </div>

          <div className="overflow-x-auto flex-1">
            {loading ? (
              <div className="p-8 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
                <RefreshCw className="h-4 w-4 animate-spin" /> Calculating network topology...
              </div>
            ) : error ? (
              <div className="p-8 text-center text-red-400 text-sm">{error}</div>
            ) : individuals.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No individuals identified in the selected network scope.
              </div>
            ) : (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
                    <th className="p-3 font-medium">Individual</th>
                    <th className="p-3 font-medium text-center">Degree</th>
                    <th className="p-3 font-medium text-center">Betweenness</th>
                    <th className="p-3 font-medium text-center">PageRank</th>
                    <th className="p-3 font-medium text-center">Links</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {individuals.map((ind, idx) => {
                    const isSelected = selectedPersonId === ind.person_id;
                    return (
                      <tr
                        key={ind.person_id}
                        onClick={() => setSelectedPersonId(ind.person_id)}
                        className={`cursor-pointer transition hover:bg-slate-800/40 ${
                          isSelected ? "bg-indigo-950/30 border-l-2 border-indigo-500" : ""
                        }`}
                      >
                        <td className="p-3">
                          <div className="flex items-center gap-2.5">
                            <span className="text-[10px] text-slate-500 font-mono w-4">#{idx + 1}</span>
                            <div className="h-7 w-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400 font-bold text-xs">
                              {ind.canonical_name.charAt(0)}
                            </div>
                            <div>
                              <div className="font-semibold text-slate-200">{ind.canonical_name}</div>
                              {ind.aliases && ind.aliases.length > 0 && (
                                <div className="text-[10px] text-slate-400">
                                  alias: {ind.aliases.join(", ")}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="p-3 text-center font-mono text-indigo-300">
                          {ind.metrics.degree_centrality.toFixed(3)}
                        </td>
                        <td className="p-3 text-center font-mono text-emerald-300">
                          {ind.metrics.betweenness_centrality.toFixed(3)}
                        </td>
                        <td className="p-3 text-center font-mono text-amber-300">
                          {ind.metrics.pagerank.toFixed(3)}
                        </td>
                        <td className="p-3 text-center">
                          <div className="flex items-center justify-center gap-2 text-[10px] text-slate-400">
                            <span title="Crimes connected" className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                              {ind.network_breakdown.connected_crimes} FIRs
                            </span>
                            <span title="Phones connected" className="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400">
                              {ind.network_breakdown.connected_phones} Ph
                            </span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Selected Individual Dossier (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          {profileLoading ? (
            <div className="p-12 rounded-xl bg-slate-900/60 border border-slate-800 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" /> Loading intelligence dossier...
            </div>
          ) : personProfile ? (
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-5">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">{personProfile.canonical_name}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-400 border border-indigo-800/50">
                      {personProfile.source_provenance}
                    </span>
                  </div>
                  {personProfile.aliases && personProfile.aliases.length > 0 && (
                    <div className="text-xs text-slate-400 mt-0.5">
                      Aliases: {personProfile.aliases.join(", ")}
                    </div>
                  )}
                </div>

                {onFocusPersonOnGraph && (
                  <button
                    onClick={() => onFocusPersonOnGraph(personProfile.person_id)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium transition"
                  >
                    <Share2 className="h-3.5 w-3.5" /> Center Graph
                  </button>
                )}
              </div>

              {/* Centrality Metrics Gauges */}
              {personProfile.metrics && (
                <div className="grid grid-cols-3 gap-2.5 p-3 rounded-lg bg-slate-950/50 border border-slate-800">
                  <div className="text-center">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Degree</div>
                    <div className="text-base font-bold text-indigo-400 font-mono mt-0.5">
                      {personProfile.metrics.degree_centrality.toFixed(3)}
                    </div>
                    <div className="text-[9px] text-slate-500">conn: {personProfile.metrics.raw_degree}</div>
                  </div>
                  <div className="text-center border-x border-slate-800/80">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Betweenness</div>
                    <div className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                      {personProfile.metrics.betweenness_centrality.toFixed(3)}
                    </div>
                    <div className="text-[9px] text-slate-500">bridge factor</div>
                  </div>
                  <div className="text-center">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">PageRank</div>
                    <div className="text-base font-bold text-amber-400 font-mono mt-0.5">
                      {personProfile.metrics.pagerank.toFixed(3)}
                    </div>
                    <div className="text-[9px] text-slate-500">network prestige</div>
                  </div>
                </div>
              )}

              {/* Structural Explanation */}
              {personProfile.structural_explanation && (
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                  <div className="font-semibold text-slate-200 mb-1 flex items-center gap-1.5 text-xs">
                    <Sparkles className="h-3.5 w-3.5 text-amber-400" /> Structural Position Analysis
                  </div>
                  {personProfile.structural_explanation}
                </div>
              )}

              {/* Associated Crimes */}
              {(() => {
                const crimes = personProfile.crimes || (personProfile as any).associated_crimes || [];
                return (
                  <div>
                    <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5 text-red-400" /> Linked FIR Incidents ({crimes.length})
                    </div>
                    {crimes.length === 0 ? (
                      <div className="text-xs text-slate-500 italic">No direct FIR links recorded.</div>
                    ) : (
                      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                        {crimes.map((c: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 text-xs space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-slate-200">{c.record_id || c.crime_id}</span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-950/40 text-red-400 border border-red-800/40">
                                {c.role}
                              </span>
                            </div>
                            {c.evidence_excerpt && (
                              <div className="text-[11px] text-slate-400 italic">"{c.evidence_excerpt}"</div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })()}

              {/* Associated Phones & CDR summary */}
              {(() => {
                const phones = personProfile.phones || (personProfile as any).associated_phones || [];
                return (
                  <div>
                    <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                      <PhoneCall className="h-3.5 w-3.5 text-emerald-400" /> Telecom & CDR Profiles ({phones.length})
                    </div>
                    {phones.length === 0 ? (
                      <div className="text-xs text-slate-500 italic">No telephone numbers linked.</div>
                    ) : (
                      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                        {phones.map((p: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-emerald-300">{p.normalized_number}</span>
                          <span className="text-[10px] text-slate-400">{p.carrier || "Unknown Carrier"}</span>
                        </div>
                        {p.metrics && (
                          <div className="text-[10px] text-slate-400 flex items-center gap-3">
                            <span>Calls: {p.metrics.total_calls}</span>
                            <span>Airtime: {Math.round((p.metrics.total_duration_seconds || 0) / 60)} min</span>
                          </div>
                        )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center text-slate-500 text-sm">
              Select an individual from the table to view their complete structural intelligence dossier.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
